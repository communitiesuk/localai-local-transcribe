resource "aws_cloudwatch_metric_alarm" "ecs_cpu_usage" {
  alarm_name          = "${var.ecs_service_name}-cpu-usage"
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
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_usage" {
  alarm_name          = "${var.ecs_service_name}-memory-usage"
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
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_start_failure" {
  alarm_name          = "${var.ecs_service_name}-ecs-task-start-failure"
  alarm_description   = "An ECS task has failed to start and reach a healthy state"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  metric_name         = aws_cloudwatch_log_metric_filter.ecs_task_start_failure.name
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

resource "aws_cloudwatch_metric_alarm" "elasticache_cpu_usage" {
  for_each = var.elasticache_cluster_ids

  alarm_name          = "${each.value}-cpu-usage"
  alarm_description   = "ElastiCache CPU utilization has been >90% for over a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  evaluation_periods  = 1
  period              = 60
  threshold           = 90
  statistic           = "Average"

  dimensions = {
    CacheClusterId = each.value
  }

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "elasticache_memory_usage" {
  for_each = var.elasticache_cluster_ids

  alarm_name          = "${each.value}-memory-usage"
  alarm_description   = "ElastiCache memory usage has been >90% for over a minute"
  comparison_operator = "GreaterThanThreshold"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  evaluation_periods  = 1
  period              = 60
  threshold           = 90
  statistic           = "Average"

  dimensions = {
    CacheClusterId = each.value
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