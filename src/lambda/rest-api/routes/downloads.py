"""
routes/downloads.py — Presigned download URL generation.

GET /downloads/{submissionId}/{versionNumber}
    Validates the caller has access to the submission, loads the version item
    to resolve the S3 key, and returns a presigned GET URL.
    Students may only download versions of their own submissions.
"""
from __future__ import annotations

import logging
import os

import boto3
from botocore.config import Config

from utils import response as resp
from utils.course_access import caller_can_access_submission

logger = logging.getLogger(__name__)

_BUCKET = os.environ["UPLOAD_BUCKET_NAME"]
_TABLE = os.environ["MAIN_TABLE_NAME"]
_EXPIRY = int(os.environ.get("PRESIGNED_URL_EXPIRY_SECONDS", "900"))

_s3 = boto3.client("s3", config=Config(signature_version="s3v4"))
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE)


def handle_download_request(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /downloads/{submissionId}/{versionNumber}"""
    submission_id = (path_params.get("submissionId") or "").strip()
    version_number_str = (path_params.get("versionNumber") or "").strip()

    if not submission_id or not version_number_str:
        return resp.bad_request(
            "submissionId and versionNumber path parameters are required."
        )

    try:
        version_number = int(version_number_str)
    except ValueError:
        return resp.bad_request("versionNumber must be an integer.")

    # Load submission metadata for ownership check
    meta_result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}
    )
    submission = meta_result.get("Item")
    if not submission:
        return resp.not_found("Submission")

    if not caller_can_access_submission(caller, submission):
        return resp.forbidden("You do not have access to this submission.")

    # Load the specific version item to get the S3 key
    version_result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": f"VERSION#{version_number:04d}"}
    )
    version_item = version_result.get("Item")
    if not version_item:
        return resp.not_found("Version")

    s3_key: str = version_item["s3Key"]

    download_url = _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": _BUCKET, "Key": s3_key},
        ExpiresIn=_EXPIRY,
    )

    return resp.ok({
        "submissionId": submission_id,
        "versionNumber": version_number,
        "originalFilename": version_item.get("originalFilename"),
        "downloadUrl": download_url,
        "expiresInSeconds": _EXPIRY,
    })
