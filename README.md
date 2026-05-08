# University Assignment Portal (Terraform)

This repository contains a self-implemented University Assignment Portal built with Terraform-managed AWS infrastructure and Python 3.12 Lambda services.

## High-Level Implementation

- Infrastructure as Code with Terraform
- Role-aware authentication and authorization with Cognito
- REST API backend with API Gateway + Lambda
- Assignment file workflows with S3 presigned URLs
- Submission metadata and workflow state in DynamoDB
- Static frontend website deployment

## Deployment Steps

1. Go to the Terraform root and create local config files:

```bash
cd infrastructure/terraform/root
cp backend.hcl.example backend.hcl
cp terraform.tfvars.example terraform.tfvars
```

2. Update the necessary manual values in `backend.hcl` and `terraform.tfvars` (for example `operations_bucket_name` and environment-specific settings).

3. Package and publish the Lambda artifact:

```bash
cd ../../scripts
./package-lambda.sh -e <environment>
```

4. Deploy infrastructure (first pass):

```bash
./deploy-infra.sh -e <environment> --deploy
```

5. Deploy frontend website:

```bash
./deploy-frontend.sh -e <environment>
```

6. Copy the website output value from the frontend deployment result, then update `infrastructure/terraform/root/terraform.tfvars` with that website value.

7. Redeploy infrastructure after the tfvars update:

```bash
./deploy-infra.sh -e <environment> --deploy
```

8. Redeploy frontend website so runtime config is regenerated from current Terraform outputs:

```bash
./deploy-frontend.sh -e <environment>
```

9. Verify deployment:

```bash
cd ../terraform/root
terraform output
```

10. Verify login flow in browser (hard refresh with `Cmd+Shift+R` / `Ctrl+Shift+R`) to ensure the latest `config.js` values are used.

## Post-Deployment Access

- Use the deployed site URL for the main portal, and use `<deployed-url>/admin` for the admin section.
- In AWS Cognito, create users as needed and add admin users to the `Admin` group so they can access admin features.

## Cleanup

1. Empty the created S3 buckets first (especially upload and artifact buckets), including object versions if versioning is enabled.
2. Run infrastructure destroy:

```bash
cd infrastructure/scripts
./deploy-infra.sh -e <environment> --destroy
```

## Documentation

- [Project Documentation Index](./project-doc/README.md)
