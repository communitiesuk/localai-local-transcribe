data "aws_caller_identity" "current" {}

# One customer-managed key that encrypts all four evals data buckets (quarantine, assets,
# outputs and results). The access log bucket beside each data bucket cannot use it, because
# S3 cannot write access logs into a bucket that uses a customer-managed key.
resource "aws_kms_key" "evals" {
  enable_key_rotation = true
  # AWS otherwise rotates yearly. 180 days matches the app config key and the Wiz check.
  rotation_period_in_days = 180
  description             = "local-transcribe-evals-${var.environment_name}"

  # If this key were destroyed, the four evals data buckets could no longer be read. A plan that
  # would delete or replace the key fails instead, so removal has to be a deliberate edit.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "evals" {
  name          = "alias/evals-${var.environment_name}"
  target_key_id = aws_kms_key.evals.key_id
}

resource "aws_kms_key_policy" "evals" {
  key_id = aws_kms_key.evals.key_id
  policy = data.aws_iam_policy_document.evals_kms.json
}

data "aws_iam_policy_document" "evals_kms" {
  # Gives the account root full control of the key. This is what lets IAM policies grant
  # other roles access to the key later: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam
  # No other principal is named here. The quarantine scan role and the promotion Lambda
  # are granted use of the key by their own IAM policies. Access for the task and for
  # people is added by the tickets that introduce them.
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = [aws_kms_key.evals.arn]
  }
}
