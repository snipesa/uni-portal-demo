# Story 10 - Terraform Outputs and Frontend Deploy Scripts

| Field | Value |
|---|---|
| Epic | Deployment Tooling |
| Status | Not Started |
| Target Scripts | `infrastructure/scripts/deploy-frontend.sh`, `infrastructure/scripts/deploy-infra.sh` |
| Dependencies | Stories 5, 8, 9 |

## Goal

Replace CloudFormation-output-based deployment scripts with Terraform-output-based
scripts.

## Implementation Tasks

- Create `deploy-infra.sh` that runs Terraform commands for a selected environment:
  - `terraform init -backend-config=backend.hcl`
  - `terraform plan`
  - optional `terraform apply`
- `deploy-infra.sh` should fail with a clear message if local `backend.hcl` is
  missing.
- `deploy-infra.sh` should point users to `backend.hcl.example`.
- Create `deploy-frontend.sh` that:
  - reads values from `terraform output -json`
  - generates `frontend-website/config.js`
  - zips the frontend website
  - uploads the artifact to the manually provided operations bucket under the
    frontend artifact prefix
  - starts an Amplify deployment
  - removes generated `config.js`
- Required Terraform outputs:
  - `aws_region`
  - `cognito_client_id`
  - `cognito_auth_domain`
  - `frontend_callback_url`
  - `http_api_url`
  - `amplify_app_id`
  - `amplify_branch_name`
  - `operations_bucket_name`
  - `frontend_artifact_prefix`

## Acceptance Criteria

- No script calls `aws cloudformation describe-stacks`.
- Infrastructure deploy uses `backend.hcl` for backend values.
- Frontend config values come from Terraform outputs.
- Frontend zip is uploaded to the manually provided operations bucket.
- The frontend can sign in and call the Terraform-created API.

## Notes

Use `jq` for reading `terraform output -json` if shell scripts are retained.
