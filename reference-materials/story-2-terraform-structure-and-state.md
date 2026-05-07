# Story 2 - Terraform Structure and State Strategy

| Field | Value |
|---|---|
| Epic | Terraform Foundation |
| Status | Completed |
| Target Folders | `infrastructure/terraform/` |
| Dependencies | Story 1 |

## Goal

Create the Terraform folder layout, module conventions, provider setup, and one
single deployment root.

## Proposed Structure

```text
infrastructure/terraform/
├── modules/
│   ├── amplify/
│   ├── cognito/
│   ├── dynamodb/
│   ├── http-api/
│   ├── rest-api-lambda/
│   └── upload-bucket/
└── root/
    ├── backend.tf
    ├── backend.hcl.example
    ├── terraform.tfvars.example
    ├── main.tf
    ├── providers.tf
    ├── variables.tf
    └── outputs.tf
```

## Implementation Tasks

- Add provider version constraints.
- Add `backend.tf` with an empty S3 backend block.
- Add `backend.hcl.example` showing the required manually provided backend values.
- Add `terraform.tfvars.example` showing manually provided runtime/artifact values.
- Define common variables:
  - `project_name`
  - `environment` with default value `prod`
  - `aws_region`
  - `operations_bucket_name`
  - `lambda_artifact_prefix`
  - `frontend_artifact_prefix`
- Create module skeletons with `main.tf`, `variables.tf`, and `outputs.tf`.
- Create one Terraform root at `infrastructure/terraform/root`.
- Define naming convention: `${project_name}-${environment}-<resource-purpose>`.
- Define output names that later scripts will consume.

## Acceptance Criteria

- `terraform init` works in the single Terraform root.
- `terraform init -backend-config=backend.hcl` is the documented path.
- Real `backend.hcl` and `terraform.tfvars` files are local-only.
- Module boundaries map clearly to service ownership.
- The root can wire module outputs without using CloudFormation exports.

## Design Decision

Use one root with remote state backed by manually provided operations resources.
The app Terraform root should not create the state bucket or lock table.
