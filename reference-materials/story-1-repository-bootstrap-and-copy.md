# Story 1 - Repository Bootstrap and Copy Unchanged Files

| Field | Value |
|---|---|
| Epic | Migration Foundation |
| Status | Completed |
| Source Project | `../uni-portal` |
| Target Project | `../uni-portal-terraform` |
| Dependencies | None |

## Goal

Create the Terraform migration repository as an independent workspace and copy
the files that should not change during the IaC migration.

## Scope

Copy unchanged application and documentation assets from `../uni-portal`:

- `src/lambda/rest-api/`
- `frontend-website/`
- selected `project-doc/` files that still describe product behavior
- root documentation that remains useful after wording updates

Do not copy CloudFormation implementation files as-is into the final Terraform
structure. Their behavior should be translated through later Terraform module
stories.

## Implementation Tasks

- Create the target repository structure.
- Add Terraform-specific `.gitignore` entries:
  - `.terraform/`
  - `.terraform.lock.hcl` if the team does not want to pin provider locks
  - `*.tfstate`
  - `*.tfstate.backup`
  - `*.tfplan`
  - generated zip files
  - generated frontend `config.js`
- Copy Lambda source without `__pycache__` and `.pyc` files.
- Copy `frontend-website/index.html` without generated `config.js`.
- Copy product docs that remain valid.
- Add Terraform-specific `README.md`, `AGENTS.md`, and `Development.md`.

## Acceptance Criteria

- The CloudFormation repository remains unchanged.
- The Terraform repository has the same application source behavior available
  for later packaging and deployment.
- Generated files are not copied or tracked.
- The new repository has its own migration story plan.

## Notes

This story is only a workspace bootstrap. Terraform resources are implemented
in later stories.
