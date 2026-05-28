from __future__ import annotations

import dspy


class DialogSumSignature(dspy.Signature):
    """DialogSum-style conversational summarization.

    Dataset fields (knkarthick/dialogsum):
    - dialogue: text of dialogue
    - summary: human written summary of the dialogue
    """

    dialogue: str = dspy.InputField(desc="Text of dialogue.")
    summary: str = dspy.OutputField(desc="Human written summary of the dialogue.")
