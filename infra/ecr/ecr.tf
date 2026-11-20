resource "aws_ecr_repository" "app" {
  name                 = "payments-ledger"
  image_tag_mutability = "IMMUTABLE" # a tag can never be re-pointed at different contents

  image_scanning_configuration {
    scan_on_push = true # free basic scan for known vulnerabilities in OS packages
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

output "repository_url" {
  value = aws_ecr_repository.app.repository_url
}
