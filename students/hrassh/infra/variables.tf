variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "unit-converter"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "public_key" {
  description = "SSH public key for the EC2 instance"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR allowed to connect over SSH"
  type        = string
  default     = "0.0.0.0/0"
}
