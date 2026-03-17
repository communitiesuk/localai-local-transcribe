resource "aws_ssm_parameter" "database_username" {
  name  = "${var.environment_name}-prsdb-database-username"
  type  = "String"
  value = aws_db_instance.main.username
}

resource "aws_ssm_parameter" "database_url" {
  name  = "${var.environment_name}-prsdb-database-url"
  type  = "String"
  value = "${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
}
