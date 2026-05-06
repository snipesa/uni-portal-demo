# Story 4 - S3 Upload Bucket Parity

| Field | Value |
|---|---|
| Epic | Storage |
| Status | Not Started |
| Target Module | `modules/upload-bucket` |
| Dependencies | Story 2 |

## Goal

Recreate the current application upload bucket behavior in Terraform without
using that bucket for Terraform state or deployment artifacts.

## Existing CloudFormation Behavior

The current CloudFormation project creates one S3 bucket:

- Upload bucket: `${ProjectName}-${Environment}-upload-bucket`

The bucket currently has:

- public access blocked
- bucket-owner-enforced ownership
- AES256 server-side encryption
- versioning enabled
- CORS allowing `PUT`, `GET`, and `HEAD`
- lifecycle rule for noncurrent `submissions/` versions
- deny-insecure-transport bucket policy
- Amplify read access for `frontend-builds/*` in the CloudFormation version

## Implementation Tasks

- Create only the upload bucket.
- Preserve versioning because the CloudFormation bucket has versioning enabled.
- Preserve AES256 encryption without creating a KMS key.
- Preserve CORS behavior from CloudFormation.
- Preserve lifecycle behavior from CloudFormation.
- Preserve deny-insecure-transport bucket policy behavior from CloudFormation.
- Do not add Amplify artifact-read policy to the application upload bucket,
  because frontend artifacts move to the manually provided operations bucket.
- Do not store Lambda zips, frontend zips, or Terraform state in this bucket.

## Acceptance Criteria

- Terraform creates no operations/artifacts bucket.
- Terraform creates no customer-managed KMS key.
- The upload bucket output exposes bucket name and ARN.
- The upload bucket is reserved for application uploads.
