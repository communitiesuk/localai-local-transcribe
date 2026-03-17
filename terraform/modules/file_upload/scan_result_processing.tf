
resource "aws_cloudwatch_event_rule" "scan_complete_event_rule" {
  name        = "process-scan-complete-event-rule-${var.environment_name}"
  description = "Rule to process GuardDuty malware scan complete events"
  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Malware Protection Object Scan Result"]
  })
}

resource "aws_cloudwatch_event_target" "process_scan_complete_event_target" {
  target_id = "process-scan-complete-event-target-${var.environment_name}"
  rule      = aws_cloudwatch_event_rule.scan_complete_event_rule.name
  arn       = var.ecs_cluster_arn
  role_arn  = aws_iam_role.event_bridge_invoke_ecs_task_role.arn
  ecs_target {
    launch_type         = "FARGATE"
    task_count          = 1
    task_definition_arn = data.aws_ecs_task_definition.webapp_task_definition.arn_without_revision

    network_configuration {
      subnets          = var.private_subnet_ids
      assign_public_ip = false
      security_groups  = var.ecs_security_group_ids
    }
    platform_version = "LATEST"
  }
  input_transformer {
    input_paths = {
      "scanResultStatus"  = "$.detail.scanResultDetails.scanResultStatus",
      "s3ObjectKey"       = "$.detail.s3ObjectDetails.objectKey",
      "s3BucketName"      = "$.detail.s3ObjectDetails.bucketName",
      "s3ObjectEtag"      = "$.detail.s3ObjectDetails.eTag",
      "s3ObjectVersionId" = "$.detail.s3ObjectDetails.versionId"
    }
    input_template = <<INPUT_TEMPLATE
{
  "containerOverrides": [
    {
      "name": "prsdb-webapp",
      "environment": [
        {
          "name": "SPRING_PROFILES_ACTIVE",
          "value": "web-server-deactivated,scan-processor"
        },
        {
          "name": "SCAN_RESULT_STATUS",
          "value": <scanResultStatus>
        },
        {
          "name": "S3_OBJECT_KEY",
          "value": <s3ObjectKey>
        },
        {
          "name": "S3_QUARANTINE_BUCKET_KEY",
          "value": <s3BucketName>
        },
        {
          "name": "S3_OBJECT_ETAG",
          "value": <s3ObjectEtag>
        },
        {
          "name": "S3_OBJECT_VERSION_ID",
          "value": <s3ObjectVersionId>
        }
      ]
    }
  ]
}
INPUT_TEMPLATE
  }
}

data "aws_ecs_task_definition" "webapp_task_definition" {
  task_definition = "prsdb-webapp-${var.environment_name}"
}

resource "aws_iam_role" "event_bridge_invoke_ecs_task_role" {
  name = "event-bridge-invoke-ecs-task-role-${var.environment_name}"

  assume_role_policy = data.aws_iam_policy_document.event_bridge_invoke_ecs_task_assume_role.json
}

data "aws_iam_policy_document" "event_bridge_invoke_ecs_task_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy_attachment" "event_bridge_invoke_ecs_task_policy_attachment" {
  role       = aws_iam_role.event_bridge_invoke_ecs_task_role.name
  policy_arn = aws_iam_policy.event_bridge_invoke_ecs_task_custom_policy.arn
}

resource "aws_iam_policy" "event_bridge_invoke_ecs_task_custom_policy" {
  name = "event-bridge-invoke-ecs-task-custom-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = [
          data.aws_ecs_task_definition.webapp_task_definition.arn_without_revision,
          "${data.aws_ecs_task_definition.webapp_task_definition.arn_without_revision}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          data.aws_ecs_task_definition.webapp_task_definition.execution_role_arn,
          data.aws_ecs_task_definition.webapp_task_definition.task_role_arn,
        ]
      }
    ]
  })
}