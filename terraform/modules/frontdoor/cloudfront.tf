locals {
  origin_id             = "origin-${var.environment_name}"
  maintenance_origin_id = "maintenance-origin-${var.environment_name}"
}

resource "aws_cloudfront_origin_access_identity" "maintenance_oai" {
  comment = "OAI for maintenance page S3 bucket"
}

#tfsec:ignore:aws-cloudfront-enable-logging: TODO we will be implementing logging later
resource "aws_cloudfront_distribution" "main" {
  aliases         = var.ssl_certs_created ? var.cloudfront_domain_names : []
  enabled         = true
  http_version    = "http2and3"
  is_ipv6_enabled = true
  price_class     = "PriceClass_100" # Affects which edge locations are used by cloudfront, which affects the latency users will experience in different geographic areas

  web_acl_id = aws_wafv2_web_acl.main.arn

  origin {
    domain_name = var.ssl_certs_created ? var.load_balancer_domain_name : aws_lb.main.dns_name
    origin_id   = local.origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = var.ssl_certs_created ? "https-only" : "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = local.cloudfront_header_name
      value = random_password.cloudfront_header.result
    }
  }

  default_cache_behavior {
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    cache_policy_id            = aws_cloudfront_cache_policy.main.id
    compress                   = true
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.main.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.main.id
    target_origin_id           = local.origin_id
    viewer_protocol_policy     = "redirect-to-https"
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.url_rewriter.arn
    }
  }

  origin {
    domain_name = module.maintenance_page_bucket.bucket_regional_domain_name
    origin_id   = local.maintenance_origin_id

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.maintenance_oai.cloudfront_access_identity_path
    }
  }

  ordered_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.main.id
    path_pattern           = "/govuk-frontend-5.11.2.min.css"
    target_origin_id       = local.maintenance_origin_id
    viewer_protocol_policy = "redirect-to-https"
  }

  ordered_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.main.id
    path_pattern           = var.maintenance_mode_on ? "*" : "/maintenance"
    target_origin_id       = local.maintenance_origin_id
    viewer_protocol_policy = "redirect-to-https"
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.url_rewriter.arn
    }
  }

  custom_error_response {
    error_code         = 501
    response_code      = 501
    response_page_path = "/maintenance"
  }

  custom_error_response {
    error_code         = 502
    response_code      = 502
    response_page_path = "/maintenance"
  }

  custom_error_response {
    error_code         = 503
    response_code      = 503
    response_page_path = "/maintenance"
  }

  custom_error_response {
    error_code         = 504
    response_code      = 504
    response_page_path = "/maintenance"
  }

  dynamic "custom_error_response" {
    for_each = var.maintenance_mode_on ? ["this"] : []
    content {
      error_code         = 404
      response_code      = 200
      response_page_path = "/maintenance"
    }
  }

  dynamic "custom_error_response" {
    for_each = var.maintenance_mode_on ? ["this"] : []
    content {
      error_code         = 403
      response_code      = 200
      response_page_path = "/maintenance"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.ssl_certs_created ? false : true
    acm_certificate_arn            = var.ssl_certs_created ? var.cloudfront_certificate_arn : null
    minimum_protocol_version       = var.ssl_certs_created ? "TLSv1.2_2021" : null
    ssl_support_method             = "sni-only"
  }

  restrictions {
    geo_restriction {
      restriction_type = var.geolocation_allow_list != null ? "whitelist" : "none"
      locations        = var.geolocation_allow_list != null ? var.geolocation_allow_list : []
    }
  }

  tags = {
    Name = "cloudfront=${var.environment_name}"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_cloudfront_cache_policy" "main" {
  name        = var.environment_name
  min_ttl     = 1
  default_ttl = 60

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "all"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "all"
    }

    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

data "aws_cloudfront_response_headers_policy" "main" {
  name = "Managed-SecurityHeadersPolicy"
}

resource "aws_cloudfront_origin_request_policy" "main" {
  name = var.environment_name

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "allViewer"
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "random_password" "cloudfront_header" {
  length  = 16
  special = false
}

resource "aws_cloudfront_function" "url_rewriter" {
  name    = "url-rewriter"
  runtime = "cloudfront-js-2.0"
  comment = "Rewrites URLs to include the service line as the first path segment"
  publish = true
  code    = file("${path.module}/url_rewriter.js")
}

resource "aws_shield_subscription" "cloudfront" {
  count = var.use_aws_shield_advanced ? 1 : 0
}

resource "aws_shield_protection" "cloudfront" {
  count = var.use_aws_shield_advanced ? 1 : 0

  name         = "cloudfront"
  resource_arn = aws_cloudfront_distribution.main.arn
}