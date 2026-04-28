variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome do projeto para tags"
  type        = string
  default     = "ServerlessTroubleshooter"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "prefix" {
  description = "Prefixo para nomes de recursos"
  type        = string
  default     = "troubleshooter-dev"
}

variable "log_retention_days" {
  description = "Retenção de logs no CloudWatch em dias"
  type        = number
  default     = 7
}

variable "lambda_runtime" {
  description = "Runtime das Lambdas"
  type        = string
  default     = "python3.11"
}

variable "github_repo" {
  description = "Repositório GitHub no formato owner/repo (ex: Sergio-Sena/serverless-troubleshooter)"
  type        = string
  default     = "Sergio-Sena/serverless-troubleshooter"
}

variable "domain_name" {
  description = "Domínio principal no Route 53 (ex: sstechnologies-cloud.com)"
  type        = string
  default     = "sstechnologies-cloud.com"
}
