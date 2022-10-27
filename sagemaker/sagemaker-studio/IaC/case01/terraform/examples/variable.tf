variable "project_name" {
  description = "Project name"
  type        = string
  default     = "chococones-tarraform"

  validation {
    condition     = length(regexall("sagemaker|Sagemaker|SageMaker", var.project_name)) <= 0
    error_message = "Do not specify these strings in your project name. Sagemaker, SageMaker, sagemaker"
  }
}

variable "environment" {
  description = "environment"
  type        = string
  default     = "dev"

  validation {
    condition     = length(regexall("sagemaker|Sagemaker|SageMaker", var.project_name)) <= 0
    error_message = "Do not specify these strings in your environment name. Sagemaker, SageMaker, sagemaker"
  }
}

# Userを追加する時はここに追加する
variable "user_list" {
  type    = list(string)
  default = ["tsugo", "kudo", "sagemaker"]

  validation {
    condition     = length(regexall("sagemaker|Sagemaker|SageMaker", var.project_name)) <= 0
    error_message = "Do not specify these strings in your user name. Sagemaker, SageMaker, sagemaker"
  }
}

