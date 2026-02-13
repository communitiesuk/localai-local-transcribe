resource "aws_kms_key" "minute_webapp_secrets" {
  description         = "minute-webapp-secrets-${var.environment_name}"
  enable_key_rotation = true

  tags = {
    "terraform-plan-read" = true
  }
}

resource "aws_kms_alias" "minute_webapp_secrets" {
  target_key_id = aws_kms_key.minute_webapp_secrets.key_id
  name          = "alias/minute-webapp-secrets-${var.environment_name}"
}
