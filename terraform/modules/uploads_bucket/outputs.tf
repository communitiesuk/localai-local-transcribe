output "bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = module.uploads_bucket.bucket_id
}
