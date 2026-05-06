"""
routes/uploads.py — Upload initialisation and confirmation.

POST /uploads/request
    Creates a Submission (METADATA) and Version (VERSION#0001) intent in
    DynamoDB, then returns a presigned PUT URL the browser uploads directly
    to S3.  The submission stays in PENDING_UPLOAD until confirmed.

POST /uploads/confirm
    Verifies the file actually arrived in S3 via HeadObject, then flips the
    submission status to SUBMITTED.

POST /submissions/{submissionId}/versions/request
    Creates the next submission version intent and returns a presigned PUT URL.

POST /submissions/{submissionId}/versions/confirm
    Verifies the revised file upload and flips the submission back to SUBMITTED.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.config import Config
from botocore.exceptions import ClientError

from utils import response as resp
from utils.auth import is_staff
from utils.course_access import (
    build_course_pk,
    get_assignment_item,
    get_course_item,
    normalize_assignment_id,
    normalize_course_id,
    normalize_term_id,
    student_is_enrolled,
)

logger = logging.getLogger(__name__)

_BUCKET = os.environ["UPLOAD_BUCKET_NAME"]
_TABLE = os.environ["MAIN_TABLE_NAME"]
_EXPIRY = int(os.environ.get("PRESIGNED_URL_EXPIRY_SECONDS", "900"))

_s3 = boto3.client("s3", config=Config(signature_version="s3v4"))
_dynamodb = boto3.resource("dynamodb")
_dynamodb_client = boto3.client("dynamodb")
_table = _dynamodb.Table(_TABLE)
_type_serializer = TypeSerializer()


def _ddb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: _type_serializer.serialize(value) for key, value in item.items()}


def _get_submission_metadata(submission_id: str) -> dict[str, Any] | None:
    result = _table.get_item(Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"})
    return result.get("Item")


def _get_submission_version(submission_id: str, version_number: int) -> dict[str, Any] | None:
    result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": f"VERSION#{version_number:04d}"}
    )
    return result.get("Item")


def handle_upload_request(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /uploads/request"""
    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    if is_staff(caller):
        return resp.forbidden("Only students can create submissions.")

    course_id = normalize_course_id(body.get("courseId"))
    term_id = normalize_term_id(body.get("termId"))
    assignment_id = normalize_assignment_id(body.get("assignmentId"))
    title = (body.get("title") or "").strip()
    original_filename = (body.get("originalFilename") or "").strip()
    file_size_bytes: Any = body.get("fileSizeBytes")  # optional

    if not all([course_id, term_id, assignment_id, title, original_filename]):
        return resp.bad_request(
            "courseId, termId, assignmentId, title, and originalFilename are required."
        )
    if file_size_bytes is not None:
        try:
            file_size_bytes = int(file_size_bytes)
            if file_size_bytes < 0:
                raise ValueError
        except (TypeError, ValueError):
            return resp.bad_request("fileSizeBytes must be a non-negative integer.")

    course = get_course_item(course_id, term_id)
    if not course:
        return resp.not_found("Course")
    if not course.get("active", True):
        return resp.bad_request("This course is no longer accepting submissions.")

    assignment = get_assignment_item(course_id, term_id, assignment_id)
    if not assignment:
        return resp.not_found("Assignment")
    if not assignment.get("active", True):
        return resp.bad_request("This assignment is no longer accepting submissions.")

    if not student_is_enrolled(course_id, term_id, caller["sub"]):
        return resp.forbidden("You are not enrolled in this course.")

    submission_id = str(uuid.uuid4())
    version_number = 1
    now = datetime.now(timezone.utc).isoformat()
    s3_key = (
        f"submissions/{caller['sub']}/{submission_id}"
        f"/v{version_number:04d}/{original_filename}"
    )

    metadata_item: dict[str, Any] = {
        "PK": f"SUBMISSION#{submission_id}",
        "SK": "METADATA",
        "EntityType": "SUBMISSION",
        "submissionId": submission_id,
        "studentId": caller["sub"],
        "courseId": course_id,
        "termId": term_id,
        "assignmentId": assignment_id,
        "title": title,
        "status": "PENDING_UPLOAD",
        "currentVersion": version_number,
        "createdAt": now,
        "updatedAt": now,
        "GSI1PK": f"STUDENT#{caller['sub']}",
        "GSI1SK": f"SUBMISSION#{now}#{submission_id}",
        "GSI2PK": build_course_pk(course_id, term_id),
        "GSI2SK": f"SUBMISSION#{now}#{submission_id}",
    }

    # Version record
    version_item: dict[str, Any] = {
        "PK": f"SUBMISSION#{submission_id}",
        "SK": f"VERSION#{version_number:04d}",
        "EntityType": "VERSION",
        "versionNumber": version_number,
        "s3Key": s3_key,
        "originalFilename": original_filename,
        "uploadedBy": caller["sub"],
        "uploadedAt": now,
    }
    if file_size_bytes is not None:
        version_item["fileSizeBytes"] = file_size_bytes

    # Atomic write so submission metadata and initial version are always in sync.
    try:
        _dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": _TABLE,
                        "Item": _ddb_item(metadata_item),
                        "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                    }
                },
                {
                    "Put": {
                        "TableName": _TABLE,
                        "Item": _ddb_item(version_item),
                        "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                    }
                },
            ]
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"TransactionCanceledException", "ConditionalCheckFailedException"}:
            return resp.conflict("A submission conflict occurred. Please retry.")
        raise

    # Presigned PUT URL — browser uploads directly to S3
    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": _BUCKET, "Key": s3_key},
        ExpiresIn=_EXPIRY,
    )

    return resp.ok(
        {
            "submissionId": submission_id,
            "versionNumber": version_number,
            "s3Key": s3_key,
            "uploadUrl": upload_url,
            "expiresInSeconds": _EXPIRY,
        },
        status=201,
    )


def handle_upload_confirm(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /uploads/confirm"""
    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    submission_id = (body.get("submissionId") or "").strip()
    version_number_raw = body.get("versionNumber")

    if not submission_id or version_number_raw is None:
        return resp.bad_request("submissionId and versionNumber are required.")
    try:
        version_number = int(version_number_raw)
        if version_number < 1:
            raise ValueError
    except (TypeError, ValueError):
        return resp.bad_request("versionNumber must be a positive integer.")

    pk = f"SUBMISSION#{submission_id}"
    submission = _get_submission_metadata(submission_id)
    if not submission:
        return resp.not_found("Submission")
    if is_staff(caller):
        return resp.forbidden("Only students can confirm uploads.")
    if submission.get("studentId") != caller["sub"]:
        return resp.forbidden("You do not have access to this submission.")

    # Load version item to get the s3Key
    version_item = _get_submission_version(submission_id, version_number)
    if not version_item:
        return resp.not_found("Version")

    s3_key: str = version_item["s3Key"]

    # Verify object exists in S3
    try:
        _s3.head_object(Bucket=_BUCKET, Key=s3_key)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            return resp.not_found("Upload object — file has not been uploaded yet")
        raise

    # Flip submission status
    now = datetime.now(timezone.utc).isoformat()
    _table.update_item(
        Key={"PK": pk, "SK": "METADATA"},
        UpdateExpression="SET #st = :s, updatedAt = :ts",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": "SUBMITTED", ":ts": now},
    )

    return resp.ok({"submissionId": submission_id, "status": "SUBMITTED"})


def handle_version_upload_request(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /submissions/{submissionId}/versions/request"""
    submission_id = (path_params.get("submissionId") or "").strip()
    if not submission_id:
        return resp.bad_request("submissionId path parameter is required.")

    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    original_filename = (body.get("originalFilename") or "").strip()
    file_size_bytes: Any = body.get("fileSizeBytes")
    if not original_filename:
        return resp.bad_request("originalFilename is required.")
    if file_size_bytes is not None:
        try:
            file_size_bytes = int(file_size_bytes)
            if file_size_bytes < 0:
                raise ValueError
        except (TypeError, ValueError):
            return resp.bad_request("fileSizeBytes must be a non-negative integer.")

    if is_staff(caller):
        return resp.forbidden("Only students can upload revised versions.")

    submission = _get_submission_metadata(submission_id)
    if not submission:
        return resp.not_found("Submission")
    if submission.get("studentId") != caller["sub"]:
        return resp.forbidden("You do not have access to this submission.")
    if submission.get("status") != "NEEDS_REVISION":
        return resp.bad_request("Only submissions in NEEDS_REVISION can accept a revised upload.")

    course_id = str(submission.get("courseId", ""))
    term_id = str(submission.get("termId", ""))
    assignment_id = str(submission.get("assignmentId", ""))

    course = get_course_item(course_id, term_id)
    if not course:
        return resp.not_found("Course")
    if not course.get("active", True):
        return resp.bad_request("This course is no longer accepting submissions.")

    assignment = get_assignment_item(course_id, term_id, assignment_id)
    if not assignment:
        return resp.not_found("Assignment")
    if not assignment.get("active", True):
        return resp.bad_request("This assignment is no longer accepting submissions.")
    if not student_is_enrolled(course_id, term_id, caller["sub"]):
        return resp.forbidden("You are not enrolled in this course.")

    version_number = int(submission.get("currentVersion", 0)) + 1
    now = datetime.now(timezone.utc).isoformat()
    s3_key = (
        f"submissions/{caller['sub']}/{submission_id}"
        f"/v{version_number:04d}/{original_filename}"
    )

    version_item: dict[str, Any] = {
        "PK": f"SUBMISSION#{submission_id}",
        "SK": f"VERSION#{version_number:04d}",
        "EntityType": "VERSION",
        "versionNumber": version_number,
        "s3Key": s3_key,
        "originalFilename": original_filename,
        "uploadedBy": caller["sub"],
        "uploadedAt": now,
    }
    if file_size_bytes is not None:
        version_item["fileSizeBytes"] = file_size_bytes

    try:
        _dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": _TABLE,
                        "Item": _ddb_item(version_item),
                        "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                    }
                },
                {
                    "Update": {
                        "TableName": _TABLE,
                        "Key": _ddb_item({"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}),
                        "UpdateExpression": "SET currentVersion = :v, #st = :s, updatedAt = :ts",
                        "ExpressionAttributeNames": {"#st": "status"},
                        "ExpressionAttributeValues": _ddb_item({
                            ":v": version_number,
                            ":s": "PENDING_UPLOAD",
                            ":ts": now,
                            ":student": caller["sub"],
                            ":required_status": "NEEDS_REVISION",
                        }),
                        "ConditionExpression": "studentId = :student AND #st = :required_status",
                    }
                },
            ]
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"TransactionCanceledException", "ConditionalCheckFailedException"}:
            return resp.conflict("A revised upload is already in progress. Refresh and try again.")
        raise

    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": _BUCKET, "Key": s3_key},
        ExpiresIn=_EXPIRY,
    )

    return resp.ok(
        {
            "submissionId": submission_id,
            "versionNumber": version_number,
            "s3Key": s3_key,
            "uploadUrl": upload_url,
            "expiresInSeconds": _EXPIRY,
        },
        status=201,
    )


def handle_version_upload_confirm(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /submissions/{submissionId}/versions/confirm"""
    submission_id = (path_params.get("submissionId") or "").strip()
    if not submission_id:
        return resp.bad_request("submissionId path parameter is required.")

    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    version_number_raw = body.get("versionNumber")
    if version_number_raw is None:
        return resp.bad_request("versionNumber is required.")
    try:
        version_number = int(version_number_raw)
        if version_number < 2:
            raise ValueError
    except (TypeError, ValueError):
        return resp.bad_request("versionNumber must be an integer greater than 1.")

    if is_staff(caller):
        return resp.forbidden("Only students can confirm revised uploads.")

    submission = _get_submission_metadata(submission_id)
    if not submission:
        return resp.not_found("Submission")
    if submission.get("studentId") != caller["sub"]:
        return resp.forbidden("You do not have access to this submission.")

    version_item = _get_submission_version(submission_id, version_number)
    if not version_item:
        return resp.not_found("Version")

    s3_key: str = version_item["s3Key"]
    try:
        _s3.head_object(Bucket=_BUCKET, Key=s3_key)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            return resp.not_found("Upload object — file has not been uploaded yet")
        raise

    now = datetime.now(timezone.utc).isoformat()
    _table.update_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"},
        UpdateExpression="SET #st = :s, currentVersion = :v, updatedAt = :ts",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": "SUBMITTED", ":v": version_number, ":ts": now},
    )

    return resp.ok({
        "submissionId": submission_id,
        "versionNumber": version_number,
        "status": "SUBMITTED",
    })
