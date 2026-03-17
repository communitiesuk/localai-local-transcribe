#tfsec:ignore:AVD-AWS-0176:iam authentication not suitable as tokens only last 15minutes, password authentication preferred
resource "aws_db_instance" "main" {
  identifier                      = "${var.environment_name}-database"
  db_name                         = "prsdb"
  allocated_storage               = var.allocated_storage #units are GiB
  backup_retention_period         = var.backup_retention_period
  backup_window                   = var.backup_window
  db_subnet_group_name            = var.db_subnet_group_name
  delete_automated_backups        = false
  deletion_protection             = true # needs to be set to false and applied if you need to delete the DB
  engine                          = "postgres"
  engine_version                  = "16.8"
  final_snapshot_identifier       = "${var.environment_name}-database-final-snapshot"
  instance_class                  = var.instance_class
  maintenance_window              = var.maintenance_window
  multi_az                        = var.multi_az
  password                        = var.database_password
  port                            = var.database_port
  publicly_accessible             = false
  storage_encrypted               = true
  storage_type                    = "gp2"
  username                        = "postgres"
  vpc_security_group_ids          = [aws_security_group.main.id]
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.performance_insights.arn
  # RDS comes with 7 days of performance insights retention for free, which should be enough for our needs
  performance_insights_retention_period = 7

  lifecycle {
    # Both this and delete_protection parameter above also needs to be set to false and applied to destroy the DB
    prevent_destroy = true
    # AWS will perform automatic minor version updates, so we want to ignore these - remove this temporarily if wanting to e.g. change the major version
    ignore_changes = [engine_version]
  }
}
