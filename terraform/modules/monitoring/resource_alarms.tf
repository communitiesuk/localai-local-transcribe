resource "aws_cloudwatch_metric_alarm" "ecs_cpu_usage" {
  for_each = toset(var.ecs_service_names)

  alarm_name          = "${each.value}-cpu-usage"
  alarm_description   = "ECS CPU utilization has been >90% for over a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  evaluation_periods  = 1
  period              = 60
  threshold           = 90
  statistic           = "Average"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = each.value
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_usage" {
  for_each = toset(var.ecs_service_names)

  alarm_name          = "${each.value}-memory-usage"
  alarm_description   = "ECS memory usage has been >90% for over a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  evaluation_periods  = 1
  period              = 60
  threshold           = 90
  statistic           = "Average"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = each.value
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_start_failure" {
  for_each = aws_cloudwatch_log_metric_filter.ecs_task_start_failure

  alarm_name          = "${each.key}-task-start-failure"
  alarm_description   = "An ECS task has failed to start and reach a healthy state"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  metric_name         = each.value.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_usage" {
  alarm_name          = "${var.database_identifier}-cpu-usage"
  alarm_description   = "RDS Database CPU utilization has been >90% for over a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  evaluation_periods  = 1
  period              = 60
  threshold           = 90
  statistic           = "Average"

  dimensions = {
    DBInstanceIdentifier = var.database_identifier
  }


  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.database_identifier}-storage"
  alarm_description   = "RDS Database storage space has been >90% full for over a minute"
  comparison_operator = "LessThanThreshold"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  evaluation_periods  = 1
  period              = 60
  threshold           = var.database_allocated_storage * 0.1
  statistic           = "Minimum"

  dimensions = {
    DBInstanceIdentifier = var.database_identifier
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.alb_name}-5xx-errors"
  alarm_description   = "There have been >100 5xx responses at the ALB in a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  evaluation_periods  = 1
  period              = 60
  threshold           = 100
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "alb_4xx_errors" {
  alarm_name          = "${var.alb_name}-4xx-errors"
  alarm_description   = "There have been >100 4xx responses at the ALB in a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "HTTPCode_Target_4XX_Count"
  namespace           = "AWS/ApplicationELB"
  evaluation_periods  = 1
  period              = 60
  threshold           = 100
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "alb_no_healthy_hosts" {
  alarm_name          = "${var.alb_name}-no-healthy-hosts"
  alarm_description   = "There have been no healthy ALB hosts for over a minute"
  comparison_operator = "LessThanThreshold"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Minimum"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.alb_target_group_arn_suffix
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "${var.waf_acl_name}-blocked-requests"
  alarm_description   = "There have been >100 blocked WAF requests in a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  evaluation_periods  = 1
  period              = 60
  threshold           = 100
  statistic           = "Sum"
  treat_missing_data  = "notBreaching"
  provider            = aws.us-east-1

  dimensions = {
    Rule   = "ALL"
    WebACL = var.waf_acl_name
  }

  alarm_actions = [
    aws_sns_topic.us_alarm_sns_topic.arn,
  ]
}


resource "aws_cloudwatch_metric_alarm" "apim_failure_rate" {
  alarm_name          = "${var.environment_name}-apim-failure-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  threshold           = 10
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  metric_query {
    id = "backend_requests"
    metric {
      namespace   = "LogMetrics"
      metric_name = "apim-requests-${var.environment_name}-backend"
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id = "backend_failures"
    metric {
      namespace   = "LogMetrics"
      metric_name = "apim-failures-${var.environment_name}-backend"
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id = "worker_requests"
    metric {
      namespace   = "LogMetrics"
      metric_name = "apim-requests-${var.environment_name}-worker"
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id = "worker_failures"
    metric {
      namespace   = "LogMetrics"
      metric_name = "apim-failures-${var.environment_name}-worker"
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "rate"
    expression  = "IF((backend_requests + worker_requests) > 0, ((backend_failures + worker_failures) / (backend_requests + worker_requests)) * 100, 0)"
    label       = "APIM Failure Rate"
    return_data = true
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn
  ]
}

resource "aws_cloudwatch_metric_alarm" "credential_renewal_failed" {
  alarm_name          = "credential-renewal-failed-${var.environment_name}"
  alarm_description   = "The database credential renewal process has failed in the backend or worker"
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  treat_missing_data  = "notBreaching"

  metric_query {
    id = "backend_failures"
    metric {
      namespace   = aws_cloudwatch_log_metric_filter.credential_renewal_failed_backend.metric_transformation[0].namespace
      metric_name = aws_cloudwatch_log_metric_filter.credential_renewal_failed_backend.metric_transformation[0].name
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id = "worker_failures"
    metric {
      namespace   = aws_cloudwatch_log_metric_filter.credential_renewal_failed_worker.metric_transformation[0].namespace
      metric_name = aws_cloudwatch_log_metric_filter.credential_renewal_failed_worker.metric_transformation[0].name
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "total_failures"
    expression  = "FILL(backend_failures, 0) + FILL(worker_failures, 0)"
    label       = "Credential renewal failures (backend + worker)"
    return_data = true
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "database_connection_failed" {
  alarm_name          = "database-connection-failed-${var.environment_name}"
  alarm_description   = "The database connection process has failed in the backend or worker"
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  treat_missing_data  = "notBreaching"

  metric_query {
    id = "backend_failures"
    metric {
      namespace   = aws_cloudwatch_log_metric_filter.database_connection_failed_backend.metric_transformation[0].namespace
      metric_name = aws_cloudwatch_log_metric_filter.database_connection_failed_backend.metric_transformation[0].name
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id = "worker_failures"
    metric {
      namespace   = aws_cloudwatch_log_metric_filter.database_connection_failed_worker.metric_transformation[0].namespace
      metric_name = aws_cloudwatch_log_metric_filter.database_connection_failed_worker.metric_transformation[0].name
      period      = 60
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "total_failures"
    expression  = "FILL(backend_failures, 0) + FILL(worker_failures, 0)"
    label       = "Database connection failures (backend + worker)"
    return_data = true
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "worker_job_failure_rate" {
  alarm_name          = "${var.environment_name}-worker-job-failure-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 4
  datapoints_to_alarm = 3
  threshold           = var.worker_job_failure_rate_threshold
  treat_missing_data  = "notBreaching"

  metric_query {
    id = "started"
    metric {
      namespace   = "LogMetrics"
      metric_name = "worker-job-started-${var.environment_name}"
      period      = 900
      stat        = "Sum"
    }
  }

  metric_query {
    id = "requeued"
    metric {
      namespace   = "LogMetrics"
      metric_name = "worker-job-requeued-${var.environment_name}"
      period      = 900
      stat        = "Sum"
    }
  }

  metric_query {
    id = "failed"
    metric {
      namespace   = "LogMetrics"
      metric_name = "worker-job-failed-${var.environment_name}"
      period      = 900
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "attempts"
    expression  = "FILL(started, 0) - FILL(requeued, 0)"
    label       = "Completed attempts"
    return_data = false
  }

  metric_query {
    id          = "failures"
    expression  = "FILL(failed, 0)"
    label       = "Failures"
    return_data = false
  }

  metric_query {
    id          = "rate"
    expression  = "IF(attempts >= ${var.worker_job_failure_rate_min_jobs}, 100 * failures / attempts, 0)"
    label       = "Worker Job Failure Rate"
    return_data = true
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}


resource "aws_cloudwatch_metric_alarm" "worker_job_failures" {
  alarm_name          = "${var.environment_name}-worker-job-failures"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 4
  datapoints_to_alarm = 2
  threshold           = var.worker_job_failure_count_threshold
  period              = 900
  statistic           = "Sum"
  namespace           = "LogMetrics"
  metric_name         = "worker-job-failed-${var.environment_name}"
  treat_missing_data  = "notBreaching"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}
