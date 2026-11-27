import argparse
import json
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

import yaml

COST_MODELLING = Path(__file__).resolve().parent
NAT = "module.networking.aws_nat_gateway.regional_nat_gateway"


def number(value):
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        msg = f"Expected a non-negative number, got {value!r}"
        raise ValueError(msg)
    return result


def decimal_values(value):
    if isinstance(value, dict):
        return {key: decimal_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decimal_values(item) for item in value]
    return number(value) if type(value) in (int, float) else value


def yaml_values(value):
    if isinstance(value, dict):
        return {key: yaml_values(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def request_count(value):
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def bucket_usage(storage, writes, reads=0):
    return {
        "standard": {
            "storage_gb": storage,
            "monthly_tier_1_requests": request_count(writes),
            "monthly_tier_2_requests": request_count(Decimal(reads)),
        }
    }


def resource_usage(workload, assumptions):
    meetings = number(workload["monthly_active_users"]) * number(workload["meetings_per_active_user"])
    minutes = number(workload["mean_audio_minutes"])
    transcriptions = meetings * number(workload["transcriptions_per_meeting"])
    summaries = meetings * number(workload["summaries_per_meeting"])
    source_gb = assumptions["source_mb_per_90_minutes"] * minutes / 90000
    mp3_gb = assumptions["converted_audio_kbps"] * minutes * 60 / 8000000
    audio_uploads = mp3_gb * transcriptions
    outbound = max(0, audio_uploads + assumptions["background_egress_gb"] - assumptions["free_egress_gb"])
    usage = {
        "module.monitoring.aws_cloudtrail.main": {
            "monthly_additional_management_events": assumptions["additional_management_events"],
        }
    }
    if outbound:
        usage["aws_data_transfer.internet_egress"] = {"region": "eu-west-2", "monthly_outbound_internet_gb": outbound}
    if not meetings:
        usage[NAT] = {"monthly_data_processed_gb": assumptions["background_nat_gb"]}
        return usage

    requests = request_count(
        meetings * assumptions["https_requests_per_meeting"]
        + transcriptions * assumptions["status_requests_per_transcription"]
    )
    viewer_gb = meetings * assumptions["viewer_gb_per_meeting"]
    usage.update(
        {
            "module.frontdoor.aws_cloudfront_distribution.main": {
                "monthly_data_transfer_to_internet_gb": {"europe": viewer_gb},
                "monthly_data_transfer_to_origin_gb": {"europe": meetings * assumptions["origin_gb_per_meeting"]},
                "monthly_https_requests": {"europe": requests},
            },
            "module.frontdoor.aws_lb.main": {
                "new_connections": meetings * assumptions["alb_new_connections_per_meeting"],
                "active_connections": number(
                    workload.get("alb_active_connections", assumptions["alb_active_connections"])
                ),
                "processed_bytes_gb": viewer_gb,
                "rule_evaluations": 0,
            },
            "module.frontdoor.aws_wafv2_web_acl.main": {"monthly_requests": requests},
            "module.frontdoor.aws_wafv2_web_acl.load_balancer": {"monthly_requests": requests},
            "module.uploads_bucket.module.uploads_bucket.aws_s3_bucket.main": bucket_usage(
                (
                    (source_gb * meetings + mp3_gb * min(meetings, transcriptions))
                    * assumptions["audio_retention_days"]
                    / 30
                ).quantize(Decimal("0.1")),
                meetings * assumptions["s3_writes_per_meeting"],
                meetings * assumptions["s3_reads_per_meeting"],
            ),
        }
    )
    for address, (storage, fixed_writes, writes) in assumptions["s3_logs"].items():
        usage[address] = bucket_usage(storage * meetings, fixed_writes + writes * meetings)
    drivers = {"meetings": meetings, "jobs": transcriptions + summaries}
    for address, (driver, storage, ingested, scanned) in assumptions["cloudwatch_logs"].items():
        count = drivers[driver]
        usage[address] = {
            "storage_gb": storage * count,
            "monthly_data_ingested_gb": ingested * count,
            "monthly_data_scanned_gb": scanned * count,
        }
    other_nat = max(assumptions["background_nat_gb"], meetings * assumptions["other_nat_gb_per_meeting"])
    usage[NAT] = {"monthly_data_processed_gb": audio_uploads + other_nat}
    usage["module.networking.aws_vpc_endpoint.vpc_endpoints[12]"] = {
        "monthly_data_processed_gb": meetings * assumptions["logs_endpoint_gb_per_meeting"]
    }
    usage["module.networking.aws_vpc_endpoint.vpc_endpoints[5]"] = {
        "monthly_data_processed_gb": assumptions["ecr_endpoint_gb"]
    }
    for queue, jobs, rate in (
        ("transcription_queue", transcriptions, assumptions["sqs_requests_per_transcription"]),
        ("llm_queue", summaries, assumptions["sqs_requests_per_summary"]),
    ):
        usage[f"module.sqs.aws_sqs_queue.{queue}"] = {
            "monthly_requests": request_count(jobs * rate),
            "request_size_kb": assumptions["queue_request_size_kb"],
        }
    for service, storage in assumptions["ecr_storage_gb"].items():
        usage[f"module.ecr.aws_ecr_repository.{service}"] = {"storage_gb": storage}
    return usage


def generate(config, forecast):
    filenames = {
        "idle": forecast["idle_usage_file"],
        **{name: option["file"] for name, option in forecast["usage"].items()},
    }
    if filenames.keys() != config["scenarios"].keys() or len(set(filenames.values())) != len(filenames):
        msg = "Workload and forecast scenarios must match and use distinct output paths"
        raise ValueError(msg)
    assumptions = config["assumptions"]
    defaults = config["resource_type_default_usage"]
    defaults["aws_sqs_queue"]["request_size_kb"] = assumptions["queue_request_size_kb"]
    for name, file in filenames.items():
        workload = {**config["defaults"], **config["scenarios"][name]}
        content = {
            "version": 0.1,
            "resource_type_default_usage": defaults,
            "resource_usage": resource_usage(workload, assumptions),
        }
        header = "# Generated by generate-infracost-usage.py from infracost-workload.yml. Do not edit.\n"
        yield file, header + yaml.safe_dump(yaml_values(content), sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description="Generate the production Infracost usage files")
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ; do not write")
    args = parser.parse_args()
    config = decimal_values(yaml.safe_load((COST_MODELLING / "infracost-workload.yml").read_text(encoding="utf-8")))
    forecast = json.loads((COST_MODELLING / "infracost-forecast.json").read_text(encoding="utf-8"))
    stale = []
    for file, text in generate(config, forecast):
        path = COST_MODELLING / file
        if args.check:
            if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
                stale.append(file)
        else:
            path.write_bytes(text.encode("utf-8"))
    if stale:
        parser.exit(1, "Regenerate usage files: " + ", ".join(stale) + "\n")


if __name__ == "__main__":
    main()
