output "evals_private_subnet" {
  value       = aws_subnet.evals_private
  description = "Private subnet that evals tasks run in"
  depends_on  = [aws_route_table_association.evals_private]
}

output "evals_kms_key_arn" {
  value       = aws_kms_key.evals.arn
  description = "Arn of the customer-managed key that encrypts the evals data buckets"
}

output "evals_buckets" {
  value = {
    for name, bucket in module.evals_bucket : name => {
      name = bucket.bucket
      arn  = bucket.bucket_arn
    }
  }
  description = "Name and arn of each evals data bucket, keyed by quarantine, assets, outputs and results"
}

output "evals_task_security_group_id" {
  value       = aws_security_group.evals_tasks.id
  description = "Security group the silver transcript task runs in. It has no inbound rules"
}

output "silver_task_family" {
  value       = local.silver_task_family
  description = "Task definition family the promotion Lambda starts. AIILG-1305 creates this family"
}
