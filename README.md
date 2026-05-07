# University Assignment Portal (Terraform)

This repository contains a self-implemented University Assignment Portal built with Terraform-managed AWS infrastructure and Python 3.12 Lambda services.

## High-Level Implementation

- Infrastructure as Code with Terraform
- Role-aware authentication and authorization with Cognito
- REST API backend with API Gateway + Lambda
- Assignment file workflows with S3 presigned URLs
- Submission metadata and workflow state in DynamoDB
- Static frontend website deployment

## Deployment Steps

```bash
cd infrastructure/terraform/root
cp backend.hcl.example backend.hcl
cp terraform.tfvars.example terraform.tfvars
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
terraform apply
```

## Documentation

- [Project Documentation Index](./project-doc/README.md)
