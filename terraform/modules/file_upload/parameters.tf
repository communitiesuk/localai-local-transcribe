resource "aws_ssm_parameter" "quarantine_bucket" {
  name  = "${var.environment_name}-prsdb-quarantine-bucket"
  type  = "String"
  value = module.quarantine_bucket.bucket
}

resource "aws_ssm_parameter" "uploaded_file_bucket" {
  name  = "${var.environment_name}-prsdb-uploaded-files"
  type  = "String"
  value = module.uploaded_files_bucket.bucket
}
