data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "vpc_flow_logs_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:vpc-flow-log/*"]
    }
  }
}

resource "aws_iam_role" "vpc_flow_logs" {
  name               = "vpc-flow-logs-role-${var.environment_name}"
  assume_role_policy = data.aws_iam_policy_document.vpc_flow_logs_assume_role.json
}

# As specified in the docs here: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html
# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "vpc_flow_logs" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "vpc_flow_logs" {
  name = "vpc-flow-logs-cloudwatch-policy-${var.environment_name}"
  role = aws_iam_role.vpc_flow_logs.id

  policy = data.aws_iam_policy_document.vpc_flow_logs.json
}
