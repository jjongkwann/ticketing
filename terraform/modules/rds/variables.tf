variable "environment" {
  type = string
}

variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "instance_class" {
  type    = string
  default = "db.t3.large"
}

variable "allocated_storage" {
  type    = number
  default = 100
}

variable "multi_az" {
  type    = bool
  default = true
}

variable "allowed_cidr_blocks" {
  type = list(string)
}
