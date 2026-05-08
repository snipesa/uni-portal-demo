#!/usr/bin/env bash
#
# Packages the REST API Lambda source, uploads the deployment zip to the manual
# operations bucket, and updates the SSM parameter that Terraform reads.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./package-lambda.sh -e <environment>

Options:
  -e, -env  Target environment
  -h        Show this help message
EOF
}

ENVIRONMENT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -env|-e)
      ENVIRONMENT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument '$1'" >&2
      usage
      exit 1
      ;;
  esac
done

if [ -z "$ENVIRONMENT" ]; then
  echo "Error: -e <environment> is required." >&2
  usage
  exit 1
fi

if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
  echo "Error: -e <environment> must be one of: dev, prod." >&2
  usage
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_TFVARS="${REPO_ROOT}/infrastructure/terraform/root/terraform.tfvars"
SRC_DIR="${REPO_ROOT}/src/lambda/rest-api"

if [ ! -f "$TERRAFORM_TFVARS" ]; then
  echo "Error: Terraform values file not found: ${TERRAFORM_TFVARS}" >&2
  exit 1
fi

if [ ! -d "$SRC_DIR" ]; then
  echo "Error: Lambda source directory not found: ${SRC_DIR}" >&2
  exit 1
fi

get_tfvar() {
  local key="$1"
  sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]+)\".*/\1/p" "$TERRAFORM_TFVARS" | tail -n 1
}

PROJECT_NAME="$(get_tfvar "project_name")"
BUCKET="$(get_tfvar "operations_bucket_name")"
LAMBDA_ARTIFACT_PREFIX="$(get_tfvar "lambda_artifact_prefix")"
AWS_REGION="$(get_tfvar "aws_region")"

PROJECT_NAME="${PROJECT_NAME:-cytora-uni-portal}"
LAMBDA_ARTIFACT_PREFIX="${LAMBDA_ARTIFACT_PREFIX:-lambda-artifacts}"
LAMBDA_ARTIFACT_PREFIX="${LAMBDA_ARTIFACT_PREFIX%/}"

if [ -z "$BUCKET" ]; then
  echo "Error: could not read operations_bucket_name from ${TERRAFORM_TFVARS}" >&2
  exit 1
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ZIP_NAME="${TIMESTAMP}-rest-api.zip"
S3_KEY="${LAMBDA_ARTIFACT_PREFIX}/${ENVIRONMENT}/${ZIP_NAME}"
SSM_PARAM_PATH="/${PROJECT_NAME}/${ENVIRONMENT}/rest-lambda-zip"

echo "=========================================="
echo " Lambda Packaging"
echo "=========================================="
echo "  Environment : ${ENVIRONMENT}"
echo "  Project     : ${PROJECT_NAME}"
echo "  Artifact    : s3://${BUCKET}/${S3_KEY}"
echo "  SSM Path    : ${SSM_PARAM_PATH}"
echo "=========================================="

BUILD_DIR="$(mktemp -d)"
ZIP_PATH="${BUILD_DIR}/${ZIP_NAME}"

trap 'rm -rf "$BUILD_DIR"' EXIT

echo ""
echo "==> Copying source files..."
cp -R "${SRC_DIR}/." "${BUILD_DIR}/"

REQUIREMENTS_FILE="${SRC_DIR}/requirements.txt"
if grep -qvE '^[[:space:]]*(#.*)?$' "${REQUIREMENTS_FILE}" 2>/dev/null; then
  echo "==> Installing dependencies from requirements.txt..."
  pip install -r "${REQUIREMENTS_FILE}" -t "${BUILD_DIR}" --quiet
else
  echo "==> No third-party dependencies to install."
fi

echo "==> Creating ${ZIP_NAME}..."
(
  cd "${BUILD_DIR}"
  zip -r "${ZIP_PATH}" . \
    --exclude "*.pyc" \
    --exclude "*.pyo" \
    --exclude "*/__pycache__/*" \
    --exclude "__pycache__/*" \
    --exclude "*.dist-info/*" \
    --exclude "*.egg-info/*" \
    --exclude ".pytest_cache/*" \
    --exclude ".mypy_cache/*" \
    --exclude ".ruff_cache/*" \
    --exclude "build/*" \
    --exclude "dist/*" \
    --exclude "*.zip" \
    --exclude ".DS_Store" \
    --exclude "requirements.txt" \
    >/dev/null
)

ZIP_SIZE="$(du -sh "${ZIP_PATH}" | cut -f1)"
echo "    Package size: ${ZIP_SIZE}"

AWS_ARGS=()
if [ -n "$AWS_REGION" ]; then
  AWS_ARGS+=(--region "$AWS_REGION")
fi

echo "==> Uploading to s3://${BUCKET}/${S3_KEY}..."
aws "${AWS_ARGS[@]}" s3 cp "${ZIP_PATH}" "s3://${BUCKET}/${S3_KEY}"

echo "==> Updating SSM parameter ${SSM_PARAM_PATH}..."
aws "${AWS_ARGS[@]}" ssm put-parameter \
  --name "${SSM_PARAM_PATH}" \
  --value "${S3_KEY}" \
  --type "String" \
  --overwrite \
  --output text \
  --query 'Version' \
  | xargs -I{} echo "    SSM version: {}"

echo ""
echo "=========================================="
echo " Done."
echo "  Zip         : ${ZIP_NAME}"
echo "  S3 Key      : ${S3_KEY}"
echo "  SSM updated : ${SSM_PARAM_PATH}"
echo "=========================================="
