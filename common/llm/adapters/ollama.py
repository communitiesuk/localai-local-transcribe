import json
import logging
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from common.settings import get_settings

from .base import ModelAdapter
from .message_utils import convert_to_openai_message

settings = get_settings()
logger = logging.getLogger(__name__)


class OllamaModelAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        base_url: str,
        temperature: float = settings.LLM_TEMPERATURE,
        **kwargs: Any,
    ) -> None:
        self._model = model
        self.temperature = temperature
        self.async_client = AsyncOpenAI(
            base_url=base_url,
            api_key="ollama",
        )
        self._kwargs = kwargs

    def _generate_example_obj(self, properties: dict[str, Any]) -> dict[str, Any]:
        """Generate a dummy example object for the LLM prompt based on the JSON schema."""
        example: dict[str, Any] = {}
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            if prop_type == "string":
                example[key] = "example_string"
            elif prop_type in ("integer", "number"):
                example[key] = 0
            elif prop_type == "boolean":
                example[key] = True
            elif prop_type == "array":
                example[key] = []
            elif prop_type == "object":
                example[key] = {}
            else:
                example[key] = "..."
        return example

    async def structured_chat[T: BaseModel](self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        schema = response_format.model_json_schema()

        # Build a clearer instruction that explains what fields to include
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        field_descriptions = []
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "string")
            field_desc = field_info.get("description", "")
            required_description = "REQUIRED" if field_name in required_fields else "optional"
            field_descriptions.append(f'  - "{field_name}" ({field_type}, {required_description}): {field_desc}')

        fields_text = "\n".join(field_descriptions)

        example_obj = self._generate_example_obj(properties)
        example_json = json.dumps(example_obj, indent=2)

        json_instruction = f"""

You must respond with ONLY valid JSON. Do not include any explanatory text before or after the JSON.

Your JSON response must include these fields:
{fields_text}

Example format (replace with your actual values):
{example_json}

Remember: Respond with ONLY the JSON object containing your actual analysis, not the schema or example."""

        modified_messages = messages.copy()
        if modified_messages:
            last_msg = modified_messages[-1].copy()
            last_msg["content"] = last_msg["content"] + json_instruction
            modified_messages[-1] = last_msg

        openai_messages = [convert_to_openai_message(msg) for msg in modified_messages]

        response = await self.async_client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            response_format={"type": "json_object"},
            temperature=self.temperature,
        )

        content = response.choices[0].message.content
        if content is None:
            msg = "Received empty response from Ollama"
            raise ValueError(msg)
        try:
            json_data = json.loads(content)
            return response_format.model_validate(json_data)
        except Exception as e:
            logger.error("Ollama JSON parsing/validation failed: %s: %s", type(e).__name__, str(e))
            logger.error("Raw response was: %s", content)
            raise

    async def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            openai_messages = [convert_to_openai_message(msg) for msg in messages]

            response = await self.async_client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=0.0,
            )

            content = response.choices[0].message.content
            if content is None:
                msg = "Received empty response from Ollama"
                raise ValueError(msg)
            return content
        except Exception as e:
            logger.error("Ollama chat failed: %s: %s", type(e).__name__, str(e))
            raise
