# Story 6 - DynamoDB Module

| Field | Value |
|---|---|
| Epic | Database |
| Status | Completed |
| Target Module | `modules/dynamodb` |
| Dependencies | Story 2 |

## Goal

Recreate the DynamoDB single-table model in Terraform.

## Resources

- Main DynamoDB table
- Primary key:
  - `PK`
  - `SK`
- GSIs:
  - `GSI1-StudentSubmissions`
  - `GSI2-CourseSubmissions`
  - `GSI3-StudentEnrollments`
  - `GSI4-StaffCourses`

## Implementation Tasks

- Use PAY_PER_REQUEST billing mode.
- Preserve table and index names expected by application code.
- Enable server-side encryption.
- Preserve point-in-time recovery as disabled.
- Preserve the current destroy-friendly behavior for the test migration.
- Output table name and ARN.

## Acceptance Criteria

- Existing Lambda code can use the Terraform-created table without code changes.
- All query patterns from the current application are supported.
- Terraform does not create a customer-managed KMS key.

## Notes

Terraform can create all GSIs during initial table creation. If migrating an
existing live table later, plan index changes carefully.
