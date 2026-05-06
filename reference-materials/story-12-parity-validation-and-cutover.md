# Story 12 - Parity Validation and Cutover Readiness

| Field | Value |
|---|---|
| Epic | Migration Validation |
| Status | Not Started |
| Dependencies | Stories 1-11 |

## Goal

Verify the Terraform deployment matches the current CloudFormation application
behavior and prepare for a safe cutover.

## Validation Areas

- Terraform formatting and validation
- Module plan review
- Lambda packaging
- Cognito sign-in and group behavior
- Student upload flow
- Staff course and assignment management
- Submission review, comments, grades, and resubmission
- Admin group-management flow
- Frontend deployment through Amplify

## Implementation Tasks

- Add a parity checklist document or runbook.
- Add smoke test commands.
- Confirm all required Terraform outputs exist.
- Confirm generated frontend `config.js` is not committed.
- Confirm no CloudFormation commands remain in Terraform deployment scripts.
- Confirm source CloudFormation repository remains untouched.

## Acceptance Criteria

- A fresh single-environment Terraform deployment works end to end.
- The user can deploy infra and frontend using the new scripts.
- The team has a documented cutover checklist before moving traffic or users.

## Notes

This story does not decommission CloudFormation resources. Cleanup should be a
separate, explicit task after Terraform parity is proven.
