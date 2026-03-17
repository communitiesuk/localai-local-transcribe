resource "aws_cloudwatch_log_metric_filter" "assume_role_with_saml" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "assume-role-with-saml-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = "AssumeRoleWithSAML")}
  EOT

  metric_transformation {
    name      = "assume-role-with-saml-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "unauthorized_api_calls" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "unauthorized-api-calls-${var.environment_name}"
  pattern        = <<EOT
    {(($.errorCode = UnauthorizedOperation) ||
      ($.errorCode = AccessDenied)) &&
     ($.userIdentity.sessionContext.sessionIssuer.arn != "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/WizAccess-Role")}
  EOT

  metric_transformation {
    name      = "unauthorized-api-calls-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "iam_policy_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "iam-policy-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = DeleteGroupPolicy) ||
     ($.eventName = DeleteRolePolicy) ||
     ($.eventName = DeleteUserPolicy) ||
     ($.eventName = PutGroupPolicy) ||
     ($.eventName = PutRolePolicy) ||
     ($.eventName = PutUserPolicy) ||
     ($.eventName = CreatePolicy) ||
     ($.eventName = DeletePolicy) ||
     ($.eventName = CreatePolicyVersion) ||
     ($.eventName = DeletePolicyVersion) ||
     ($.eventName = AttachRolePolicy) ||
     ($.eventName = DetachRolePolicy) ||
     ($.eventName = AttachUserPolicy) ||
     ($.eventName = DetachUserPolicy) ||
     ($.eventName = AttachGroupPolicy)||
     ($.eventName = DetachGroupPolicy)}
  EOT

  metric_transformation {
    name      = "iam-policy-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "cloudtrail_config_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "cloudtrail-config-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = CreateTrail) ||
     ($.eventName = UpdateTrail) ||
     ($.eventName = DeleteTrail) ||
     ($.eventName = StartLogging) ||
     ($.eventName = StopLogging)}
  EOT

  metric_transformation {
    name      = "cloudtrail-config-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "s3_bucket_policy_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "s3-bucket-policy-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventSource = s3.amazonaws.com) &&
     (($.eventName = PutBucketAcl) ||
      ($.eventName = PutBucketPolicy) ||
      ($.eventName = PutBucketCors) ||
      ($.eventName = PutBucketLifecycle) ||
      ($.eventName = PutBucketReplication) ||
      ($.eventName = DeleteBucketPolicy) ||
      ($.eventName = DeleteBucketCors) ||
      ($.eventName = DeleteBucketLifecycle) ||
      ($.eventName = DeleteBucketReplication))}
  EOT

  metric_transformation {
    name      = "s3-bucket-policy-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "network_gateway_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "network-gateway-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = CreateCustomerGateway) ||
     ($.eventName = DeleteCustomerGateway) ||
     ($.eventName = AttachInternetGateway) ||
     ($.eventName = CreateInternetGateway) ||
     ($.eventName = DeleteInternetGateway) ||
     ($.eventName = DetachInternetGateway)}
  EOT

  metric_transformation {
    name      = "network-gateway-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "route_tables_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "route-tables-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = CreateRoute) ||
     ($.eventName = CreateRouteTable) ||
     ($.eventName = ReplaceRoute) ||
     ($.eventName = ReplaceRouteTableAssociation) ||
     ($.eventName = DeleteRouteTable) ||
     ($.eventName = DeleteRoute) ||
     ($.eventName = DisassociateRouteTable)}
  EOT

  metric_transformation {
    name      = "route-tables-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "vpc_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "vpc-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventName = CreateVpc) ||
     ($.eventName = DeleteVpc) ||
     ($.eventName = ModifyVpcAttribute) ||
     ($.eventName = AcceptVpcPeeringConnection) ||
     ($.eventName = CreateVpcPeeringConnection) ||
     ($.eventName = DeleteVpcPeeringConnection) ||
     ($.eventName = RejectVpcPeeringConnection) ||
     ($.eventName = AttachClassicLinkVpc) ||
     ($.eventName = DetachClassicLinkVpc) ||
     ($.eventName = DisableVpcClassicLink) ||
     ($.eventName = EnableVpcClassicLink)}
  EOT

  metric_transformation {
    name      = "vpc-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "organization_changes" {
  log_group_name = module.cloudtrail_cloudwatch_group.name
  name           = "organization-changes-${var.environment_name}"
  pattern        = <<EOT
    {($.eventSource = organizations.amazonaws.com) &&
     (($.eventName = AcceptHandshake) ||
      ($.eventName = AttachPolicy) ||
      ($.eventName = CreateAccount) ||
      ($.eventName = CreateOrganizationalUnit) ||
      ($.eventName = CreatePolicy) ||
      ($.eventName = DeclineHandshake) ||
      ($.eventName = DeleteOrganization) ||
      ($.eventName = DeleteOrganizationalUnit) ||
      ($.eventName = DeletePolicy) ||
      ($.eventName = DetachPolicy) ||
      ($.eventName = DisablePolicyType) ||
      ($.eventName = EnablePolicyType) ||
      ($.eventName = InviteAccountToOrganization) ||
      ($.eventName = LeaveOrganization) ||
      ($.eventName = MoveAccount) ||
      ($.eventName = RemoveAccountFromOrganization) ||
      ($.eventName = UpdatePolicy) ||
      ($.eventName = UpdateOrganizationalUnit))}
  EOT

  metric_transformation {
    name      = "organization-changes-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ecs_task_start_failure" {
  log_group_name = module.ecs_events_log_group.name
  name           = "ecs-task-start-failure-${var.environment_name}"
  pattern        = <<EOT
    {($.detail.stopCode = "TaskFailedToStart") &&
     ($.detail-type = "ECS Task State Change")}
  EOT

  metric_transformation {
    name      = "ecs-task-start-failure-${var.environment_name}"
    namespace = "LogMetrics"
    value     = "1"
  }
}