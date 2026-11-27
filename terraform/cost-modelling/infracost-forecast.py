import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory

COST_MODELLING = Path(__file__).resolve().parent
TERRAFORM = COST_MODELLING.parent
MONTHLY_HOURS = Decimal(730)
REGIONAL_NAT = "module.networking.aws_nat_gateway.regional_nat_gateway"
FARGATE_COMPONENTS = {"Per vCPU per hour": "vcpu", "Per GB per hour": "memory_gb"}
SCALABLE_COMPONENTS = {
    "aws_vpc_endpoint": "Endpoint (Interface)",
    "aws_lb": "Application load balancer",
    "aws_kms_key": "Customer master key",
}
CAPACITY = {
    "workers": ("ecs", "worker_task_desired_count", r"[0-9]+"),
    "frontend": ("ecs", "frontend_task_desired_count", r"[0-9]+"),
    "backend": ("ecs", "backend_task_desired_count", r"[0-9]+"),
}
DB_CLASS = r'"db\.[a-z0-9]+\.[a-z0-9]+"'


def block_setting(source, header, argument, pattern):
    blocks = list(re.finditer(rf"^{re.escape(header)} \{{\n(.*?)^\}}[ \t]*$", source, re.MULTILINE | re.DOTALL))
    if len(blocks) != 1:
        msg = f"Expected exactly one {header} block in production/main.tf"
        raise ValueError(msg)
    block = blocks[0]
    assignments = list(re.finditer(rf"^[ \t]+{argument}[ \t]*=[ \t]*(.*)$", block[1], re.MULTILINE))
    if len(assignments) != 1 or not re.fullmatch(pattern, assignments[0][1].rstrip()):
        msg = f"Unexpected {argument} assignment in {header} in production/main.tf"
        raise ValueError(msg)
    setting = assignments[0]
    start = block.start(1) + setting.start(1)
    value = setting[1].rstrip()
    return value, start, start + len(value)


def module_setting(source, module, argument, literal):
    value, start, end = block_setting(source, f'module "{module}"', argument, literal)
    return json.loads(value), start, end


def capacity_options(source, config):
    for dimension, (module, argument, literal) in CAPACITY.items():
        baseline, start, end = module_setting(source, module, argument, literal)
        options = config[dimension]
        if (
            not isinstance(options, list)
            or not options
            or any(not re.fullmatch(literal, json.dumps(option)) for option in options)
        ):
            msg = f"Invalid capacity options for {dimension}"
            raise ValueError(msg)
        for option in dict.fromkeys(options):
            if option != baseline:
                yield f"{dimension}={option}", source[:start] + json.dumps(option) + source[end:]
    yield from database_options(source, config)


def database_options(source, config):
    baseline_class, _, _ = module_setting(source, "database", "instance_class", DB_CLASS)
    _, az_start, az_end = block_setting(source, 'module "database"', "multi_az", r"local\.multi_az")
    baseline_az, _, _ = block_setting(source, "locals", "multi_az", r"true|false")
    classes = config["database"]
    modes = config.get("database_multi_az", [json.loads(baseline_az)])
    if (
        not isinstance(classes, list)
        or not classes
        or any(not re.fullmatch(DB_CLASS, json.dumps(item)) for item in classes)
    ):
        msg = "Invalid database instance classes"
        raise ValueError(msg)
    if not isinstance(modes, list) or not modes or any(type(mode) is not bool for mode in modes):
        msg = "database_multi_az must be a non-empty list of booleans"
        raise ValueError(msg)
    for instance_class in dict.fromkeys(classes):
        for multi_az in dict.fromkeys(modes):
            az_literal = json.dumps(multi_az)
            if (instance_class, az_literal) == (baseline_class, baseline_az):
                continue
            changed = source
            if az_literal != baseline_az:
                changed = changed[:az_start] + az_literal + changed[az_end:]
            if instance_class != baseline_class:
                _, start, end = module_setting(changed, "database", "instance_class", DB_CLASS)
                changed = changed[:start] + json.dumps(instance_class) + changed[end:]
            mode = "multi-az" if multi_az else "single-az"
            yield f"database={instance_class}/{mode}", changed


def nonnegative(value):
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        msg = f"Expected a non-negative number, got {value!r}"
        raise ValueError(msg)
    return number


def regional_nat_hourly_adjustment(report, source):
    az_count, _, _ = module_setting(source, "networking", "number_of_availability_zones", r"[1-9][0-9]*")
    expected_hours = MONTHLY_HOURS * az_count
    components = [
        component
        for project in report["projects"]
        for resource in project["resources"]
        if resource["name"] == REGIONAL_NAT
        for component in resource["cost_components"]
        if component["unit"] == "hours"
    ]
    if not components:
        msg = f"No hourly cost component found for {REGIONAL_NAT}"
        raise ValueError(msg)
    billed_hours = sum(nonnegative(component["quantity"]) for component in components)
    if billed_hours == expected_hours:
        return Decimal(0)
    if len(components) != 1 or billed_hours != MONTHLY_HOURS:
        msg = f"Unexpected regional NAT hours: {billed_hours}; expected {expected_hours}"
        raise ValueError(msg)
    rate = nonnegative(components[0]["price"])
    return (expected_hours - billed_hours) * rate


def fargate_architectures(source):
    architectures = {}
    for service in ("frontend", "backend", "worker"):
        blocks = re.findall(
            rf'^resource "aws_ecs_task_definition" "{service}" \{{\n(.*?)^\}}', source, re.MULTILINE | re.DOTALL
        )
        architecture = (
            re.findall(r'^\s*cpu_architecture\s*=\s*"(ARM64|X86_64)"\s*$', blocks[0], re.MULTILINE)
            if len(blocks) == 1
            else []
        )
        if len(architecture) != 1:
            msg = f"Expected an explicit Fargate architecture for {service}"
            raise ValueError(msg)
        architectures[f"module.ecs.aws_ecs_service.{service}"] = architecture[0]
    return architectures


def fargate_adjustment(components, architecture, rates):
    adjustment = Decimal(0)
    for name, meter in FARGATE_COMPONENTS.items():
        matches = [component for component in components if component["name"] == name]
        if len(matches) != 1:
            msg = f"Expected one Fargate component named {name!r}"
            raise ValueError(msg)
        component = matches[0]
        prices = {arch: MONTHLY_HOURS * nonnegative(rate[meter]) for arch, rate in rates.items()}
        reported_price = nonnegative(component["price"])
        quantity = nonnegative(component["quantity"])
        if reported_price not in prices.values() or reported_price * quantity != nonnegative(
            component["total_monthly_cost"]
        ):
            msg = f"Unexpected Infracost Fargate rate or quantity for {name}: {component}"
            raise ValueError(msg)
        adjustment += (prices[architecture] - reported_price) * quantity
    return adjustment


def forecast_prices(report, source, architectures, rates, scale_factor):
    nat_adjustment = regional_nat_hourly_adjustment(report, source)
    list_price = nonnegative(report["summary"]["total_monthly_cost"]) + nat_adjustment
    scalable_cost = nat_adjustment
    services = set()
    for project in report["projects"]:
        for resource in project["resources"]:
            resource_type = resource["type"]
            name = resource["name"]
            components = resource.get("cost_components") or []
            if name in architectures and resource_type == "aws_ecs_service":
                services.add(name)
                architecture = architectures[name]
                adjustment = fargate_adjustment(components, architecture, rates)
                list_price += adjustment
                if architecture == "ARM64":
                    scalable_cost += adjustment + sum(
                        nonnegative(component["total_monthly_cost"])
                        for component in components
                        if component["name"] in FARGATE_COMPONENTS
                    )
            for component in components:
                cost = nonnegative(component.get("total_monthly_cost") or 0)
                if resource_type == "aws_shield_subscription":
                    list_price -= cost
                elif (
                    component["name"] == SCALABLE_COMPONENTS.get(resource_type)
                    or (name == REGIONAL_NAT and component["unit"] == "hours")
                    or (resource_type == "aws_db_instance" and component["name"].startswith("Database instance ("))
                ):
                    scalable_cost += cost
    if services != architectures.keys():
        msg = f"Missing Fargate services in scan: {sorted(architectures.keys() - services)}"
        raise ValueError(msg)
    return list_price, list_price - scalable_cost * (1 - scale_factor)


def scan(label, source, usage_file, architectures, rates, scale_factor):
    executable = shutil.which("infracost")
    if executable is None:
        msg = "Infracost CLI not found on PATH"
        raise FileNotFoundError(msg)
    sys.stderr.write(f"Scanning {label}...\n")
    sys.stderr.flush()
    with TemporaryDirectory(prefix="infracost-production-") as temporary:
        staging = Path(temporary)
        for directory in ("production", "modules"):
            shutil.copytree(
                TERRAFORM / directory,
                staging / directory,
                ignore=shutil.ignore_patterns(".terraform", "*.tfstate*", "*.tfvars*"),
            )
        (staging / "production/main.tf").write_text(source, encoding="utf-8")
        shutil.copyfile(COST_MODELLING / "infracost-scan.yml", staging / "infracost.yml")
        shutil.copyfile(usage_file, staging / "infracost-usage.yml")
        result = subprocess.run(  # noqa: S603
            [str(Path(executable).resolve()), "scan", ".", "--json", "--currency", "USD"],
            cwd=staging,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
            timeout=180,
        )
        try:
            report = json.loads(result.stdout, parse_float=Decimal)
            if report["currency"] != "USD" or [project["path"] for project in report["projects"]] != ["production"]:
                msg = "Expected USD costs for the production project only"
                raise ValueError(msg)
            return forecast_prices(report, source, architectures, rates, scale_factor)
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            msg = f"Unexpected Infracost JSON for {label}: {error}"
            raise ValueError(msg) from error


def forecast(config_path, csv_path=None, scale_factor=None):
    config = json.loads(config_path.read_text(encoding="utf-8"), parse_float=Decimal)
    source = (TERRAFORM / "production/main.tf").read_text(encoding="utf-8")
    architectures = fargate_architectures((TERRAFORM / "modules/ecs/task_definition.tf").read_text(encoding="utf-8"))
    rates = config["fargate_hourly_usd"]
    show_scaled = scale_factor is not None
    if scale_factor is None:
        scale_factor = Decimal(1)
    elif not scale_factor.is_finite() or not 0 <= scale_factor <= 1:
        msg = "rate scale factor must be between 0 and 1"
        raise ValueError(msg)
    idle = config_path.parent / config["idle_usage_file"]
    alternatives = [(label, changed, idle) for label, changed in capacity_options(source, config)]
    for name, usage in config["usage"].items():
        alternatives.append((f"usage={name}", source, config_path.parent / usage["file"]))
    for usage_path in {idle, *(option[2] for option in alternatives)}:
        if not usage_path.is_file():
            msg = f"Usage file not found: {usage_path}"
            raise ValueError(msg)

    baseline_list, baseline_scaled = scan("baseline", source, idle, architectures, rates, scale_factor)
    rows = [("baseline", baseline_list, baseline_scaled)]
    for label, terraform, usage_file in alternatives:
        rows.append((label, *scan(label, terraform, usage_file, architectures, rates, scale_factor)))

    headers = ("Option", "List total", "List delta")
    if show_scaled:
        headers += ("Scaled total", "Scaled delta")
    matrix = []
    for label, list_price, scaled_price in rows:
        amounts = (list_price, list_price - baseline_list)
        if show_scaled:
            amounts += (scaled_price, scaled_price - baseline_scaled)
        matrix.append((label, *amounts))
    if csv_path is not None:
        with csv_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows((label, *(format(value, ".2f") for value in amounts)) for label, *amounts in matrix)

    label_width = max(len(label) for label, *_ in matrix)
    sys.stdout.write("Monthly costs (USD, pre-tax, excluding Shield):\n\n")
    header_line = " ".join((f"{headers[0]:<{label_width}}", *(f"{header:>12}" for header in headers[1:])))
    sys.stdout.write(f"{header_line}\n")
    for label, *amounts in matrix:
        formats = (">12,.2f", ">+12,.2f") * (len(amounts) // 2)
        cells = (format(value, spec) for value, spec in zip(amounts, formats, strict=True))
        row_line = " ".join((f"{label:<{label_width}}", *cells))
        sys.stdout.write(f"{row_line}\n")


def main():
    parser = argparse.ArgumentParser(description="Forecast independent production AWS cost options")
    parser.add_argument("--config", type=Path, default=COST_MODELLING / "infracost-forecast.json")
    parser.add_argument("--csv", type=Path, metavar="PATH", help="Also write the pre-tax forecast matrix to a CSV file")
    parser.add_argument(
        "--rate-scale-factor",
        type=Decimal,
        metavar="FACTOR",
        help="Show scaled totals using this fraction of list price for eligible charges (0 to 1)",
    )
    args = parser.parse_args()
    try:
        forecast(args.config.resolve(), csv_path=args.csv, scale_factor=args.rate_scale_factor)
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation, subprocess.SubprocessError) as error:
        parser.exit(1, f"Forecast failed: {error}\n")


if __name__ == "__main__":
    main()
