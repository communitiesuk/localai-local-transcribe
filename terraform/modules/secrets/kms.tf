resource "aws_kms_key" "minute_secrets" {
  description         = "minute-secrets-${var.environment_name}"
  enable_key_rotation = true

  tags = {
    "terraform-plan-read" = true
  }
}

resource "aws_kms_alias" "minute_secrets" {
  target_key_id = aws_kms_key.minute_secrets.key_id
  name          = "alias/minute-secrets-${var.environment_name}"
}
