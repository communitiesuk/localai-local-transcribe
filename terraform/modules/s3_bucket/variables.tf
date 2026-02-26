variable "bucket_name" {
  type        = string
  description = "The name of the bucket to create"
}

variable "access_log_bucket_name" {
  type        = string
  description = "The name of the accompanying log bucket"
}

variable "kms_key_arn" {
  type        = string
  default     = null
  description = "Optional. KMS key to encrypt bucket and access logs bucket."
}

variable "force_destroy" {
  description = "Allow the buckets to be destroyed by Terraform even if they are not empty."
  type        = bool
  default     = false
}

variable "noncurrent_version_expiration_days" {
  type        = number
  description = "Set to null to skip creating a bucket lifecycle configuration"
  default     = 180
}

variable "access_s3_log_expiration_days" {
  type        = number
  description = "The number of days to retain s3 access logs"
}

variable "policy" {
  description = "optional policy json to append to default bucket enforce ssl policy"
  type        = string
  default     = null
}

variable "object_lock_enabled" {
  description = "Whether the bucket is configured to allow AWS Object Lock"
  type        = bool
  default     = false
}