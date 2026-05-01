output "ecr_frontend_repository_url" {
  value       = aws_ecr_repository.frontend.repository_url
  description = "URL of the ecr repository containing the frontend image"
}

output "ecr_backend_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "URL of the ecr repository containing the backend image"
}

output "ecr_worker_repository_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "URL of the ecr repository containing the worker image"
}

output "push_frontend_ecr_image_policy_arn" {
  value       = aws_iam_policy.push_frontend_images.arn
  description = "iam policy allowing pushing to the frontend ecr repository"
}

output "push_backend_ecr_image_policy_arn" {
  value       = aws_iam_policy.push_backend_images.arn
  description = "iam policy allowing pushing to the backend ecr repository"
}

output "push_worker_ecr_image_policy_arn" {
  value       = aws_iam_policy.push_worker_images.arn
  description = "iam policy allowing pushing to the worker ecr repository"
}
