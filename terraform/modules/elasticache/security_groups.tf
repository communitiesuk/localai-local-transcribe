resource "aws_security_group" "redis" {
  name        = "${var.environment_name}-redis"
  description = "Redis security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}