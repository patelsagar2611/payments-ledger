# Execution role: used by the ECS agent to start the task
# (pull the image, read the DB secret, write logs). The app's code never sees it.
resource "aws_iam_role" "task_execution" {
  name = "ledger-task-execution"

  # Trust policy: WHO may assume this role. Only the ECS tasks service.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

# Permission policy (AWS-managed): ECR pull + CloudWatch Logs.
# It does not cover Secrets Manager; that needs its own statement.
resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "task_execution_secret" {
  name = "ledger-task-execution-secret"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = aws_db_instance.main.master_user_secret[0].secret_arn
      }
    ]
  })
}

# Task role: what the app's own code may call in AWS. No permissions yet.
resource "aws_iam_role" "task" {
  name = "ledger-task"

  # Trust policy: WHO may assume this role. Only the ECS tasks service.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/ledger-api"
  retention_in_days = 7
}