# Story 3 - Single Environment Remote State

| Field | Value |
|---|---|
| Epic | Terraform Foundation |
| Status | Completed |
| Target Folder | `infrastructure/terraform/root/` |
| Dependencies | Story 2 |

## Goal

Use one Terraform deployment root, default the environment name to `prod`, and
configure remote state using manually provided operations resources.

## Scope

This story intentionally avoids creating operations resources from the app
Terraform root. The state bucket and lock table are created manually and passed
to Terraform commands.

## Implementation Tasks

- Configure one root module at `infrastructure/terraform/root/`.
- Default `environment` to `prod`.
- Configure the S3 backend with a manually provided bucket.
- Configure DynamoDB state locking with a manually provided table.
- Use a state key prefix such as `terraform-state/uni-portal/prod.tfstate`.
- Add committed `backend.hcl.example`.
- Require local `backend.hcl` for actual Terraform commands.
- Add `terraform.tfvars.example` instead of committed real tfvars.
- Document `terraform init -backend-config=backend.hcl` usage.

## Acceptance Criteria

- There is no `envs/dev` or `envs/prod` split.
- There is no Terraform-managed operations bucket.
- There is no Terraform-managed DynamoDB lock table.
- Terraform uses the manually provided bucket and table for remote state.
- `backend.hcl.example` documents required backend fields.
- `backend.hcl` is ignored by git.
- The app resource names can use `${project_name}-${environment}-...` with
  `environment = "prod"` by default.
