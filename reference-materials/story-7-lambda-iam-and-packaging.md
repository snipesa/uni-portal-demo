# Story 7 - Lambda, IAM, and Packaging

| Field | Value |
|---|---|
| Epic | API Runtime |
| Status | Not Started |
| Target Module | `modules/rest-api-lambda` |
| Target Scripts | `infrastructure/scripts/package-lambda.sh` |
| Dependencies | Stories 4, 5, 6 |

## Goal

Package and deploy the existing Python 3.12 REST API Lambda with Terraform.

## Resources

- Lambda execution role
- Lambda IAM policies
- CloudWatch log group
- Lambda function
- Lambda package zip

## Implementation Tasks

- Copy the current Lambda source from `src/lambda/rest-api`.
- Preserve handler: `lambda_function.lambda_handler`.
- Preserve runtime: `python3.12`.
- Preserve environment variables:
  - `UPLOAD_BUCKET_NAME`
  - `MAIN_TABLE_NAME`
  - `USER_POOL_ID`
  - `PRESIGNED_URL_EXPIRY_SECONDS`
  - `ENVIRONMENT`
  - `LOG_LEVEL`
- Replace the CloudFormation SSM pointer flow with an artifact strategy that
  uploads Lambda zips to the manually provided operations bucket under the
  Lambda artifact prefix.
- Pass Lambda artifact bucket/key values into Terraform.
- Output Lambda ARN and function name.

## Acceptance Criteria

- Terraform deploys the Lambda from the manually provided operations bucket.
- Lambda can read/write DynamoDB, generate S3 presigned URLs, and manage Cognito
  groups as currently implemented.
- Deployment does not include `__pycache__`, `.pyc`, or local build artifacts.
- Terraform does not create the Lambda artifact bucket.

## Future Improvement

Consider splitting admin Cognito group management into a separate Lambda/role
after parity is achieved.
