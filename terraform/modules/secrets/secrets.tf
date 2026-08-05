resource "aws_ssm_parameter" "oidc_client_id" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/oidc_secrets/client_id"
  description = "OIDC client ID for local-transcribe"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "oidc_client_secret" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/oidc_secrets/client_secret"
  description = "OIDC client secret for local-transcribe"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "azure_apim_tenant_id" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/azure/apim_tenant_id"
  description = "Azure tenant ID for APIM client secret auth"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "azure_apim_client_id" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/azure/apim_client_id"
  description = "Azure client ID for APIM client secret auth"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "azure_apim_client_secret" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/azure/apim_client_secret"
  description = "Azure client secret for APIM client secret auth"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "azure_apim_scope" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/azure/apim_scope"
  description = "OAuth scope for APIM client secret auth"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "azure_apim_subscription_key" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/azure/apim_subscription_key"
  description = "Azure APIM subscription key"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "sentry_dsn" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/sentry/dsn"
  description = "Sentry DSN for local-transcribe"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "govnotify_api_key" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/govnotify/api_key"
  description = "GovNotify API key"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "govnotify_invite_template_id" {
  type        = "SecureString"
  key_id      = aws_kms_key.local_transcribe_secrets.arn
  name        = "/local-transcribe/govnotify/invite_template_id"
  description = "GovNotify invite email template ID"
  value       = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_secretsmanager_secret" "database_password" {
  name                    = "tf-${var.environment_name}-local-transcribe-database-password"
  description             = "Password for local-transcribe backend database user"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.local_transcribe_secrets.arn
}

resource "random_password" "database_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id     = aws_secretsmanager_secret.database_password.id
  secret_string = random_password.database_password.result
}
