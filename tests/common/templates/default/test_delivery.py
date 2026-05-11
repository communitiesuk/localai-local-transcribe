import pytest
from common.templates.default.delivery import Delivery
from common.templates.utils.template_renderer import render_template


def test_get_messages_for_sections():
    result = Delivery.get_messages_for_sections()

    assert result["role"] == "user"
    assert "Generate a list of sections" in result["content"]
    assert "The sections should be in the order they appear in the transcript" in result["content"]
    assert "introduction and a conclusion" in result["content"]
    assert "style guide" in result["content"]


def test_get_messages_for_sections_style_guide():
    template = render_template("delivery_style_guide.j2")
    style_guide = template.render()

    result = Delivery.get_messages_for_sections()

    assert style_guide in result["content"]
    assert "The minute is written in past reported speech." in style_guide
    assert "The output should be in plain text format." in style_guide