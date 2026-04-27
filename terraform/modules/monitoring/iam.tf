data "aws_iam_policy_document" "cloudtrail_cloudwatch_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "cloudtrail_cloudwatch_role" {
  name               = "cloudtrail-cloudwatch-role-${var.environment_name}"
  assume_role_policy = data.aws_iam_policy_document.cloudtrail_cloudwatch_assume_role.json
}

# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "cloudtrail_cloudwatch_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]

    resources = [
      "${module.cloudtrail_cloudwatch_group.log_group_arn}:*:*"
    ]
  }
}

resource "aws_iam_policy" "cloudtrail_cloudwatch_policy" {
  name   = "cloudtrail-cloudwatch-policy-${var.environment_name}"
  policy = data.aws_iam_policy_document.cloudtrail_cloudwatch_policy_document.json
}

resource "aws_iam_role_policy_attachment" "cloudtrail_cloudwatch_policy_attachment" {
  role       = aws_iam_role.cloudtrail_cloudwatch_role.name
  policy_arn = aws_iam_policy.cloudtrail_cloudwatch_policy.arn
}

resource "aws_sns_topic_policy" "cloudwatch_to_alarm_sns" {
  arn    = aws_sns_topic.alarm_sns_topic.arn
  policy = data.aws_iam_policy_document.cloudwatch_to_sns_policy_document.json
}

data "aws_iam_policy_document" "cloudwatch_to_sns_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]
    resources = [
      aws_sns_topic.alarm_sns_topic.arn
    ]
    principals {
      type = "Service"
      identifiers = [
        "cloudwatch.amazonaws.com"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}
