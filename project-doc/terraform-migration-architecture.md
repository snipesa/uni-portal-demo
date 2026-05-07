# University Assignment Portal - Terraform Migration Architecture

## Purpose

This document defines the target Terraform structure for migrating the existing
University Assignment Portal from CloudFormation to Terraform.

The migration goal is application-resource parity first. Deployment plumbing
uses manually provided operations resources so Terraform does not mix
application uploads with infrastructure state and build artifacts.

## Target Repository Shape

```text
uni-portal-terraform-workspace/
├── AGENTS.md
├── Development.md
├── reference-materials/
└── uni-portal-terraform/
    ├── README.md
    ├── frontend-website/
    ├── project-doc/
    ├── src/
    └── infrastructure/
        ├── terraform/
        │   ├── modules/
        │   │   ├── amplify/
        │   │   ├── cognito/
        │   │   ├── dynamodb/
        │   │   ├── http-api/
        │   │   ├── rest-api-lambda/
        │   │   └── upload-bucket/
        │   └── root/
        │       ├── backend.tf
        │       ├── backend.hcl.example
        │       ├── main.tf
        │       ├── providers.tf
        │       ├── variables.tf
        │       ├── outputs.tf
        │       └── terraform.tfvars.example
        └── scripts/
            ├── package-lambda.sh
            ├── deploy-infra.sh
            └── deploy-frontend.sh
```

## Terraform Design

Use reusable modules for service-level organization and one Terraform root for
the single test deployment.

The root module should default `environment = "prod"` so resource names keep the
same pattern as the CloudFormation project:

```text
${project_name}-${environment}-<resource-purpose>
```

## State Strategy

Use a manually provided S3 bucket for Terraform remote state and a manually
provided DynamoDB table for Terraform state locking.

Do not create the operations bucket, lock table, or KMS key as part of the app
Terraform root.

Terraform backend configuration cannot use normal Terraform variables from
`variables.tf`. Use partial backend configuration:

```hcl
terraform {
  backend "s3" {}
}
```

Commit `backend.hcl.example` for visibility and keep the real `backend.hcl`
local. The deploy script should run `terraform init -backend-config=backend.hcl`.

The backend file should contain:

- operations bucket name
- Terraform state key, for example `terraform-state/uni-portal/prod.tfstate`
- region
- DynamoDB lock table name

Runtime and artifact values that are not backend settings should live in local
`terraform.tfvars`, using `terraform.tfvars.example` as the visible template.

## Resource Replication Rules

Terraform should create the same application resources CloudFormation creates:

- Cognito user pool, domain, app client, and groups
- S3 upload bucket and policy
- DynamoDB main table and GSIs
- Lambda execution role, policies, log group, and function
- API Gateway HTTP API, authorizer, integration, routes, stage, and permission
- Amplify app, branch, service role, rewrite rule, and optional WAF association

Terraform should not create resources that CloudFormation does not currently
create:

- no operations/artifacts bucket
- no Terraform lock table
- no Secrets Manager secrets
- no customer-managed KMS keys
- no CloudFront distribution
- no placeholder IAM or CloudFront resources

## S3 Replication Rule

Terraform creates one application S3 bucket: the upload bucket.

That bucket has versioning enabled, so Terraform should also enable versioning
on the upload bucket. The Terraform version should treat this bucket as the
application bucket for student upload objects under `submissions/`.

Lambda deployment zips, frontend Amplify zips, and Terraform state should live
in the manually provided operations bucket under separate prefixes:

- `terraform-state/`
- `lambda-artifacts/`
- `frontend-builds/`

## Deployment Flow

Terraform scripts should replace CloudFormation output lookups with
`terraform output`.

The frontend script should:

1. Generate `frontend-website/config.js` from Terraform outputs.
2. Zip `frontend-website/`.
3. Upload the zip to `s3://<operations-bucket>/<frontend-artifact-prefix>/latest.zip`.
4. Start an Amplify deployment from that S3 source URL.
5. Remove generated `config.js`.
