import importlib
import inspect
import logging
import pkgutil
import typing

import common.templates as templates_package
from common.templates.types import Template
from common.types import TemplateMetadata

logger = logging.getLogger(__name__)


class TemplateManager:
    templates: typing.ClassVar[dict[str, type[Template]]] = {}

    @classmethod
    def register_template(cls, template: type[Template]) -> None:
        """Register a template instance in the templates module."""
        if template.name in cls.templates:
            msg = (
                f"Failed loading {template.__name__} with name: '{template.name}'. A template with the same name"
                f" ({cls.templates[template.name].__name__}) has already been registered. Please ensure template"
                f" names are unique."
            )
            raise ValueError(msg)

        cls.templates[template.name] = template

    @classmethod
    def get_template(cls, name: str) -> type[Template]:
        """Get a template instance by name."""
        try:
            return cls.templates[name]
        except KeyError as e:
            err_msg = f"Template '{name}' not found."
            raise TemplateNotFoundError(err_msg) from e

    @classmethod
    def get_template_metadata(cls) -> list[TemplateMetadata]:
        """Get a template instance by name."""
        return [
            TemplateMetadata(
                name=template.name,
                description=template.description,
                category=template.category,
                agenda_usage=template.agenda_usage,
            )
            for template in cls.templates.values()
        ]

    @classmethod
    def discover_templates(cls) -> None:
        """Discover and register all Template implementations in the templates package."""

        # Get the package path
        package_path = templates_package.__path__
        package_name = templates_package.__name__

        # Walk through all modules in the package and subpackages
        for _, modname, _ in pkgutil.walk_packages(package_path, package_name + "."):
            try:
                # Import the module
                module = importlib.import_module(modname)

                # Inspect all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a class defined in this module and has the required Template protocol attributes
                    protocol_attrs = set(typing.get_type_hints(Template).keys())
                    # `Template` and the base classes beside it are scaffolding, not templates.
                    if obj.__module__ != modname or modname == Template.__module__:
                        continue
                    missing = sorted(attr for attr in protocol_attrs if not hasattr(obj, attr))
                    if not missing:
                        try:
                            cls.register_template(obj)
                            logger.info("successfully registered template: %s", obj.name)
                        except Exception as e:  # noqa: BLE001
                            logger.warning("Warning: Could not instantiate template %s from %s: %s", name, modname, e)
                    elif len(missing) < len(protocol_attrs):
                        # Looks like a template but doesn't satisfy the protocol. Without this it would
                        # be skipped in silence and simply never appear in the product.
                        logger.warning(
                            "Warning: Not registering %s from %s: missing Template attribute(s): %s",
                            name,
                            modname,
                            ", ".join(missing),
                        )

            except Exception as e:  # noqa: BLE001
                # Log the error but continue with other modules
                logger.warning("Warning: Could not import module %s: %s", modname, e)


# Auto-discover templates when the module is initialized
TemplateManager.discover_templates()


class TemplateNotFoundError(Exception):
    """Exception raised when a template is not found."""
