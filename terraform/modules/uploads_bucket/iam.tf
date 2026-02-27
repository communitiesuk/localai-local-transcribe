data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "uploads_bucket" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetBucketLocation",
      "s3:DeleteObject"
    ]
    resources = [
      module.uploads_bucket.bucket_arn,
      "${module.uploads_bucket.bucket_arn}/*",
    ]
    principals {
      type = "Service"
      identifiers = [
        "transcribe.amazonaws.com"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        data.aws_caller_identity.current.account_id,
      ]
    }
  }
}