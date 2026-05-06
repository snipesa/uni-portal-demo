# Story 0 - Manual Operations Prerequisites

| Field | Value |
|---|---|
| Epic | Migration Foundation |
| Status | Not Started |
| Owner | Human operator |
| Target Files | `infrastructure/terraform/root/backend.hcl`, `infrastructure/terraform/root/terraform.tfvars` |
| Dependencies | None |

## Goal

Prepare the manually managed operations resources and local values needed before
the Terraform migration can run.

Terraform should not create these operations resources. They are created or
identified outside the application Terraform root and then referenced by local
configuration files.

## Manual AWS Resources

Create or identify one operations S3 bucket.

Purpose:

- Terraform remote state
- Lambda deployment zips
- Amplify frontend deployment zips

Recommended prefixes:

- `terraform-state/uni-portal/prod.tfstate`
- `lambda-artifacts/uni-portal/`
- `frontend-builds/uni-portal/`

Create or identify one DynamoDB lock table.

Purpose:

- Terraform state locking only

Required key:

- Partition key: `LockID`
- Type: string

## Local Backend File

Create this file from the committed example:

```text
infrastructure/terraform/root/backend.hcl
```

Example shape:

```hcl
bucket         = "your-operations-bucket-name"
key            = "terraform-state/uni-portal/prod.tfstate"
region         = "us-east-1"
dynamodb_table = "your-terraform-lock-table-name"
encrypt        = true
```

This file is passed during the deploy stage by `deploy-infra.sh`:

```bash
terraform init -backend-config=backend.hcl
```

## Local Terraform Values

Create this file from the committed example:

```text
infrastructure/terraform/root/terraform.tfvars
```

Values to provide:

- `project_name`
- `environment`
- `aws_region`
- `operations_bucket_name`
- `lambda_artifact_prefix`
- `frontend_artifact_prefix`
- `frontend_callback_url`
- `cognito_domain_suffix`
- optional `amplify_web_acl_arn`

## Acceptance Criteria

- Operations S3 bucket exists before Terraform init.
- Terraform lock table exists before Terraform init.
- Local `backend.hcl` exists and is not committed.
- Local `terraform.tfvars` exists and is not committed.
- Application Terraform root does not create the operations bucket or lock table.
