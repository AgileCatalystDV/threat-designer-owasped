import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from services.threat_designer_service import (
    check_status,
    check_trail,
    delete_tm,
    delete_session,
    fetch_all,
    fetch_results,
    generate_presigned_download_url,
    generate_presigned_download_urls_batch,
    generate_presigned_url,
    invoke_lambda,
    restore,
    update_results,
)
from services.collaboration_service import (
    share_threat_model,
    get_collaborators,
    remove_collaborator,
    update_collaborator_access,
    list_cognito_users,
)
from services.lock_service import (
    acquire_lock,
    refresh_lock,
    release_lock,
    get_lock_status,
    force_release_lock,
)

LOG = logging.getLogger(__name__)
router = APIRouter()

# No-auth mode: all requests run as LOCAL_USER
LOCAL_USER = os.environ.get("LOCAL_USER", "local-user")


# ── Status / Trail ─────────────────────────────────────────────────────────

@router.get("/threat-designer/status/{id}")
@router.get("/threat-designer/mcp/status/{id}")
def _tm_status(id: str):
    return check_status(id)


@router.get("/threat-designer/trail/{id}")
def _tm_trail(id: str):
    return check_trail(id)


# ── Fetch single / all ─────────────────────────────────────────────────────

@router.get("/threat-designer/all")
@router.get("/threat-designer/mcp/all")
def _fetch_all(
    limit: int = Query(default=20),
    cursor: Optional[str] = Query(default=None),
    filter: str = Query(default="all"),
):
    allowed_page_sizes = [10, 20, 50, 100]
    if limit not in allowed_page_sizes:
        return JSONResponse(status_code=400, content={"error": "Page size must be 10, 20, 50, or 100"})

    allowed_filters = ["owned", "shared", "all"]
    if filter not in allowed_filters:
        return JSONResponse(status_code=400, content={"error": "Filter must be 'owned', 'shared', or 'all'"})

    result = fetch_all(LOCAL_USER, limit=limit, cursor=cursor, filter_mode=filter)

    if isinstance(result, dict) and result.get("error"):
        return JSONResponse(status_code=400, content=result)

    return result


@router.get("/threat-designer/{id}")
@router.get("/threat-designer/mcp/{id}")
def _tm_fetch_results(id: str):
    return fetch_results(id, LOCAL_USER)


# ── Create / Start ─────────────────────────────────────────────────────────

@router.post("/threat-designer")
@router.post("/threat-designer/mcp")
async def tm_start(request: Request):
    body = await request.json()
    return invoke_lambda(LOCAL_USER, body)


# ── Update / Restore ───────────────────────────────────────────────────────

@router.put("/threat-designer/restore/{id}")
@router.put("/threat-designer/mcp/restore/{id}")
def _restore(id: str):
    return restore(id, LOCAL_USER)


@router.put("/threat-designer/{id}")
@router.put("/threat-designer/mcp/{id}")
async def _update_results(id: str, request: Request):
    body = await request.json()
    lock_token = body.get("lock_token")
    return update_results(id, body, LOCAL_USER, lock_token)


# ── Delete ─────────────────────────────────────────────────────────────────

@router.delete("/threat-designer/{id}/session/{session_id}")
@router.delete("/threat-designer/mcp/{id}/session/{session_id}")
def _delete_session(id: str, session_id: str):
    return delete_session(id, session_id, LOCAL_USER)


@router.delete("/threat-designer/{id}")
@router.delete("/threat-designer/mcp/{id}")
def _delete(id: str, force_release: bool = Query(default=False)):
    return delete_tm(id, LOCAL_USER, force_release)


# ── Upload / Download ──────────────────────────────────────────────────────

@router.post("/threat-designer/upload")
@router.post("/threat-designer/mcp/upload")
async def _upload(request: Request):
    body = await request.json()
    file_type = body.get("file_type")
    return generate_presigned_url(file_type)


@router.post("/threat-designer/download")
async def _download(request: Request):
    body = await request.json()
    threat_model_id = body.get("threat_model_id")
    return generate_presigned_download_url(threat_model_id, LOCAL_USER)


@router.post("/threat-designer/download/batch")
async def _download_batch(request: Request):
    body = await request.json()

    if "threat_model_ids" not in body:
        return JSONResponse(status_code=400, content={"error": "Missing required field: threat_model_ids"})

    threat_model_ids = body.get("threat_model_ids")

    if not isinstance(threat_model_ids, list):
        return JSONResponse(status_code=400, content={"error": "threat_model_ids must be an array"})
    if len(threat_model_ids) == 0:
        return JSONResponse(status_code=400, content={"error": "threat_model_ids array cannot be empty"})
    if len(threat_model_ids) > 50:
        return JSONResponse(status_code=400, content={"error": "Batch size cannot exceed 50 items"})

    results = generate_presigned_download_urls_batch(threat_model_ids, LOCAL_USER)
    return {"results": results}


# ── Collaboration ──────────────────────────────────────────────────────────

@router.post("/threat-designer/{id}/share")
async def _share_threat_model(id: str, request: Request):
    body = await request.json()
    collaborators = body.get("collaborators", [])
    return share_threat_model(id, LOCAL_USER, collaborators)


@router.get("/threat-designer/{id}/collaborators")
def _get_collaborators(id: str):
    return get_collaborators(id, LOCAL_USER)


@router.delete("/threat-designer/{id}/collaborators/{collab_user_id}")
def _remove_collaborator(id: str, collab_user_id: str):
    return remove_collaborator(id, LOCAL_USER, collab_user_id)


@router.put("/threat-designer/{id}/collaborators/{collab_user_id}")
async def _update_collaborator_access(id: str, collab_user_id: str, request: Request):
    body = await request.json()
    new_access_level = body.get("access_level")
    return update_collaborator_access(id, LOCAL_USER, collab_user_id, new_access_level)


@router.get("/threat-designer/users")
def _list_users(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100),
):
    return list_cognito_users(search_filter=search, max_results=limit, exclude_user=LOCAL_USER)


# ── Lock management ────────────────────────────────────────────────────────

@router.post("/threat-designer/{id}/lock")
def _acquire_lock(id: str):
    result = acquire_lock(id, LOCAL_USER)
    if not result.get("success"):
        return JSONResponse(status_code=409, content=result)
    return result


@router.put("/threat-designer/{id}/lock/heartbeat")
async def _refresh_lock(id: str, request: Request):
    body = await request.json()
    lock_token = body.get("lock_token")
    result = refresh_lock(id, LOCAL_USER, lock_token)
    if not result.get("success") and result.get("status_code") == 410:
        return JSONResponse(status_code=410, content=result)
    return result


@router.delete("/threat-designer/{id}/lock")
async def _release_lock(id: str, request: Request):
    body = await request.json()
    lock_token = body.get("lock_token")
    return release_lock(id, LOCAL_USER, lock_token)


@router.get("/threat-designer/{id}/lock/status")
def _get_lock_status(id: str):
    return get_lock_status(id)


@router.delete("/threat-designer/{id}/lock/force")
def _force_release_lock(id: str):
    return force_release_lock(id, LOCAL_USER)
