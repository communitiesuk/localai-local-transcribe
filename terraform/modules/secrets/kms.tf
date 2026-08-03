resource "aws_kms_key" "local_transcribe_secrets" {
  description         = "local-transcribe-secrets-${var.environment_name}"
  enable_key_rotation = true

  tags = {
    "terraform-plan-read" = true
  }
}

resource "aws_kms_alias" "local_transcribe_secrets" {
  target_key_id = aws_kms_key.local_transcribe_secrets.key_id
  name          = "alias/local-transcribe-secrets-${var.environment_name}"
}
