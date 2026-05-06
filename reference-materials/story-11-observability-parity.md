# Story 11 - Observability Parity

| Field | Value |
|---|---|
| Epic | Operations |
| Status | Not Started |
| Target Modules | `modules/rest-api-lambda`, `modules/http-api` |
| Dependencies | Stories 7 and 8 |

## Goal

Replicate the observability resources currently present in CloudFormation.

## Existing CloudFormation Behavior

- Lambda log group is explicitly managed with 14-day retention.
- API Gateway default stage has detailed metrics enabled.
- No CloudWatch dashboard is currently created.
- No CloudWatch alarms are currently created.
- X-Ray tracing is not currently enabled.

## Implementation Tasks

- Create the Lambda log group with 14-day retention.
- Enable detailed metrics on the HTTP API default stage.
- Do not add dashboards, alarms, X-Ray, or extra monitoring resources during
  the parity migration.

## Acceptance Criteria

- Terraform observability matches the current CloudFormation behavior.
- No additional monitoring resources are introduced during the parity phase.

## Future Improvement

After the Terraform migration is proven, dashboards, alarms, access logs, and
tracing can be added as a separate enhancement story.
