# Story 9 - Amplify Hosting Module

| Field | Value |
|---|---|
| Epic | Frontend Delivery |
| Status | Not Started |
| Target Module | `modules/amplify` |
| Dependencies | Story 4 |

## Goal

Recreate Amplify Hosting in Terraform for manual S3-source deployments.

## Resources

- Amplify app
- Amplify branch per environment
- Amplify service role
- Optional WAF association
- Optional custom domain placeholder

## Implementation Tasks

- Create Amplify app and branch.
- Keep auto build disabled for manual artifact deploys.
- Allow Amplify to read frontend artifacts from the manually provided operations
  bucket under the frontend artifact prefix.
- Keep SPA rewrite rule for `/admin` and hash routes.
- Parameterize WAF ARN and make association optional.
- Output Amplify app ID and default domain URL.

## Acceptance Criteria

- Amplify branch is deployable from an S3 source artifact.
- The module does not hard-code account-specific WAF ARNs.
- Frontend URL output is available for Cognito callback configuration.
- Terraform does not create the frontend artifact bucket.

## Notes

Custom domain can remain deferred unless explicitly required for the migration.
