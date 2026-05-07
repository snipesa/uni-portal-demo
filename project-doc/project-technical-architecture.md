# University Assignment Portal - Technical Architecture and Tooling

## Purpose
This document captures the implemented tooling and architecture for the University Assignment
Submission and Grading Portal.

## High-Level Architecture

1. Edge and delivery layer serves the web application through AWS Amplify Hosting.
2. Authenticated users interact with a REST API (HTTP API) for metadata and CRUD operations.
3. Client updates are handled through standard HTTP requests.
4. File uploads happen directly from browser to S3 using short-lived presigned URLs.
5. Business logic runs in a single REST Lambda handler.
6. Metadata and grading records are stored in DynamoDB (single-table design).
7. Observability and security controls are enabled across services.

## Architecture Diagram

![University Assignment Portal Architecture](./arch-diagramv3.png)


## Tooling and Services
### Frontend and Delivery
- AWS Amplify Hosting: Managed HTTPS/CDN hosting for the current static portal page and future SPA builds.
- Amazon S3 (Frontend Deployment Artifacts): Stores zipped `frontend-builds/` artifacts used by Amplify manual deployments.
- Amazon Route 53: DNS routing (manual CNAME until custom domain is set up).

### Identity and Access
- Amazon Cognito User Pool: User sign-up/sign-in, JWT issuance, group-based roles.
- IAM: Least-privilege roles for REST Lambda and service integrations.

### API and Application Layer
- AWS API Gateway HTTP API (v2): RESTful routes with Cognito JWT authorizer, single-stage auto-deploy.
- AWS Lambda (REST API Handler): Unified Python 3.12 function with modular route files for presigned URL generation, submission CRUD, comments, grades, and downloads.

### Storage and Data
- Amazon S3 (Private Upload Bucket): Assignment files and revised versions. Browser uploads via presigned PUT URLs.
- Amazon S3 (Frontend Deployment Artifacts): Frontend zip artifacts consumed by Amplify deployments.
- Amazon DynamoDB (Single-Table Design): Submissions, versions, comments, and grades with GSIs for student and course query paths.
- S3 lifecycle to Glacier Flexible Retrieval: Archives old versions after policy threshold.
- S3 lifecycle to keep one version of deleted objects.

### Security and Encryption
- S3 SSE-S3 (AES256): Server-side encryption at rest for both buckets.
- S3 Block Public Access: Enforced on the upload bucket.
- Amplify Hosting: Managed HTTPS delivery for the website.
- Presigned upload URLs: Short expiration, scoped object key paths per user and role.

### Monitoring and Operations
- Amazon CloudWatch: Log groups for Lambda and API Gateway, metric filters, alarms, dashboards.
- API Gateway metrics: Request count, 4xx and 5xx errors, and latency.

## Why This Approach
This architecture uses managed AWS services and a single REST Lambda backend to keep operations straightforward, security controls centralized, and deployment flow predictable. It supports role-based access, direct file upload patterns, and clear ownership between infrastructure, API, and frontend runtime configuration.

## Core Technical Flows
### Authentication
1. User signs in with Cognito (React SPA uses Cognito Hosted UI or custom auth component).
2. Frontend receives JWT (`id_token` + `access_token`).
3. JWT is attached to HTTP API calls via `Authorization` header.
4. API requests use role-aware authorization based on Cognito JWT claims.

### Assignment Upload
1. Frontend calls `POST /uploads/request` with assignment metadata.
2. REST API Lambda generates a scoped presigned S3 PUT URL and creates a `PENDING` submission record in DynamoDB.
3. Browser uploads file directly to S3 using the presigned URL.
4. Frontend calls `POST /uploads/confirm`; Lambda verifies the S3 object exists via `HeadObject` and marks the submission as `SUBMITTED`.

### Review and Grading
1. Instructor calls `GET /submissions` filtered by course and term.
2. Instructor downloads a file via `GET /downloads/{submissionId}/{versionNumber}` which returns a presigned GET URL.
3. Instructor adds comments via `POST /comments` and grades via `POST /grades`.
4. Users refresh or re-query submissions to see latest comments and grades.

## Environment Strategy
- **Dev**: Core stack active, permissive CORS (`*`), lower alarm thresholds, self-registration enabled in Cognito.
- **Prod**: Full security controls, strict IAM boundaries, hardened monitoring and retention policies, `AdminCreateUserOnly: true` in Cognito.
