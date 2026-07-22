resource "postgresql_role" "app_user" {
  name                = "app_user"
  login               = true
  password_wo         = var.app_user_password
  password_wo_version = 1

}