module "maintenance_page_bucket" {
  source                        = "../s3_bucket"
  bucket_name                   = "prsdb-maintenance-page-${var.environment_name}"
  access_log_bucket_name        = "prsdb-maintenance-page-access-logs-${var.environment_name}"
  access_s3_log_expiration_days = 700
  policy                        = data.aws_iam_policy_document.maintenance_page.json
}

# The index file needs to match the path name so it can be found
resource "aws_s3_object" "maintenance_page_index_file" {
  bucket        = module.maintenance_page_bucket.bucket
  key           = "maintenance"
  source        = "../modules/frontdoor/maintenance_page/index.html"
  content_type  = "text/html"
  cache_control = "no-cache"
}

resource "aws_s3_object" "maintenance_page_style_file" {
  bucket       = module.maintenance_page_bucket.bucket
  key          = "govuk-frontend-5.11.2.min.css"
  source       = "../modules/frontdoor/maintenance_page/govuk-frontend-5.11.2.min.css"
  content_type = "text/css"
}

resource "aws_s3_object" "govuk_crest_svg" {
  bucket       = module.maintenance_page_bucket.bucket
  key          = "/assets/images/govuk-crest.svg"
  source       = "../modules/frontdoor/maintenance_page/assets/images/govuk-crest.svg"
  content_type = "image/svg+xml"
}

resource "aws_s3_object" "gds_font_bold" {
  bucket       = module.maintenance_page_bucket.bucket
  key          = "/assets/fonts/bold-b542beb274-v2.woff2"
  source       = "../modules/frontdoor/maintenance_page/assets/fonts/bold-b542beb274-v2.woff2"
  content_type = "font/woff2"
}

resource "aws_s3_object" "gds_font_light" {
  bucket       = module.maintenance_page_bucket.bucket
  key          = "/assets/fonts/light-94a07e06a1-v2.woff2"
  source       = "../modules/frontdoor/maintenance_page/assets/fonts/light-94a07e06a1-v2.woff2"
  content_type = "font/woff2"
}

data "aws_iam_policy_document" "maintenance_page" {
  statement {
    sid = "AllowGetFromCloudfront"
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.maintenance_oai.iam_arn]
    }
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${module.maintenance_page_bucket.bucket_arn}/*"]
  }
}