# Resource - specific parameters are to be created in their respective modules

resource "aws_ssm_parameter" "one_login_public_key" {
  name  = "${var.environment_name}-one-login-public-key"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "one_login_client_id" {
  name  = "${var.environment_name}-one-login-client-id"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "one_login_issuer_url" {
  name  = "${var.environment_name}-one-login-issuer-url"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "one_login_did_url" {
  name  = "${var.environment_name}-one-login-did-url"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "epc_register_client_id" {
  name  = "${var.environment_name}-prsdb-epc-client-id"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "epc_register_token_uri" {
  name  = "${var.environment_name}-prsdb-epc-token-uri"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "epc_register_base_url" {
  name  = "${var.environment_name}-prsdb-epc-register-base-url"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "epc_certificate_base_url" {
  name  = "${var.environment_name}-prsdb-epc-certificate-base-url"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "landlord_base_url" {
  name  = "${var.environment_name}-prsdb-landlord-base-url"
  type  = "String"
  value = var.landlord_base_url
}

resource "aws_ssm_parameter" "local_council_base_url" {
  name  = "${var.environment_name}-prsdb-local-council-base-url"
  type  = "String"
  value = var.local_council_base_url
}

resource "aws_ssm_parameter" "plausible_analytics_domain_id" {
  name  = "${var.environment_name}-prsdb-plausible-analytics-domain-id"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "google_analytics_measurement_id" {
  name  = "${var.environment_name}-prsdb-google-analytics-measurement-id"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "google_analytics_cookie_domain" {
  name  = "${var.environment_name}-prsdb-google-analytics-cookie-domain"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "beta_feedback_team_email_address" {
  name  = "${var.environment_name}-prsdb-beta-feedback-team-email-address"
  type  = "String"
  value = "default_to_be_set_manually" # To be set manually on AWS

  lifecycle {
    ignore_changes = [value]
  }
}