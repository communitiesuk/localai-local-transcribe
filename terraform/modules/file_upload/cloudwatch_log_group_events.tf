module "virus_scan_retention_log_group" {
  source = "../../modules/encrypted_log_group"

  log_group_name     = "virus-scan-result-log-group-${var.environment_name}"
  log_retention_days = 14
}

data "aws_iam_policy_document" "virus_scan_retention_log_policy" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream"
    ]

    resources = [
      "${module.virus_scan_retention_log_group.log_group_arn}:*"
    ]

    principals {
      type = "Service"
      identifiers = [
        "events.amazonaws.com",
        "delivery.logs.amazonaws.com"
      ]
    }
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:PutLogEvents"
    ]

    resources = [
      "${module.virus_scan_retention_log_group.log_group_arn}:*:*"
    ]

    principals {
      type = "Service"
      identifiers = [
        "events.amazonaws.com",
        "delivery.logs.amazonaws.com"
      ]
    }

    condition {
      test     = "ArnEquals"
      values   = [aws_cloudwatch_event_rule.scan_complete_event_rule.arn]
      variable = "aws:SourceArn"
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "virus_scan_retention" {
  policy_document = data.aws_iam_policy_document.virus_scan_retention_log_policy.json
  policy_name     = "guardduty-log-publishing-policy"
}


resource "aws_cloudwatch_event_target" "example" {
  rule = aws_cloudwatch_event_rule.scan_complete_event_rule.name
  arn  = module.virus_scan_retention_log_group.log_group_arn
}