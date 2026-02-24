resource "aws_ssm_parameter" "database_username" {
  name  = "${var.environment_name}-minute-database-username"
  type  = "String"
  value = aws_db_instance.main.username
}
