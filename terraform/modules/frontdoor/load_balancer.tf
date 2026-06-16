#tfsec:ignore:aws-elb-alb-not-public:the load balancer must be exposed to the internet in order to communicate with cloudfront
locals {
  gds_ia_issuer               = "https://sso.service.security.gov.uk"
  listener_rule_base_priority = 1

}

resource "aws_lb" "main" {
  name                       = "alb-${var.environment_name}"
  drop_invalid_header_fields = true
  enable_deletion_protection = true
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.load_balancer.id]
  subnets                    = var.public_subnet_ids

  access_logs {
    bucket  = module.alb_logs.bucket
    prefix  = "alb"
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

module "alb_logs" {
  source = "../s3_bucket"

  bucket_name                        = "alb-logs-${var.environment_name}"
  access_log_bucket_name             = "alb-logs-${var.environment_name}-access-logs"
  force_destroy                      = false
  object_lock_enabled                = false
  noncurrent_version_expiration_days = 700
  access_s3_log_expiration_days      = 365
  policy                             = data.aws_iam_policy_document.alb_logs_bucket_policy.json
  kms_key_arn                        = null
}

data "aws_iam_policy_document" "alb_logs_bucket_policy" {
  statement {
    sid    = "AWSLogDeliveryAclCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["logdelivery.elasticloadbalancing.amazonaws.com"]
    }

    actions   = ["s3:GetBucketAcl"]
    resources = [module.alb_logs.bucket_arn]
  }

  statement {
    sid    = "AWSLogDeliveryWrite"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["logdelivery.elasticloadbalancing.amazonaws.com"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${module.alb_logs.bucket_arn}/*"]
    

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [aws_lb.main.arn]
    }
  }
}


resource "aws_lb_listener" "https" {
  count = var.ssl_certs_created ? 1 : 0

  certificate_arn   = var.load_balancer_certificate_arn
  load_balancer_arn = aws_lb.main.id
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "403: Forbidden"
      status_code  = "403"
    }

    order = 50000 # this is the highest value possible so will be performed last out of all listener rules
  }
}

resource "aws_security_group" "load_balancer" {
  name        = "load-balancer-sg-${var.environment_name}"
  description = "Load Balancer security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_target_group" "frontend" {
  name                          = var.environment_name
  port                          = var.frontend_port
  protocol                      = "HTTP"
  vpc_id                        = var.vpc_id
  target_type                   = "ip"
  load_balancing_algorithm_type = "least_outstanding_requests"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 5
    interval            = 30
    protocol            = "HTTP"
    matcher             = "200"
    timeout             = 10
    path                = "/health"
    port                = var.frontend_port
  }
}


data "aws_ssm_parameter" "oidc_client_id" {
  count           = var.ssl_certs_created && var.enable_oidc_auth ? 1 : 0
  name            = var.internal_access_oidc_client_id_name
  with_decryption = true
}

data "aws_ssm_parameter" "oidc_client_secret" {
  count           = var.ssl_certs_created && var.enable_oidc_auth ? 1 : 0
  name            = var.internal_access_oidc_client_secret_name
  with_decryption = true
}

resource "aws_lb_listener_rule" "authentication" {
  count        = var.ssl_certs_created && var.enable_oidc_auth ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = local.listener_rule_base_priority + 1

  action {
    type = "authenticate-oidc"

    authenticate_oidc {
      client_id              = data.aws_ssm_parameter.oidc_client_id[0].value
      issuer                 = local.gds_ia_issuer
      authorization_endpoint = "${local.gds_ia_issuer}/auth/oidc"
      token_endpoint         = "${local.gds_ia_issuer}/auth/token"
      user_info_endpoint     = "${local.gds_ia_issuer}/auth/profile"
      session_cookie_name    = "X-Amzn-Oidc-Data"
      client_secret          = data.aws_ssm_parameter.oidc_client_secret[0].value
      scope                  = "openid profile email"
      session_timeout        = 604800
    }
  }

  action {
    target_group_arn = aws_lb_target_group.frontend.id
    type             = "forward"
  }

  condition {
    host_header {
      values = [var.app_host]
    }
  }

  condition {
    http_header {
      http_header_name = local.cloudfront_header_name
      values           = [random_password.cloudfront_header.result]
    }
  }
}

resource "aws_lb_listener_rule" "signout" {
  count        = var.ssl_certs_created && var.enable_oidc_auth ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = local.listener_rule_base_priority

  action {
    target_group_arn = aws_lb_target_group.frontend.id
    type             = "forward"
  }

  condition {
    host_header {
      values = [var.app_host]
    }
  }

  condition {
    http_header {
      http_header_name = local.cloudfront_header_name
      values           = [random_password.cloudfront_header.result]
    }
  }

  condition {
    path_pattern {
      values = ["/signout", "/signout/"]
    }
  }
}

resource "aws_lb_listener_rule" "forward_no_auth" {
  count        = var.ssl_certs_created && !var.enable_oidc_auth ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = local.listener_rule_base_priority + 2


  action {
    target_group_arn = aws_lb_target_group.frontend.id
    type             = "forward"
  }

  condition {
    host_header {
      values = [var.app_host]
    }
  }

  condition {
    http_header {
      http_header_name = local.cloudfront_header_name
      values           = [random_password.cloudfront_header.result]
    }
  }
}

data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_https_ingress" {
  description       = "Allow https ingress from cloudfront only"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
  security_group_id = aws_security_group.load_balancer.id
}

resource "aws_vpc_security_group_egress_rule" "load_balancer_https_egress" {
  description       = "Allow https egress for OIDC token and user info endpoints"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
  security_group_id = aws_security_group.load_balancer.id
}

resource "aws_wafv2_web_acl_association" "load_balancer" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.load_balancer.arn
}

resource "aws_shield_protection" "load_balancer" {
  count = var.use_aws_shield_advanced ? 1 : 0

  name         = "load_balancer"
  resource_arn = aws_lb.main.arn
}