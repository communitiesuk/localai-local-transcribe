module "frontend_log_group" {
  source             = "../encrypted_log_group"
  log_group_name     = "${var.environment_name}-frontend"
  log_retention_days = 365
}

module "backend_log_group" {
  source             = "../encrypted_log_group"
  log_group_name     = "${var.environment_name}-backend"
  log_retention_days = 365
}

module "worker_log_group" {
  source             = "../encrypted_log_group"
  log_group_name     = "${var.environment_name}-worker"
  log_retention_days = 365
}
