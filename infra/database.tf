resource "aws_db_instance" "main" {
  identifier                  = "ledger-db"
  engine                      = "postgres"
  engine_version              = "17"
  instance_class              = "db.t4g.micro"
  allocated_storage           = 20
  storage_type                = "gp3"
  db_name                     = "ledger"
  username                    = "ledger"
  manage_master_user_password = true
  db_subnet_group_name        = aws_db_subnet_group.main.name
  vpc_security_group_ids      = [aws_security_group.rds.id]
  publicly_accessible         = false
  multi_az                    = false
  skip_final_snapshot         = true
  deletion_protection         = false
}
