# Terraform skeleton — Bedrock Knowledge Base for the managed RAG arm.
# Skeleton, not turnkey: the vector store (OpenSearch Serverless collection + its
# encryption/network/data-access policies) is verbose and best created once via the
# console or a dedicated module. This file shows the core wiring: S3 data source,
# IAM role, the Knowledge Base, and the S3 data source binding.
#
#   terraform init && terraform apply
#   terraform output knowledge_base_id     # -> export KB_ID for query.py

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { default = "us-east-1" }
variable "collection_arn" {
  description = "ARN of a pre-created OpenSearch Serverless collection (or swap for Aurora/S3 Vectors — see note below)."
  type        = string
}

# 1. S3 bucket holding the source documents the KB will ingest.
resource "aws_s3_bucket" "docs" {
  bucket = "regintel-rag-docs-${data.aws_caller_identity.me.account_id}"
}

data "aws_caller_identity" "me" {}

# 2. IAM role Bedrock assumes to read S3, embed with Titan, and write to the vector store.
resource "aws_iam_role" "kb" {
  name = "bedrock-kb-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "kb" {
  role = aws_iam_role.kb.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:ListBucket"], Resource = [aws_s3_bucket.docs.arn, "${aws_s3_bucket.docs.arn}/*"] },
      { Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0" },
      { Effect = "Allow", Action = ["aoss:APIAccessAll"], Resource = var.collection_arn },
    ]
  })
}

# 3. The Knowledge Base — Titan embeddings + the OpenSearch Serverless vector store.
resource "aws_bedrockagent_knowledge_base" "this" {
  name     = "regintel-managed-rag"
  role_arn = aws_iam_role.kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }

  # COST NOTE: OpenSearch Serverless bills a ~2-OCU (~$300+/mo) minimum, always-on.
  # For low volume, swap this block for an Aurora PostgreSQL (pgvector) or S3 Vectors
  # storage_configuration instead — same KB, far lower floor.
  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = var.collection_arn
      vector_index_name = "regintel-index"
      field_mapping {
        vector_field   = "embedding"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
  }
}

# 4. Bind the S3 bucket as a data source (then sync/ingest from the console or API).
resource "aws_bedrockagent_data_source" "s3" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.this.id
  name              = "s3-docs"
  data_source_configuration {
    type = "S3"
    s3_configuration { bucket_arn = aws_s3_bucket.docs.arn }
  }
}

output "knowledge_base_id" { value = aws_bedrockagent_knowledge_base.this.id }
output "docs_bucket" { value = aws_s3_bucket.docs.bucket }
