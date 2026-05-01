resource "aws_ssm_parameter" "database_username" {
  name  = "${var.environment_name}-local-transcribe-database-username"
  type  = "String"
  value = aws_db_instance.main.username
}
