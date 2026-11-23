# Traffic chain: internet -> ALB (80) -> task (8000) -> RDS (5432).
# Rules are separate resources, so groups can reference each other without a cycle.

resource "aws_security_group" "alb" {
  name        = "ledger-alb-sg"
  description = "Load balancer: HTTP from the internet"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "ledger-alb-sg" }
}

resource "aws_security_group" "task" {
  name        = "ledger-task-sg"
  description = "App tasks: port 8000 from the load balancer only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "ledger-task-sg" }
}

resource "aws_security_group" "rds" {
  name        = "ledger-rds-sg"
  description = "Database: Postgres 5432 from the app tasks only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "ledger-rds-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http_from_internet" {
  security_group_id = aws_security_group.alb.id
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "task_https_to_internet" {
  security_group_id = aws_security_group.task.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_task" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.task.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

resource "aws_vpc_security_group_ingress_rule" "task_from_alb" {
  security_group_id            = aws_security_group.task.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

resource "aws_vpc_security_group_egress_rule" "task_to_rds" {
  security_group_id            = aws_security_group.task.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_task" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.task.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_db_subnet_group" "main" {
  name       = "ledger-db-subnets"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = { Name = "ledger-db-subnets" }
}
