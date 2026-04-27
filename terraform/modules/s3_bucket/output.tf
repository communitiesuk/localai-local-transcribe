output "bucket" {
  value       = aws_s3_bucket.main.bucket
  description = "The bucket"
}

output "bucket_arn" {
  value       = aws_s3_bucket.main.arn
  description = "The arn of the bucket"
}

output "bucket_id" {
  value       = aws_s3_bucket.main.id
  description = "The id of the bucket"
}

output "bucket_regional_domain_name" {
  value       = aws_s3_bucket.main.bucket_regional_domain_name
  description = "The domain name of the bucket"
}