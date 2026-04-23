import json

import pytest

from evals.dataset_generation.counterfactual_generation.src.parser import (
    _extract_from_code_block,
    parse_llm_response,
)


def test_parse_llm_response_valid_json_list():
    response = '["First text", "Second text", "Third text"]'
    result = parse_llm_response(response)

    assert result == ["First text", "Second text", "Third text"]
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)


def test_parse_llm_response_handles_markdown_code_blocks():
    response_with_lang = """```json
["First", "Second", "Third"]
```"""
    response_no_lang = """```
["First", "Second"]
```"""
    response_with_whitespace = '  \n["Text one", "Text two"]\n  '

    assert parse_llm_response(response_with_lang) == ["First", "Second", "Third"]
    assert parse_llm_response(response_no_lang) == ["First", "Second"]
    assert parse_llm_response(response_with_whitespace) == ["Text one", "Text two"]


def test_parse_llm_response_rejects_invalid_formats():
    with pytest.raises(ValueError, match="Failed to parse LLM response as JSON"):
        parse_llm_response("This is not JSON")

    with pytest.raises(ValueError, match="Expected list of text strings"):
        parse_llm_response('{"key": "value"}')

    with pytest.raises(ValueError, match="Expected string in list"):
        parse_llm_response('["Valid string", 123, "Another string"]')


def test_parse_llm_response_empty_list():
    result = parse_llm_response("[]")
    assert result == []
    assert isinstance(result, list)


def test_extract_from_code_block_preserves_json_structure():
    response = """```json
[
  "First line",
  "Second line"
]
```"""
    result = _extract_from_code_block(response)
    parsed = json.loads(result)

    assert parsed == ["First line", "Second line"]
    assert isinstance(parsed, list)


def test_extract_from_code_block_ignores_surrounding_text():
    response = """Here is the response:
```
["Item 1", "Item 2"]
```
That's the data."""
    result = _extract_from_code_block(response)

    assert result.strip() == '["Item 1", "Item 2"]'
    assert "Here is" not in result
    assert "That's" not in result
