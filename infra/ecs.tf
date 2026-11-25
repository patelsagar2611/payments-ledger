# The ECR repository lives in its own state (infra/ecr/), so this stack
# only reads it. A data source looks up an existing object; it never creates
# or destroys anything.
data "aws_ecr_repository" "app" {
  name = "payments-ledger"
}

resource "aws_ecs_cluster" "main" {
  name = "ledger-cluster"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "ledger-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${data.aws_ecr_repository.app.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.main.address
        },
        {
          name  = "DB_PORT"
          value = tostring(aws_db_instance.main.port)
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.main.db_name
        }
      ]
      secrets = [
        {
          name      = "DB_USER"
          valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:password::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = "ap-southeast-2"
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}