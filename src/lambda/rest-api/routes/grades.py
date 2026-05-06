"""
routes/grades.py — Grade create / update.

POST /grades
    Restricted to staff users assigned to the submission's course.
    Creates or replaces the GRADE item for a submission (idempotent upsert).
    When status is PUBLISHED, also flips the submission status to GRADED.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import boto3

from utils import response as resp
from utils.auth import is_staff
from utils.course_access import caller_can_access_submission

logger = logging.getLogger(__name__)

_TABLE = os.environ["MAIN_TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE)

_VALID_STATUSES = {"DRAFT", "PUBLISHED"}


def handle_upsert_grade(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /grades"""
    if not is_staff(caller):
        return resp.forbidden("Only staff can submit grades.")

    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    submission_id = (body.get("submissionId") or "").strip()
    score = body.get("score")
    max_score = body.get("maxScore")
    feedback = (body.get("feedback") or "").strip()
    status = (body.get("status") or "DRAFT").strip().upper()

    if not submission_id or score is None or max_score is None:
        return resp.bad_request("submissionId, score, and maxScore are required.")

    if status not in _VALID_STATUSES:
        return resp.bad_request("status must be DRAFT or PUBLISHED.")

    # Verify submission exists before writing the grade
    meta_result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}
    )
    submission = meta_result.get("Item")
    if not submission:
        return resp.not_found("Submission")
    if not caller_can_access_submission(caller, submission):
        return resp.forbidden("You do not have access to this submission.")

    now = datetime.now(timezone.utc).isoformat()

    _table.put_item(Item={
        "PK": f"SUBMISSION#{submission_id}",
        "SK": "GRADE",
        "EntityType": "GRADE",
        "score": score,
        "maxScore": max_score,
        "feedback": feedback,
        "gradedBy": caller["sub"],
        "gradedAt": now,
        "status": status,
    })

    # When a grade is published, surface the GRADED status on the submission
    if status == "PUBLISHED":
        _table.update_item(
            Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"},
            UpdateExpression="SET #st = :s, updatedAt = :ts",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":s": "GRADED", ":ts": now},
        )

    return resp.ok({
        "submissionId": submission_id,
        "score": score,
        "maxScore": max_score,
        "status": status,
        "gradedAt": now,
    })
