# Story 5 - Cognito Module

| Field | Value |
|---|---|
| Epic | Identity and Access |
| Status | Completed |
| Target Module | `modules/cognito` |
| Dependencies | Story 2 |

## Goal

Recreate the Cognito user pool, Hosted UI domain, app client, and role groups in
Terraform.

## Resources

- Cognito User Pool
- Cognito User Pool Domain
- Cognito User Pool Client
- Cognito groups:
  - `Admin`
  - `Staff`
  - `Students`

## Implementation Tasks

- Preserve email-based username behavior.
- Preserve app client code flow for the SPA.
- Parameterize callback and logout URLs.
- Preserve group precedence.
- Preserve the current MFA(disabled for now) and self-registration behavior unless explicitly changed later.
- Output:
  - user pool ID
  - user pool ARN
  - app client ID
  - Hosted UI domain prefix/auth domain

## Acceptance Criteria

- The frontend can run the PKCE sign-in flow using Terraform-created Cognito values.
- API Gateway can use the Terraform-created user pool as JWT issuer.
- Admin, Staff, and Students groups exist.

## Parity Notes

The CloudFormation template currently has MFA off and `AllowAdminCreateUserOnly`
set to false. The Terraform migration should match that behavior for parity.
