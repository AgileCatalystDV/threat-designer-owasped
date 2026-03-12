"""
Attack Tree Route Handler — FastAPI version

Provides REST API endpoints for attack tree operations.
"""

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.attack_tree_service import (
    invoke_attack_tree_agent,
    check_attack_tree_status,
    fetch_attack_tree,
    delete_attack_tree,
    update_attack_tree,
    get_attack_tree_metadata,
)
from exceptions.exceptions import (
    BadRequestError,
    UnauthorizedError,
    NotFoundError,
    InternalError,
)

LOG = logging.getLogger(__name__)
router = APIRouter()

LOCAL_USER = os.environ.get("LOCAL_USER", "local-user")


@router.post("/attack-tree")
async def create_attack_tree(request: Request):
    """Initiate attack tree generation for a specific threat."""
    body = await request.json()

    threat_model_id = body.get("threat_model_id")
    threat_name = body.get("threat_name")
    threat_description = body.get("threat_description")
    reasoning = body.get("reasoning", 0)

    if not threat_model_id:
        raise BadRequestError("threat_model_id is required")
    if not threat_name:
        raise BadRequestError("threat_name is required")
    if not threat_description:
        raise BadRequestError("threat_description is required")
    if not isinstance(reasoning, int) or reasoning < 0 or reasoning > 3:
        raise BadRequestError("reasoning must be an integer between 0 and 3")

    result = invoke_attack_tree_agent(
        owner=LOCAL_USER,
        threat_model_id=threat_model_id,
        threat_name=threat_name,
        threat_description=threat_description,
        reasoning=reasoning,
    )
    LOG.info("Attack tree generation initiated: %s", result.get("attack_tree_id"))
    return result


@router.get("/attack-tree/{attack_tree_id}/status")
def get_attack_tree_status(attack_tree_id: str):
    """Poll the status of attack tree generation."""
    return check_attack_tree_status(attack_tree_id, LOCAL_USER)


@router.get("/attack-tree/{attack_tree_id}")
def get_attack_tree(attack_tree_id: str):
    """Retrieve a completed attack tree in React Flow format."""
    result = fetch_attack_tree(attack_tree_id, LOCAL_USER)
    LOG.info("Attack tree retrieved: %s", attack_tree_id)
    return result


@router.put("/attack-tree/{attack_tree_id}")
async def update_attack_tree_endpoint(attack_tree_id: str, request: Request):
    """Update an existing attack tree with new data."""
    body = await request.json()

    if "attack_tree" not in body:
        raise BadRequestError("attack_tree is required in request body")

    attack_tree_data = body["attack_tree"]
    if not isinstance(attack_tree_data, dict):
        raise BadRequestError("attack_tree must be an object")

    result = update_attack_tree(attack_tree_id, attack_tree_data, LOCAL_USER)
    LOG.info("Attack tree updated: %s", attack_tree_id)
    return result


@router.delete("/attack-tree/{attack_tree_id}")
def delete_attack_tree_endpoint(attack_tree_id: str):
    """Delete an attack tree. Returns 204 No Content on success."""
    delete_attack_tree(attack_tree_id, LOCAL_USER)
    LOG.info("Attack tree deleted: %s", attack_tree_id)
    return JSONResponse(status_code=204, content=None)


@router.get("/threat-models/{threat_model_id}/attack-trees/metadata")
def get_attack_tree_metadata_endpoint(threat_model_id: str):
    """Get metadata about which threats have attack trees."""
    result = get_attack_tree_metadata(threat_model_id, LOCAL_USER)
    LOG.info(
        "Attack tree metadata retrieved for threat model: %s (%d threats)",
        threat_model_id,
        len(result.get("threats_with_attack_trees", [])),
    )
    return result
