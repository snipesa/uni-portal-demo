# University Assignment Portal - Terraform Migration Stories

## Overview

This document is the master story list for migrating the existing University
Assignment Portal from CloudFormation to Terraform.

The source project remains at `../uni-portal`. This repository is the new
Terraform migration workspace and should preserve the current application
behavior while replacing the infrastructure layer.

Technical migration architecture is documented in
[project-doc/terraform-migration-architecture.md](project-doc/terraform-migration-architecture.md).

> **Migration Notes**
> - The existing CloudFormation project must remain untouched unless explicitly requested.
> - This migration should use one default deployment environment only.
> - Terraform should replicate the current application resources before adding improvements.
> - Terraform should create only the application resources; operations resources are provided manually.
> - A manually created operations S3 bucket should be used for Terraform state, Lambda zips, and frontend zips under separate prefixes.
> - A manually created DynamoDB table should be used for Terraform state locking.
> - Do not add customer-managed KMS keys or Secrets Manager resources.
> - Keep S3 upload bucket versioning because the CloudFormation upload bucket has versioning enabled.
> - Lambda functions remain Python 3.12.
> - Frontend runtime config must be generated from `terraform output`, not CloudFormation outputs.

---

## Repository File Structure Convention

```text
uni-portal-terraform/
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── amplify/
│   │   │   ├── cognito/
│   │   │   ├── dynamodb/
│   │   │   ├── http-api/
│   │   │   ├── rest-api-lambda/
│   │   │   └── upload-bucket/
│   │   └── root/
│   │       ├── backend.tf
│   │       ├── backend.hcl.example
│   │       ├── main.tf
│   │       ├── providers.tf
│   │       ├── variables.tf
│   │       ├── outputs.tf
│   │       └── terraform.tfvars.example
│   └── scripts/
│       ├── package-lambda.sh
│       ├── deploy-infra.sh
│       └── deploy-frontend.sh
├── frontend-website/
├── src/
├── project-doc/
├── reference-materials/
├── Development.md
├── README.md
└── AGENTS.md
```

---

## Existing CloudFormation Resource Parity

Terraform should recreate the same resource nature:

- Cognito user pool, Hosted UI domain, app client, and `Admin`, `Staff`, `Students` groups
- One S3 application upload bucket with encryption, versioning, CORS, lifecycle, and bucket policy
- DynamoDB main table with the same primary key and four GSIs
- REST API Lambda, IAM role/policies, and log group
- API Gateway HTTP API, JWT authorizer, Lambda integration, routes, stage, and invoke permission
- Amplify app, branch, service role, SPA rewrite rule, and optional WAF association

Terraform should not create:

- the operations/artifacts S3 bucket
- the Terraform state-lock DynamoDB table
- a customer-managed KMS key
- Secrets Manager secrets
- CloudFront resources
- placeholder IAM or CloudFront resources

Manually provided infrastructure should include:

- operations S3 bucket name
- Terraform state key prefix
- Lambda artifact prefix
- frontend artifact prefix
- Terraform lock table name

---

## Recommended Build Order

| Milestone | Scope | Main files/folders | Story |
|---|---|---|---|
| 0 | Manual operations prerequisites | AWS console/CLI, local config files | [Story 0](reference-materials/story-0-manual-operations-prerequisites.md) |
| 1 | Migration workspace bootstrap | repo root, copied app files | [Story 1](reference-materials/story-1-repository-bootstrap-and-copy.md) |
| 2 | Terraform root and module skeleton | `infrastructure/terraform/` | [Story 2](reference-materials/story-2-terraform-structure-and-state.md) |
| 3 | Remote state and external artifact inputs | `infrastructure/terraform/root/` | [Story 3](reference-materials/story-3-single-environment-state.md) |
| 4 | S3 upload bucket parity | `modules/upload-bucket` | [Story 4](reference-materials/story-4-s3-upload-bucket-parity.md) |
| 5 | Cognito Terraform module | `modules/cognito` | [Story 5](reference-materials/story-5-cognito-module.md) |
| 6 | DynamoDB Terraform module | `modules/dynamodb` | [Story 6](reference-materials/story-6-dynamodb-module.md) |
| 7 | Lambda, IAM, and packaging | `modules/rest-api-lambda`, scripts | [Story 7](reference-materials/story-7-lambda-iam-and-packaging.md) |
| 8 | HTTP API Terraform module | `modules/http-api` | [Story 8](reference-materials/story-8-http-api-module.md) |
| 9 | Amplify Hosting Terraform module | `modules/amplify` | [Story 9](reference-materials/story-9-amplify-hosting-module.md) |
| 10 | Frontend config and deploy scripts | `infrastructure/scripts`, `frontend-website` | [Story 10](reference-materials/story-10-terraform-outputs-and-frontend-deploy.md) |
| 11 | Observability parity | Lambda/API module settings | [Story 11](reference-materials/story-11-observability-parity.md) |
| 12 | Parity validation | docs, scripts, validation checklist | [Story 12](reference-materials/story-12-parity-validation-and-cutover.md) |

---

## Milestone Checklist

### Milestone 0 - Manual Operations Prerequisites
- Manually create or identify the operations S3 bucket
- Manually create or identify the Terraform lock DynamoDB table
- Create local `backend.hcl` from `backend.hcl.example`
- Create local `terraform.tfvars` from `terraform.tfvars.example`
- Provide values for artifact prefixes, callback URL, and Cognito domain suffix

### Milestone 1 - Migration Workspace Bootstrap
- Copy unchanged source application files from `../uni-portal`
- Keep this repository independent from the CloudFormation repository
- Add Terraform-focused `.gitignore`, README, and instructions

### Milestone 2 - Terraform Structure
- Create module folders and a single Terraform root
- Define shared naming, tagging, provider, and variable conventions
- Default the single deployment environment variable to `prod`

### Milestone 3 - Single Environment State
- Use a manually provided S3 bucket for Terraform remote state
- Use a manually provided DynamoDB table for Terraform locking
- Store backend values in local `backend.hcl`
- Let `deploy-infra.sh` pass `backend.hcl` during `terraform init`
- Use prefixes in the same manually provided bucket for Lambda and frontend artifacts
- Do not create the operations bucket or lock table from the application Terraform root

### Milestone 4 - S3 Upload Bucket
- Recreate only the CloudFormation upload bucket
- Preserve AES256 encryption, versioning, CORS, lifecycle, and bucket policy
- Treat this bucket as the application upload bucket, not the deployment artifact bucket

### Milestone 5 - Cognito
- Recreate user pool, Hosted UI domain, app client, and groups
- Preserve callback/logout URL behavior through variables

### Milestone 6 - DynamoDB
- Recreate the single table and GSIs
- Preserve `PointInTimeRecoveryEnabled: false`
- Preserve DynamoDB server-side encryption without creating a KMS key

### Milestone 7 - Lambda and IAM
- Package Python 3.12 Lambda
- Keep Lambda env vars compatible with existing application code
- Upload Lambda zips to the manually provided operations bucket under the Lambda artifact prefix

### Milestone 8 - HTTP API
- Recreate HTTP API, JWT authorizer, routes, integration, and invoke permission
- Export API URL for frontend config

### Milestone 9 - Amplify
- Recreate Amplify app and branch
- Wire Amplify deployment artifacts to the manually provided operations bucket under the frontend artifact prefix
- Keep WAF association optional, matching the current CloudFormation behavior

### Milestone 10 - Frontend Deploy
- Generate `frontend-website/config.js` from `terraform output`
- Upload frontend artifact to the manually provided operations bucket under the frontend artifact prefix
- Trigger Amplify deployment

### Milestone 11 - Observability Parity
- Preserve explicit Lambda log group with 14-day retention
- Preserve API Gateway detailed metrics
- Do not add alarms/dashboards until after parity is proven

### Milestone 12 - Validation
- Validate Terraform plan/apply
- Validate end-to-end app parity
- Produce a cutover readiness checklist
