"""
routes/comments.py — Comment creation.

POST /comments
    Writes a COMMENT#{timestamp}#{commentId} item to the submission partition.
    Students may only comment on their own submissions.
    Staff may comment on any submission they can access.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

from utils import response as resp
from utils.course_access import caller_can_access_submission

logger = logging.getLogger(__name__)

_TABLE = os.environ["MAIN_TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE)


def handle_create_comment(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /comments"""
    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    submission_id = (body.get("submissionId") or "").strip()
    comment_body = (body.get("body") or "").strip()
    version_ref = body.get("versionRef")  # optional — integer version number

    if not submission_id or not comment_body:
        return resp.bad_request("submissionId and body are required.")

    # Validate submission exists and enforce student ownership
    meta_result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}
    )
    submission = meta_result.get("Item")
    if not submission:
        return resp.not_found("Submission")

    if not caller_can_access_submission(caller, submission):
        return resp.forbidden("You do not have access to this submission.")

    comment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    sk = f"COMMENT#{now}#{comment_id}"

    comment_item: dict = {
        "PK": f"SUBMISSION#{submission_id}",
        "SK": sk,
        "EntityType": "COMMENT",
        "commentId": comment_id,
        "authorId": caller["sub"],
        "authorRole": caller["primary_group"],
        "body": comment_body,
        "createdAt": now,
    }
    if version_ref is not None:
        try:
            version_ref = int(version_ref)
            if version_ref < 1:
                raise ValueError
        except (TypeError, ValueError):
            return resp.bad_request("versionRef must be a positive integer.")
        comment_item["versionRef"] = version_ref

    _table.put_item(Item=comment_item)

    return resp.ok(
        {
            "commentId": comment_id,
            "submissionId": submission_id,
            "createdAt": now,
        },
        status=201,
    )
