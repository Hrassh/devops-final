data "aws_vpc" "default" {
  default = true
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "deploy" {
  key_name   = "${var.project_name}-deploy"
  public_key = var.public_key
}

resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg"
  description = "HTTP and SSH for ${var.project_name}"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.deploy.key_name
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true
  user_data                   = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }

  tags = {
    Name = "${var.project_name}-server"
  }

  lifecycle {
    ignore_changes = [ami, user_data]
  }
}
