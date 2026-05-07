# Story 7 - Lambda, IAM, and Packaging

| Field | Value |
|---|---|
| Epic | API Runtime |
| Status | Not Started |
| Target Module | `modules/rest-api-lambda` |
| Target Scripts | `infrastructure/scripts/package-lambda.sh` |
| Dependencies | Stories 4, 5, 6 |

## Goal

Package the existing Python 3.12 REST API Lambda with a script and deploy it
with Terraform using the latest artifact key stored in SSM Parameter Store.

## Resources

- Lambda execution role
- Lambda IAM policies
- CloudWatch log group
- Lambda function
- Lambda package script
- SSM parameter lookup for the Lambda artifact key

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
- Create `infrastructure/scripts/package-lambda.sh` using the same packaging
  approach as `../uni-portal/infrastructure/package-lambda.sh`.
- Package the Lambda source into a timestamped zip named
  `<YYYYMMDD-HHMMSS>-rest-api.zip`.
- Install third-party dependencies from `requirements.txt` only when real
  requirements exist.
- Exclude `__pycache__`, `.pyc`, dependency metadata, and local build artifacts
  from the deployment zip.
- Upload Lambda zips to the manually provided operations bucket under the
  configured Lambda artifact prefix.
- Update the SSM parameter
  `/cytora-uni-portal/${ENVIRONMENT}/rest-lambda-zip` with the uploaded S3
  object key.
- Read that SSM parameter from Terraform and use its value as the Lambda
  deployment S3 key.
- Output Lambda ARN and function name.

## Acceptance Criteria

- The package script uploads the Lambda zip to the manually provided operations
  bucket.
- The package script creates or overwrites
  `/cytora-uni-portal/${ENVIRONMENT}/rest-lambda-zip` with the latest Lambda
  artifact S3 key.
- Terraform deploys the Lambda from the manually provided operations bucket
  using the S3 key read from SSM Parameter Store.
- Lambda can read/write DynamoDB, generate S3 presigned URLs, and manage Cognito
  groups as currently implemented.
- Deployment does not include `__pycache__`, `.pyc`, or local build artifacts.
- Terraform does not create the Lambda artifact bucket.
- The package script must run before the first Terraform apply for this Lambda
  so the SSM parameter exists.

## Migration Notes

- This Terraform migration intentionally keeps the Lambda artifact pointer flow:
  package script writes the S3 key to SSM, Terraform reads that SSM value.
- The new SSM parameter path is
  `/cytora-uni-portal/${ENVIRONMENT}/rest-lambda-zip`.
- The new path uses `rest-lambda-zip`, correcting the previous
  `rest-lamba-zip` spelling used in the CloudFormation project.

## Future Improvement

Consider splitting admin Cognito group management into a separate Lambda/role
after parity is achieved.
