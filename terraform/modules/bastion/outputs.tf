output "security_group_id" {
  description = "Id of the bastion security group"
  value       = aws_security_group.bastion.id
}

output "bastion_instance_arns" {
  description = "List of Bastion instance IDs"
  value       = aws_instance.bastion[*].arn
}
