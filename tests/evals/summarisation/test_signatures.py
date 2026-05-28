import dspy

from evals.summarisation.src.common.signatures import DialogSumSignature


def test_contract_dialog_sum_signature_extends_dspy_signature():
    """CONTRACT TEST: DialogSumSignature must be a DSPy Signature for LLM prompting."""
    assert issubclass(DialogSumSignature, dspy.Signature)


def test_contract_dialog_sum_signature_has_required_fields():
    """CONTRACT TEST: DialogSumSignature must have dialogue input and summary output fields."""
    required_input_fields = ["dialogue"]
    required_output_fields = ["summary"]

    fields = DialogSumSignature.model_fields

    for field_name in required_input_fields:
        assert field_name in fields, f"Missing required input field: {field_name}"

    for field_name in required_output_fields:
        assert field_name in fields, f"Missing required output field: {field_name}"
