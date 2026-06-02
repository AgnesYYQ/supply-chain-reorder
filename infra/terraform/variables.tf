variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix used for created resources."
  type        = string
  default     = "supply-chain"
}

variable "environment" {
  description = "Environment label, e.g. dev/stage/prod."
  type        = string
  default     = "dev"
}

variable "k8s_namespace" {
  description = "Kubernetes namespace where the worker runs."
  type        = string
  default     = "supply-chain"
}

variable "k8s_service_account_name" {
  description = "Kubernetes service account name for the worker."
  type        = string
  default     = "supply-chain-sqs-worker"
}

variable "eks_oidc_provider_arn" {
  description = "OIDC provider ARN for the EKS cluster (for IRSA)."
  type        = string
}

variable "eks_oidc_provider_url" {
  description = "OIDC provider URL for the EKS cluster, e.g. https://oidc.eks.<region>.amazonaws.com/id/<id>."
  type        = string
}
