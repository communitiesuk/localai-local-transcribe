resource "aws_cloudwatch_event_rule" "ecs_events" {
  name        = "${var.environment_name}-ecs-events"
  description = "Capture ECS events"

  event_pattern = jsonencode({
    source : ["aws.ecs"],
  })
}

module "ecs_events_log_group" {
  source = "../encrypted_log_group"

  log_group_name     = "${var.environment_name}-ecs-events"
  log_retention_days = 1
}

data "aws_iam_policy_document" "ecs_events_log_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream"
    ]

    resources = [
      "${module.ecs_events_log_group.log_group_arn}:*"
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
      "${module.ecs_events_log_group.log_group_arn}:*:*"
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
      values   = [aws_cloudwatch_event_rule.ecs_events.arn]
      variable = "aws:SourceArn"
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "ecs_events_log_policy" {
  policy_document = data.aws_iam_policy_document.ecs_events_log_policy_document.json
  policy_name     = "ecs-events-log-policy"
}

resource "aws_cloudwatch_event_target" "ecs_events_to_logs" {
  rule = aws_cloudwatch_event_rule.ecs_events.name
  arn  = module.ecs_events_log_group.log_group_arn
}