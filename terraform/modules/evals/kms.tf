data "aws_caller_identity" "current" {}

# One customer-managed key that encrypts all four evals data buckets (quarantine, assets,
# outputs and results). The access log bucket beside each data bucket cannot use it, because
# S3 cannot write access logs into a bucket that uses a customer-managed key.
resource "aws_kms_key" "evals" {
  enable_key_rotation = true
  description         = "local-transcribe-evals-${var.environment_name}"
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
  # No other principal is named here. Access for the malware scan, the task and people is
  # added by the tickets that introduce them.
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = [aws_kms_key.evals.arn]
  }
}
