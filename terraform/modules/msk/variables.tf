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

variable "kafka_version" {
  type    = string
  default = "3.5.1"
}

variable "instance_type" {
  type    = string
  default = "kafka.m5.large"
}

variable "number_of_broker_nodes" {
  type    = number
  default = 3
}

variable "allowed_cidr_blocks" {
  type = list(string)
}
