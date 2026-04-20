from common.templates.citations import strip_meeting_summary_tags


def test_strip_meeting_summary_tags_removes_wrapping_tags() -> None:
    raw = "<meeting_summary>\nThis is the summary.\n</meeting_summary>"
    cleaned = strip_meeting_summary_tags(raw)

    assert cleaned == "This is the summary."


def test_strip_meeting_summary_tags_leaves_text_intact() -> None:
    raw = "This is a summary without tags."
    cleaned = strip_meeting_summary_tags(raw)

    assert cleaned == raw
