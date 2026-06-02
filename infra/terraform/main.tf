locals {
  app_name   = "${var.name_prefix}-${var.environment}"
  queue_name = "${local.app_name}-events"
  dlq_name   = "${local.app_name}-events-dlq"

  oidc_provider_hostpath = replace(var.eks_oidc_provider_url, "https://", "")
}

resource "aws_ecr_repository" "agent" {
  name                 = local.app_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = var.name_prefix
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "dlq" {
  name                      = local.dlq_name
  message_retention_seconds = 1209600

  tags = {
    Project     = var.name_prefix
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "events" {
  name                       = local.queue_name
  visibility_timeout_seconds = 120
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Project     = var.name_prefix
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "irsa_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.eks_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_hostpath}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_hostpath}:sub"
      values   = ["system:serviceaccount:${var.k8s_namespace}:${var.k8s_service_account_name}"]
    }
  }
}

resource "aws_iam_role" "sqs_worker_irsa" {
  name               = "${local.app_name}-sqs-worker-irsa"
  assume_role_policy = data.aws_iam_policy_document.irsa_assume_role.json

  tags = {
    Project     = var.name_prefix
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "sqs_worker_permissions" {
  statement {
    sid    = "SqsWorkerMainQueueAccess"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
    resources = [aws_sqs_queue.events.arn]
  }

  statement {
    sid    = "SqsWorkerDlqInspectAccess"
    effect = "Allow"
    actions = [
      "sqs:GetQueueAttributes"
    ]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_iam_role_policy" "sqs_worker_inline" {
  name   = "${local.app_name}-sqs-worker-inline"
  role   = aws_iam_role.sqs_worker_irsa.id
  policy = data.aws_iam_policy_document.sqs_worker_permissions.json
}
