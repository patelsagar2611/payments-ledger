terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "ledger-tfstate-367907527985"
    key          = "payments-ledger/terraform.tfstate" # path of the state object inside the bucket
    region       = "ap-southeast-2"
    profile      = "ledger-login"
    use_lockfile = true # a .tflock object stops two applies running at once
  }
}

provider "aws" {
  region  = "ap-southeast-2"
  profile = "ledger-login"

  default_tags { # added to every resource this provider creates
    tags = {
      Project   = "payments-ledger"
      ManagedBy = "terraform"
    }
  }
}
