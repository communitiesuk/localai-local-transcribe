output "transcription_queue_name" {
  value       = aws_sqs_queue.transcription_queue.name
  description = "name of transcription sqs queue"
}

output "transcription_deadletter_queue_name" {
  value       = aws_sqs_queue.transcription_queue_deadletter.name
  description = "name of transcription deadletter sqs queue"
}

output "llm_queue_name" {
  value       = aws_sqs_queue.llm_queue.name
  description = "name of llm sqs queue"
}

output "llm_deadletter_queue_name" {
  value       = aws_sqs_queue.llm_queue_deadletter.name
  description = "name of llm deadletter sqs queue"
}
