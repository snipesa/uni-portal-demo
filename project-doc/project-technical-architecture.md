# University Assignment Portal - Technical Architecture and Tooling

## Purpose
This document captures the tooling and architecture to implement the University Assignment
Submission and Grading Portal. It is a technical baseline for future story breakdown.

## High-Level Architecture

1. Edge and delivery layer serves the web application through AWS Amplify Hosting.
2. Authenticated users interact with a REST API (HTTP API) for metadata and CRUD operations.
3. Client updates are handled through standard HTTP requests.
4. File uploads happen directly from browser to S3 using short-lived presigned URLs.
5. Business logic runs in a single REST Lambda handler.
6. Metadata and grading records are stored in DynamoDB (single-table design).
7. Observability and security controls are enabled across services.

## Tooling and Services
### Frontend and Delivery
- AWS Amplify Hosting: Managed HTTPS/CDN hosting for the current static portal page and future SPA builds.
- Amazon S3 (Frontend Deployment Artifacts): Stores zipped `frontend-builds/` artifacts used by Amplify manual deployments.
- Amazon Route 53: DNS routing (deferred — manual CNAME until custom domain is set up).
- AWS WAF: Request filtering, rate limiting, basic threat protection (future enhancement).

### Identity and Access
- Amazon Cognito User Pool: User sign-up/sign-in, JWT issuance, group-based roles.
- IAM: Least-privilege roles for REST Lambda and service integrations.

### API and Application Layer
- AWS API Gateway HTTP API (v2): RESTful routes with Cognito JWT authorizer, single-stage auto-deploy.
- AWS Lambda (REST API Handler): Unified Python 3.12 function with modular route files — presigned URL generation, submission CRUD, comments, grades, downloads.

### Storage and Data
- Amazon S3 (Private Upload Bucket): Assignment files and revised versions. Browser uploads via presigned PUT URLs.
- Amazon S3 (Frontend Deployment Artifacts): Frontend zip artifacts consumed by Amplify deployments.
- Amazon DynamoDB (Single-Table Design): Submissions, versions, comments, and grades — with GSIs for student and course query paths.
- S3 lifecycle → Glacier Flexible Retrieval: Archive old versions after policy threshold.
- S3 lifecycle → Keep just one version of deleted objects.

### Security and Encryption
- S3 SSE-S3 (AES256): Server-side encryption at rest for both buckets.
- S3 Block Public Access: Enforced on the upload bucket.
- Amplify Hosting: Provides managed HTTPS delivery for the website.
- Presigned upload URLs: Short expiration, scoped object key paths per user/role.

### Monitoring and Operations
- Amazon CloudWatch: Log groups for Lambda and API Gateway, metric filters, alarms, dashboards.
- API Gateway Metrics: Request count, 4xx/5xx errors, and latency (HTTP API).

## Why REST (Instead of AppSync + GraphQL)

1. **Simpler learning curve** — REST is universally understood; no GraphQL schema or resolver language to learn.
2. **Fewer Lambda functions** — One unified REST handler with route modules replaces multiple single-purpose Lambdas behind AppSync resolvers.
3. **Standard HTTP API pricing** — API Gateway HTTP API is significantly cheaper than AppSync per-request pricing.
4. **Portable architecture** — REST routes can migrate to any platform (ECS, EC2, self-hosted) without rewriting the API layer.
5. **Direct Cognito JWT integration** — HTTP API has a built-in JWT authorizer.

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
4. Frontend calls `POST /uploads/confirm` — Lambda verifies the S3 object exists via `HeadObject` and marks the submission as `SUBMITTED`.

### Review and Grading
1. Instructor calls `GET /submissions` filtered by course and term.
2. Instructor downloads a file via `GET /downloads/{submissionId}/{versionNumber}` which returns a presigned GET URL.
3. Instructor adds comments via `POST /comments` and grades via `POST /grades`.
4. Users refresh or re-query submissions to see latest comments and grades.

## Environment Strategy
- **Dev**: Core stack active, permissive CORS (`*`), `DeletionPolicy: Delete` on DynamoDB, lower alarm thresholds, self-registration enabled in Cognito.
- **Prod**: Full security controls, strict IAM boundaries, hardened monitoring and retention policies, `AdminCreateUserOnly: true` in Cognito.

## Suggested Next Breakdown Areas (Stories/Epics)
1. Identity and role model (Student, Instructor, TA).
2. REST API routes and authorization rules.
3. Submission/versioning workflow.
4. Commenting and grading workflow.
5. Observability, alerting, and operational runbooks.
