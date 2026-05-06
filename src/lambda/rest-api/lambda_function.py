"""
lambda_function.py — Lambda entrypoint and route dispatcher.

Responsibilities (thin by design — business logic lives in route modules):
  1. Parse HTTP method and path from the API Gateway v2 payload.
  2. Gate every request through require_auth() — ungrouped users are blocked.
  3. Match method + path against the route table; extract path parameters.
  4. Delegate to the appropriate route handler.
  5. Log one structured line per request (route, sub, group, status).
  6. Return 500 with a correlation ID for any unhandled exception.
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any

from utils.auth import require_auth
from utils import response as resp
from routes import admin, uploads, submissions, comments, grades, downloads, courses

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Route table — (METHOD, compiled-regex, handler)
# Order matters: more-specific patterns must come before catch-alls.
# Path parameters are captured as named groups and forwarded to handlers.
# ---------------------------------------------------------------------------
_ROUTES: list[tuple[str, re.Pattern, Any]] = [
    ("GET",  re.compile(r"^/admin/users$"),                                              admin.handle_get_user_by_email),
    ("POST", re.compile(r"^/admin/groups/add$"),                                         admin.handle_add_user_to_group),
    ("POST", re.compile(r"^/admin/groups/remove$"),                                      admin.handle_remove_user_from_group),
    ("POST", re.compile(r"^/uploads/request$"),                                         uploads.handle_upload_request),
    ("POST", re.compile(r"^/uploads/confirm$"),                                          uploads.handle_upload_confirm),
    ("GET",  re.compile(r"^/submissions$"),                                              submissions.handle_list_submissions),
    ("GET",  re.compile(r"^/submissions/(?P<submissionId>[^/]+)/details$"),              submissions.handle_get_submission_details),
    ("POST", re.compile(r"^/submissions/(?P<submissionId>[^/]+)/status$"),               submissions.handle_update_submission_status),
    ("POST", re.compile(r"^/submissions/(?P<submissionId>[^/]+)/versions/request$"),     uploads.handle_version_upload_request),
    ("POST", re.compile(r"^/submissions/(?P<submissionId>[^/]+)/versions/confirm$"),     uploads.handle_version_upload_confirm),
    ("GET",  re.compile(r"^/submissions/(?P<submissionId>[^/]+)$"),                      submissions.handle_get_submission),
    ("POST", re.compile(r"^/comments$"),                                                 comments.handle_create_comment),
    ("POST", re.compile(r"^/grades$"),                                                   grades.handle_upsert_grade),
    ("GET",  re.compile(r"^/downloads/(?P<submissionId>[^/]+)/(?P<versionNumber>[^/]+)$"), downloads.handle_download_request),
    ("GET",  re.compile(r"^/courses$"),                                                  courses.handle_list_courses),
    ("POST", re.compile(r"^/courses$"),                                                  courses.handle_create_course),
    ("GET",  re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)$"),      courses.handle_get_course),
    ("GET",  re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/assignments$"), courses.handle_list_assignments),
    ("POST", re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/assignments$"), courses.handle_create_assignment),
    ("POST", re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/enrollments$"), courses.handle_enroll_student),
    ("DELETE", re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/enrollments$"), courses.handle_unenroll_student),
    ("POST", re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/staff$"), courses.handle_assign_staff),
    ("DELETE", re.compile(r"^/courses/(?P<courseId>[^/]+)/terms/(?P<termId>[^/]+)/staff$"), courses.handle_unassign_staff),
]


def lambda_handler(event: dict, context: Any) -> dict:
    correlation_id = str(uuid.uuid4())
    method: str = event.get("requestContext", {}).get("http", {}).get("method", "")
    raw_path: str = event.get("rawPath", "")

    # --- Auth gate -----------------------------------------------------------
    caller, auth_err = require_auth(event)
    if auth_err:
        logger.warning(
            "auth_rejected path=%s method=%s correlation_id=%s",
            raw_path, method, correlation_id,
        )
        return auth_err

    # --- Route dispatch -------------------------------------------------------
    try:
        for route_method, pattern, handler in _ROUTES:
            if method != route_method:
                continue
            match = pattern.match(raw_path)
            if match:
                path_params = match.groupdict()
                logger.info(
                    "request route=%s %s sub=%s group=%s correlation_id=%s",
                    method, raw_path,
                    caller["sub"], caller["primary_group"], correlation_id,
                )
                result = handler(event, caller, path_params)
                logger.info(
                    "response route=%s %s status=%s correlation_id=%s",
                    method, raw_path, result.get("statusCode"), correlation_id,
                )
                return result

        logger.warning(
            "no_route method=%s path=%s correlation_id=%s",
            method, raw_path, correlation_id,
        )
        return resp.not_found("Route")

    except Exception:  # pylint: disable=broad-except
        logger.exception(
            "unhandled_exception method=%s path=%s correlation_id=%s",
            method, raw_path, correlation_id,
        )
        return resp.internal_error(correlation_id)
