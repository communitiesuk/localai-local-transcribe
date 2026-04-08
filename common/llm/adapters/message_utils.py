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
