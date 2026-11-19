terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" # any 6.x, never 7.0 without you choosing it
    }
  }
}

provider "aws" {
  region  = "ap-southeast-2"
  profile = "ledger-login"
}

resource "aws_s3_bucket" "tfstate" {
  bucket = "ledger-tfstate-367907527985" # names are global across ALL AWS accounts → add account id

  lifecycle {
    prevent_destroy = true # terraform refuses to destroy this resource
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
