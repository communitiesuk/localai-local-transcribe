variable "image_name" {
  description = "name of the docker image to deploy"
  type        = string
  default     = "nginx:alpine"
}

variable "file_upload_buckets_created" {
  description = "Flag to indicate if the file upload buckets have been created"
  type        = bool
  default     = true
}