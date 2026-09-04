data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  # arm64 to match the Graviton (t4g) instance type.
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-*-arm64"]
  }
}

resource "aws_instance" "bastion" {
  count = length(var.bastion_subnet_ids)
  ami   = data.aws_ami.amazon_linux_2023.id
  # t4g (Graviton) rather than t2: t2 is previous generation and is prone to
  # InsufficientInstanceCapacity in some eu-west-2 availability zones. Must stay
  # in sync with the AMI architecture above.
  instance_type          = "t4g.micro"
  subnet_id              = var.bastion_subnet_ids[count.index]
  vpc_security_group_ids = [aws_security_group.bastion.id]
  iam_instance_profile   = aws_iam_instance_profile.ssm_bastion.name

  root_block_device {
    encrypted = true
  }
  metadata_options {
    http_tokens = "required"
  }
  tags = {
    Name = "${var.environment_name}-bastion-${count.index + 1}"
  }
}