#!/usr/bin/env bash
#
# Runs Terraform for the single migration root.
# By default this initializes and plans only. Pass --deploy to run apply.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy-infra.sh -e <environment> [--deploy]

Options:
  -e, -env   Target environment
  --deploy   Run terraform apply instead of stopping after terraform plan
  -h         Show this help message
EOF
}

ENVIRONMENT=""
AUTO_DEPLOY="false"

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

echo "=========================================="
echo " Terraform Infrastructure"
echo "=========================================="
echo "  Environment : ${ENVIRONMENT}"
echo "  Root        : ${TERRAFORM_ROOT}"
echo "  Backend     : ${BACKEND_CONFIG}"
echo "  Deploy      : ${AUTO_DEPLOY}"
echo "=========================================="

cd "$TERRAFORM_ROOT"

echo ""
echo "==> Initializing Terraform..."
terraform init -backend-config=backend.hcl

if [ "$AUTO_DEPLOY" = "true" ]; then
  echo ""
  echo "==> Applying Terraform..."
  terraform apply -var "environment=${ENVIRONMENT}"
else
  echo ""
  echo "==> Planning Terraform..."
  terraform plan -var "environment=${ENVIRONMENT}"
  echo ""
  echo "Plan complete. Re-run with --deploy to apply."
fi
