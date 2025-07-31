terraform {
  required_providers {
    synthetics = {
      source  = "splunk/synthetics"
      version = "2.0.2"
    }
  }
}

provider "synthetics" {
  product = "observability"
  realm   = var.realm
  apikey  = var.access_token
}

variable "access_token" {
  description = "Splunk Access Token"
}

variable "realm" {
  description = "Splunk Realm"
  default     = "us1"
}
