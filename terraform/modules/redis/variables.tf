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

variable "node_type" {
  type    = string
  default = "cache.r6g.large"
}

variable "num_cache_clusters" {
  type    = number
  default = 3
}

variable "allowed_cidr_blocks" {
  type = list(string)
}
