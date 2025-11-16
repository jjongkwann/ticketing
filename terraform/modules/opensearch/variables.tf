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

variable "instance_type" {
  type    = string
  default = "r6g.large.search"
}

variable "instance_count" {
  type    = number
  default = 3
}

variable "opensearch_version" {
  type    = string
  default = "2.9"
}

variable "allowed_cidr_blocks" {
  type = list(string)
}
