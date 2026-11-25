variable "image_tag" {
  description = "Tag of the payments-ledger image in ECR to deploy (short git commit)."
  type        = string
  # No default: every plan/apply must name the exact image it deploys.
}
