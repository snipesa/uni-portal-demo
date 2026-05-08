#!/usr/bin/env bash
#
# Runs Terraform for the single migration root.
# By default this initializes and plans only. Pass --deploy to run apply.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy-infra.sh -e <environment> [--deploy|--destroy]

Options:
  -e, -env   Target environment
  --deploy   Run terraform apply instead of stopping after terraform plan
  --destroy  Run terraform destroy (non-interactive)
  -h         Show this help message
EOF
}

ENVIRONMENT=""
AUTO_DEPLOY="false"
AUTO_DESTROY="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -env|-e)
      ENVIRONMENT="${2:-}"
      shift 2
      ;;
    --deploy)
      AUTO_DEPLOY="true"
      shift
      ;;
    --destroy)
      AUTO_DESTROY="true"
      shift
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

if [ "$AUTO_DEPLOY" = "true" ] && [ "$AUTO_DESTROY" = "true" ]; then
  echo "Error: --deploy and --destroy cannot be used together." >&2
  usage
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_ROOT="${REPO_ROOT}/infrastructure/terraform/root"
BACKEND_CONFIG="${TERRAFORM_ROOT}/backend.hcl"
BACKEND_EXAMPLE="${TERRAFORM_ROOT}/backend.hcl.example"

if [ ! -f "$BACKEND_CONFIG" ]; then
  echo "Error: backend config not found: ${BACKEND_CONFIG}" >&2
  echo "Create it from: ${BACKEND_EXAMPLE}" >&2
  exit 1
fi

BACKEND_REGION="$(sed -nE 's/^[[:space:]]*region[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$BACKEND_CONFIG" | tail -n 1)"
if [ -z "$BACKEND_REGION" ]; then
  echo "Error: region not found in backend config: ${BACKEND_CONFIG}" >&2
  exit 1
fi

export AWS_REGION="$BACKEND_REGION"
export AWS_DEFAULT_REGION="$BACKEND_REGION"
# Ensure SDKs (including Terraform AWS backend/provider chain) load ~/.aws/config
# so SSO profiles using sso_session are resolved correctly when AWS_PROFILE is set.
export AWS_SDK_LOAD_CONFIG=1

# If a profile is set (common with SSO), materialize session credentials into
# env vars so Terraform backend/provider can authenticate consistently.
if [ -n "${AWS_PROFILE:-}" ] && command -v aws >/dev/null 2>&1; then
  if PROFILE_CREDS="$(aws configure export-credentials --profile "${AWS_PROFILE}" --format env 2>/dev/null)"; then
    # shellcheck disable=SC1090
    eval "$PROFILE_CREDS"
    unset AWS_PROFILE
  fi
fi

echo "=========================================="
echo " Terraform Infrastructure"
echo "=========================================="

if command -v aws >/dev/null 2>&1; then
  echo ""
  echo "==> Verifying AWS caller identity..."
  if ! aws sts get-caller-identity --output text >/dev/null 2>&1; then
    echo "Error: unable to resolve AWS credentials for Terraform." >&2
    echo "Use one of: active SSO session, access keys env vars, or CI role credentials." >&2
    if [ -n "${AWS_PROFILE:-}" ]; then
      echo "Current AWS_PROFILE='${AWS_PROFILE}' failed. If using SSO, run: aws sso login --profile ${AWS_PROFILE}" >&2
    fi
    exit 1
  fi
fi
echo "  Environment : ${ENVIRONMENT}"
echo "  Root        : ${TERRAFORM_ROOT}"
echo "  Backend     : ${BACKEND_CONFIG}"
echo "  AWS Region  : ${BACKEND_REGION}"
echo "  Deploy      : ${AUTO_DEPLOY}"
echo "  Destroy     : ${AUTO_DESTROY}"
echo "=========================================="

cd "$TERRAFORM_ROOT"

echo ""
echo "==> Initializing Terraform..."
terraform init -reconfigure -backend-config=backend.hcl

if [ "$AUTO_DEPLOY" = "true" ]; then
  echo ""
  echo "==> Applying Terraform..."
  terraform apply -auto-approve -var "environment=${ENVIRONMENT}"
elif [ "$AUTO_DESTROY" = "true" ]; then
  echo ""
  echo "==> Destroying Terraform resources..."
  terraform destroy -auto-approve -var "environment=${ENVIRONMENT}"
else
  echo ""
  echo "==> Planning Terraform..."
  terraform plan -var "environment=${ENVIRONMENT}"
  echo ""
  echo "Plan complete. Re-run with --deploy to apply."
fi
