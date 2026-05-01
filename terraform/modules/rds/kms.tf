data "aws_caller_identity" "current" {}

resource "aws_kms_key" "performance_insights" {
  description         = "KMS key used for db performance insights."
  enable_key_rotation = true
}

resource "aws_kms_alias" "performance_insights" {
  name          = "alias/rds-performance-insights-${var.environment_name}"
  target_key_id = aws_kms_key.performance_insights.key_id
}

resource "aws_kms_key_policy" "performance_insights" {
  key_id = aws_kms_key.performance_insights.id
  policy = data.aws_iam_policy_document.kms_performance_insights.json
}

data "aws_iam_policy_document" "kms_performance_insights" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions = ["kms:*"]

    resources = [aws_kms_key.performance_insights.arn]
  }
}
