output "ecr_repository_url" {
  description = "ECR repository URL to push the worker image."
  value       = aws_ecr_repository.agent.repository_url
}

output "sqs_queue_url" {
  description = "Primary SQS queue URL for event messages."
  value       = aws_sqs_queue.events.url
}

output "sqs_queue_arn" {
  description = "Primary SQS queue ARN for IAM policies and auditing."
  value       = aws_sqs_queue.events.arn
}

output "sqs_dlq_url" {
  description = "Dead-letter queue URL."
  value       = aws_sqs_queue.dlq.url
}

output "sqs_worker_irsa_role_arn" {
  description = "IAM role ARN to annotate on the Kubernetes service account."
  value       = aws_iam_role.sqs_worker_irsa.arn
}
