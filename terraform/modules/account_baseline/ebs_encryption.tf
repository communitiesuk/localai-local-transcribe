resource "aws_ebs_encryption_by_default" "default" {
  enabled = true
}

resource "aws_ebs_encryption_by_default" "us_east_1" {
  provider = aws.us-east-1
  enabled  = true
}
