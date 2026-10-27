import pytest

from common.llm.adapters.message_utils import convert_to_anthropic_messages


def test_system_message_is_split_out():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
    ]

    system, anthropic_messages = convert_to_anthropic_messages(messages)

    assert system == "You are a helpful assistant."
    assert anthropic_messages == [{"role": "user", "content": "Hello"}]


def test_no_system_message_returns_none_system():
    messages = [{"role": "user", "content": "Hello"}]

    system, anthropic_messages = convert_to_anthropic_messages(messages)

    assert system is None
    assert anthropic_messages == [{"role": "user", "content": "Hello"}]


def test_user_and_assistant_messages_are_preserved_in_order():
    messages = [
        {"role": "user", "content": "Hi, my name is John."},
        {"role": "assistant", "content": "Hello John!"},
        {"role": "user", "content": "What's my name?"},
    ]

    system, anthropic_messages = convert_to_anthropic_messages(messages)

    assert system is None
    assert anthropic_messages == [
        {"role": "user", "content": "Hi, my name is John."},
        {"role": "assistant", "content": "Hello John!"},
        {"role": "user", "content": "What's my name?"},
    ]


def test_multiple_system_messages_are_joined():
    messages = [
        {"role": "system", "content": "First system instruction."},
        {"role": "system", "content": "Second system instruction."},
        {"role": "user", "content": "Hello"},
    ]

    system, anthropic_messages = convert_to_anthropic_messages(messages)

    assert system == "First system instruction.\n\nSecond system instruction."
    assert anthropic_messages == [{"role": "user", "content": "Hello"}]


def test_unsupported_role_raises_value_error():
    messages = [{"role": "developer", "content": "Some instructions"}]

    with pytest.raises(ValueError, match="Invalid role"):
        convert_to_anthropic_messages(messages)
