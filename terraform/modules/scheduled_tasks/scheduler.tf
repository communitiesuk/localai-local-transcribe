resource "aws_cloudwatch_event_rule" "scheduled_tasks" {
  for_each = local.tasks

  name                = "${var.environment_name}-${each.key}-scheduled-task"
  description         = "Trigger ${each.key} scheduled task in ${var.environment_name}"
  schedule_expression = each.value.schedule_expression
  state               = "ENABLED"
}

resource "aws_scheduler_schedule_group" "scheduled_tasks" {
  name = "${var.environment_name}-scheduled-tasks-group"
}

resource "aws_scheduler_schedule" "scheduled_tasks" {
  for_each   = local.tasks
  name       = "${var.environment_name}-${each.key}-scheduled-task"
  group_name = aws_scheduler_schedule_group.scheduled_tasks.name

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = each.value.schedule_expression

  target {
    arn      = aws_ecs_cluster.scheduled_tasks.arn
    role_arn = aws_iam_role.scheduled_tasks.arn

    ecs_parameters {
      task_definition_arn = each.value.task_family_arn
      launch_type         = "FARGATE"
      platform_version    = "LATEST"
      task_count          = 1

      network_configuration {
        subnets          = var.private_subnet_ids
        security_groups  = var.security_group_ids
        assign_public_ip = false
      }
    }

    input = jsonencode({
      "containerOverrides" : [
        {
          "name" : "prsdb-${each.key}-scheduled-task",
          "environment" : [
            {
              "name" : "SPRING_PROFILES_ACTIVE",
              "value" : "web-server-deactivated,scheduled-task,${each.key}-scheduled-task"
            }
          ]
        }
      ]
    })

    retry_policy {
      # ToDo PRSD-1607: Consider sensible max retry attempts and cooldown period
      maximum_retry_attempts = 0
    }

    dead_letter_config {
      arn = aws_sqs_queue.scheduled_tasks_dead_letter_queue.arn
    }
  }

}

resource "aws_cloudwatch_event_target" "scheduled_tasks" {
  for_each = local.tasks

  rule      = aws_cloudwatch_event_rule.scheduled_tasks[each.key].name
  target_id = "${var.environment_name}-${each.key}-task"
  arn       = aws_ecs_cluster.scheduled_tasks.arn
  role_arn  = aws_iam_role.scheduled_tasks.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = each.value.task_family_arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      subnets          = var.private_subnet_ids
      security_groups  = var.security_group_ids
      assign_public_ip = false
    }
  }
}

