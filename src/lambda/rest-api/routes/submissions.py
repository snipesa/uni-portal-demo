"""
routes/submissions.py — Submission read APIs.

GET /submissions
    Students: lists own submissions via GSI1 (STUDENT#{sub}).
    Staff: lists submissions for a courseId query param via GSI2.

GET /submissions/{submissionId}
    Returns the METADATA item for one submission.
    Students are blocked from accessing other students' submissions.

GET /submissions/{submissionId}/details
    Returns submission metadata plus versions, comments, grade, and display info.

POST /submissions/{submissionId}/status
    Assigned staff may request revision or move the workflow back to submitted.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from utils import response as resp
from utils.auth import is_staff
from utils.cognito_users import find_user_by_sub
from utils.course_access import (
    build_course_pk,
    caller_can_access_submission,
    get_assignment_item,
    get_staff_assignment_item,
    normalize_course_id,
    normalize_term_id,
    staff_is_assigned,
)

logger = logging.getLogger(__name__)

_TABLE = os.environ["MAIN_TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE)
_WORKFLOW_STATUSES = {"SUBMITTED", "NEEDS_REVISION"}


def _split_submission_items(items: list[dict]) -> tuple[dict | None, list[dict], list[dict], dict | None]:
    metadata = None
    versions: list[dict] = []
    comments: list[dict] = []
    grade = None
    for item in items:
        sk = str(item.get("SK", ""))
        if sk == "METADATA":
            metadata = item
        elif sk.startswith("VERSION#"):
            versions.append(item)
        elif sk.startswith("COMMENT#"):
            comments.append(item)
        elif sk == "GRADE":
            grade = item

    versions.sort(key=lambda item: int(item.get("versionNumber", 0)), reverse=True)
    comments.sort(key=lambda item: str(item.get("createdAt", "")))
    return metadata, versions, comments, grade


def _build_user_summary(user_id: str) -> dict:
    profile = find_user_by_sub(user_id) if user_id else None
    return {
        "userId": user_id,
        "email": profile.get("email", "") if profile else "",
        "displayName": profile.get("displayName", "") if profile else "",
        "groups": profile.get("groups", []) if profile else [],
    }


def _build_comment_author_label(comment: dict, submission: dict) -> str:
    author_id = str(comment.get("authorId", ""))
    if author_id and author_id == str(submission.get("studentId", "")):
        return "Student"

    course_id = str(submission.get("courseId", ""))
    term_id = str(submission.get("termId", ""))
    if course_id and term_id and author_id:
        staff_assignment = get_staff_assignment_item(course_id, term_id, author_id)
        if staff_assignment:
            return str(staff_assignment.get("staffRole", "Staff")).replace("_", " ").title()

    groups = comment.get("authorGroups") or []
    if isinstance(groups, list) and "Students" in groups:
        return "Student"
    return "Staff"


def _build_submission_detail(submission_id: str) -> tuple[dict | None, list[dict], list[dict], dict | None]:
    result = _table.query(KeyConditionExpression=Key("PK").eq(f"SUBMISSION#{submission_id}"))
    metadata, versions, comments, grade = _split_submission_items(result.get("Items", []))
    return metadata, versions, comments, grade


def handle_list_submissions(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /submissions"""
    query_params: dict = event.get("queryStringParameters") or {}

    try:
        if is_staff(caller):
            course_id = normalize_course_id(query_params.get("courseId"))
            term_id = normalize_term_id(query_params.get("termId"))
            if not course_id or not term_id:
                return resp.bad_request(
                    "courseId and termId query parameters are required for staff."
                )
            if not staff_is_assigned(course_id, term_id, caller["sub"]):
                return resp.forbidden("You are not assigned to this course.")
            result = _table.query(
                IndexName="GSI2-CourseSubmissions",
                KeyConditionExpression=Key("GSI2PK").eq(build_course_pk(course_id, term_id)),
            )
        else:
            result = _table.query(
                IndexName="GSI1-StudentSubmissions",
                KeyConditionExpression=Key("GSI1PK").eq(f"STUDENT#{caller['sub']}"),
            )
    except ClientError as exc:
        message = exc.response.get("Error", {}).get("Message", "")
        if exc.response.get("Error", {}).get("Code") == "ValidationException" and "specified index" in message:
            logger.exception("submission_index_missing")
            return resp.service_unavailable(
                "Submission listing is temporarily unavailable because the required DynamoDB index is not deployed yet."
            )
        raise

    return resp.ok({
        "submissions": result.get("Items", []),
        "count": result.get("Count", 0),
    })


def handle_get_submission(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /submissions/{submissionId}"""
    submission_id = (path_params.get("submissionId") or "").strip()
    if not submission_id:
        return resp.bad_request("submissionId path parameter is required.")

    result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}
    )
    item = result.get("Item")
    if not item:
        return resp.not_found("Submission")

    # Ownership check — students may only view their own submissions
    if not caller_can_access_submission(caller, item):
        return resp.forbidden("You do not have access to this submission.")

    return resp.ok(item)


def handle_get_submission_details(event: dict, caller: dict, path_params: dict) -> dict:
    """GET /submissions/{submissionId}/details"""
    submission_id = (path_params.get("submissionId") or "").strip()
    if not submission_id:
        return resp.bad_request("submissionId path parameter is required.")

    submission, versions, comments, grade = _build_submission_detail(submission_id)
    if not submission:
        return resp.not_found("Submission")

    if not caller_can_access_submission(caller, submission):
        return resp.forbidden("You do not have access to this submission.")

    student = _build_user_summary(str(submission.get("studentId", "")))
    assignment = get_assignment_item(
        str(submission.get("courseId", "")),
        str(submission.get("termId", "")),
        str(submission.get("assignmentId", "")),
    )

    comment_payload = []
    for item in comments:
        author = _build_user_summary(str(item.get("authorId", "")))
        comment_payload.append({
            "commentId": item.get("commentId"),
            "body": item.get("body", ""),
            "createdAt": item.get("createdAt"),
            "versionRef": item.get("versionRef"),
            "authorId": item.get("authorId"),
            "authorEmail": author.get("email", ""),
            "authorDisplayName": author.get("displayName", ""),
            "authorRoleLabel": _build_comment_author_label(item, submission),
        })

    allowed_actions = {
        "canComment": is_staff(caller),
        "canGrade": is_staff(caller),
        "canRequestRevision": is_staff(caller),
        "canResubmit": (
            not is_staff(caller)
            and str(submission.get("studentId", "")) == caller["sub"]
            and str(submission.get("status", "")) == "NEEDS_REVISION"
        ),
    }

    return resp.ok({
        "submission": submission,
        "student": {
            "studentId": submission.get("studentId"),
            "email": student.get("email", ""),
            "displayName": student.get("displayName", ""),
        },
        "assignment": {
            "assignmentId": submission.get("assignmentId"),
            "title": assignment.get("title", "") if assignment else "",
        },
        "versions": versions,
        "comments": comment_payload,
        "grade": grade,
        "allowedActions": allowed_actions,
    })


def handle_update_submission_status(event: dict, caller: dict, path_params: dict) -> dict:
    """POST /submissions/{submissionId}/status"""
    submission_id = (path_params.get("submissionId") or "").strip()
    if not submission_id:
        return resp.bad_request("submissionId path parameter is required.")
    if not is_staff(caller):
        return resp.forbidden("Only staff can update submission status.")

    try:
        body: dict = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return resp.bad_request("Request body must be valid JSON.")

    new_status = (body.get("status") or "").strip().upper()
    if new_status not in _WORKFLOW_STATUSES:
        return resp.bad_request("status must be SUBMITTED or NEEDS_REVISION.")

    submission_result = _table.get_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"}
    )
    submission = submission_result.get("Item")
    if not submission:
        return resp.not_found("Submission")
    if not caller_can_access_submission(caller, submission):
        return resp.forbidden("You do not have access to this submission.")
    if new_status == "SUBMITTED" and str(submission.get("status", "")) != "NEEDS_REVISION":
        return resp.bad_request("Only submissions in NEEDS_REVISION can be moved back to SUBMITTED.")

    timestamp = datetime.now(timezone.utc).isoformat()
    _table.update_item(
        Key={"PK": f"SUBMISSION#{submission_id}", "SK": "METADATA"},
        UpdateExpression="SET #st = :s, updatedAt = :ts",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":s": new_status, ":ts": timestamp},
    )

    return resp.ok({
        "submissionId": submission_id,
        "status": new_status,
        "updatedAt": timestamp,
    })
