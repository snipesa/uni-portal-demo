# Story 8 - HTTP API Module

| Field | Value |
|---|---|
| Epic | API Layer |
| Status | Not Started |
| Target Module | `modules/http-api` |
| Dependencies | Stories 5, 7 |

## Goal

Recreate API Gateway HTTP API with Cognito JWT authorization and Lambda proxy
integration.

## Resources

- API Gateway HTTP API
- JWT authorizer
- Lambda proxy integration
- Routes for uploads, submissions, comments, grades, downloads, courses, and admin
- Default stage
- Lambda invoke permission

## Implementation Tasks

- Translate current route definitions from CloudFormation to Terraform.
- Use Cognito user pool issuer and app client ID from module outputs.
- Use Lambda ARN from the Lambda module.
- Export HTTP API URL for frontend config generation.
- Keep CORS environment-aware.

## Acceptance Criteria

- Every current route exists in Terraform.
- All protected routes require Cognito JWT auth.
- The frontend can call the Terraform-created API URL.

## Notes

The application route dispatcher in Lambda should not need to change for this
story.
