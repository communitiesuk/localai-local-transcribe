output "evals_private_subnet" {
  value       = aws_subnet.evals_private
  description = "Private subnet that evals tasks run in"
  depends_on  = [aws_route_table_association.evals_private]
}
