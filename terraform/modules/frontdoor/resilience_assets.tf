module "resilience_assets_bucket" {
  source                        = "../s3_bucket"
  bucket_name                   = "local-transcribe-resilience-assets-${var.environment_name}"
  access_log_bucket_name        = "local-transcribe-resilience-assets-access-logs-${var.environment_name}"
  access_s3_log_expiration_days = 700
  policy                        = data.aws_iam_policy_document.resilience_assets.json
}

resource "aws_s3_object" "security_txt" {
  bucket       = module.resilience_assets_bucket.bucket
  key          = ".well-known/security.txt"
  source       = "../modules/frontdoor/well_known/security.txt"
  content_type = "text/plain"
}

# The index file needs to match the path name so it can be found
resource "aws_s3_object" "maintenance_page_index_file" {
  bucket        = module.resilience_assets_bucket.bucket
  key           = "maintenance"
  source        = "../modules/frontdoor/maintenance_page/index.html"
  content_type  = "text/html"
  cache_control = "no-cache"
}

resource "aws_s3_object" "maintenance_page_style_file" {
  bucket       = module.resilience_assets_bucket.bucket
  key          = "govuk-frontend-6.3.0.min.css"
  source       = "../modules/frontdoor/maintenance_page/govuk-frontend-6.3.0.min.css"
  content_type = "text/css"
}

resource "aws_s3_object" "assets" {
  for_each = fileset("${path.module}/maintenance_page/assets", "**")

  bucket = module.resilience_assets_bucket.bucket
  key    = "assets/${each.value}"
  source = "${path.module}/maintenance_page/assets/${each.value}"

  content_type = lookup(
    {
      css   = "text/css"
      svg   = "image/svg+xml"
      png   = "image/png"
      ico   = "image/x-icon"
      json  = "application/json"
      woff  = "font/woff"
      woff2 = "font/woff2"
    },
    regex("[^.]+$", each.value),
    "application/octet-stream"
  )
}

data "aws_iam_policy_document" "resilience_assets" {
  statement {
    sid = "AllowGetFromCloudfront"
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.resilience_assets_oai.iam_arn]
    }
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${module.resilience_assets_bucket.bucket_arn}/*"]
  }
}