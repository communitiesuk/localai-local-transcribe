output "rds_security_group_id" {
  value       = aws_security_group.main.id
  description = "The id of the rds security group"
}

output "database_url" {
  value       = aws_db_instance.main.address
  description = "The database host address"
}

output "database_identifier" {
  value       = aws_db_instance.main.identifier
  description = "The identifier of the DB instance"
}

output "database_name" {
  value       = aws_db_instance.main.db_name
  description = "The name of the database"
}
