from anthropic.types import AssistantMessageParam, MessageParam, UserMessageParam
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


def convert_to_openai_message(msg: dict[str, str]) -> ChatCompletionMessageParam:
    role = msg["role"]
    content = msg["content"]

    if role == "system":
        return ChatCompletionSystemMessageParam(role="system", content=content)
    elif role == "user":
        return ChatCompletionUserMessageParam(role="user", content=content)
    elif role == "assistant":
        return ChatCompletionAssistantMessageParam(role="assistant", content=content)
    elif role == "developer":
        return ChatCompletionDeveloperMessageParam(role="developer", content=content)
    else:
        error_msg = f"Invalid role: {role}"
        raise ValueError(error_msg)


def convert_to_anthropic_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[MessageParam]]:
    """Splits an OpenAI-style message history into Anthropic's shape.

    Anthropic's Messages API takes the system prompt as a separate top-level `system`
    argument rather than as a message with role "system", and only supports "user" and
    "assistant" roles within `messages`.
    """
    system_parts: list[str] = []
    anthropic_messages: list[MessageParam] = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            system_parts.append(content)
        elif role == "user":
            anthropic_messages.append(UserMessageParam(role="user", content=content))
        elif role == "assistant":
            anthropic_messages.append(AssistantMessageParam(role="assistant", content=content))
        else:
            error_msg = f"Invalid role: {role}"
            raise ValueError(error_msg)

    system = "\n\n".join(system_parts) if system_parts else None

    return system, anthropic_messages
