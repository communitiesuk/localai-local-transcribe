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

resource "aws_secretsmanager_secret" "database_secret" {
  name                    = "${var.environment_name}-local-transcribe-database-secret"
  description             = "Local-transcribe backend database secret(alternating users rotation)"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.rds_secrets.arn
}

resource "random_password" "app_user_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret_version" "database_secret" {
  secret_id = aws_secretsmanager_secret.database_secret.id
  secret_string = jsonencode({
    username  = "app_user"
    password  = random_password.app_user_password.result
    engine    = "postgres"
    host      = var.database_url
    port      = var.database_port
    dbname    = var.db_name
    masterarn = var.master_user_secret_arn
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret_rotation" "rds_database" {
  secret_id           = aws_secretsmanager_secret.database_secret.id
  rotation_lambda_arn = aws_serverlessapplicationrepository_cloudformation_stack.rds_rotation_lambda.outputs["RotationLambdaARN"]
  rotation_rules {
    automatically_after_days = var.rotation_days
  }
}

data "aws_serverlessapplicationrepository_application" "rds_rotation_lambda" {
  application_id = "arn:aws:serverlessrepo:us-east-1:297356227824:applications/SecretsManagerRDSPostgreSQLRotationMultiUser"

}
 
data "aws_secretsmanager_secret_version" "rds_master" {
  secret_id = var.master_user_secret_arn
}

resource "aws_serverlessapplicationrepository_cloudformation_stack" "rds_rotation_lambda" {
  name             = "${var.environment_name}-db-rotation-lambda"
  application_id   = data.aws_serverlessapplicationrepository_application.rds_rotation_lambda.application_id
  capabilities     = data.aws_serverlessapplicationrepository_application.rds_rotation_lambda.required_capabilities
  semantic_version = "1.1.692"

  parameters = {
    functionName        = "${var.environment_name}-rotation-function"
    endpoint            = var.database_url
    vpcSubnetIds        = join(",", var.private_subnet_ids)
    vpcSecurityGroupIds = var.lambda_rotation_sg_id
    superuserSecretArn  = var.master_user_secret_arn

  }

}


