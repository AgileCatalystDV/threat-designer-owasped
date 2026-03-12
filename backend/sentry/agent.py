import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_mcp_adapters.client import MultiServerMCPClient
from models import InvocationRequest
from session_manager import session_manager
from agent_manager import agent_manager
from handlers import handlers
from streaming import streaming_handler, cancel_stream_async
from exceptions import MissingHeader
from utils import logger, load_mcp_config
from config import ALL_AVAILABLE_TOOLS
from tools import add_threats, edit_threats, delete_threats, get_attack_tree
from tavily_tools import get_tavily_tools

LOCAL_USER = os.environ.get("LOCAL_USER", "local-user")


def get_user_id(http_request: Request) -> str:
    """Return local user in no-auth mode; optionally decode real JWT if present."""
    return LOCAL_USER


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mcp_config = load_mcp_config()
        mcp_tools = MultiServerMCPClient(mcp_config)
        mcp_tools_list = await mcp_tools.get_tools()

        # Filter out unwanted tools
        excluded_tools = {"aws___list_regions"}
        filtered_mcp_tools = [
            tool for tool in mcp_tools_list if tool.name not in excluded_tools
        ]

        if len(filtered_mcp_tools) < len(mcp_tools_list):
            excluded_count = len(mcp_tools_list) - len(filtered_mcp_tools)
            logger.debug(f"Filtered out {excluded_count} MCP tool(s): {excluded_tools}")
    except Exception as e:
        logger.error(f"Failed to load mcp tools: {e}")
        filtered_mcp_tools = []
    try:
        ALL_AVAILABLE_TOOLS.clear()
        ALL_AVAILABLE_TOOLS.extend(filtered_mcp_tools)

        # Load Tavily tools if configured
        tavily_tools = get_tavily_tools()

        if tavily_tools:
            logger.debug(
                f"Loaded {len(tavily_tools)} Tavily tools: {[t.name for t in tavily_tools]}"
            )
            ALL_AVAILABLE_TOOLS.extend(tavily_tools)

        ALL_AVAILABLE_TOOLS.extend(
            [add_threats, edit_threats, delete_threats, get_attack_tree]
        )
        await agent_manager.initialize_default_agent()
    except Exception as e:
        logger.error(f"Failed to initialize default agent: {e}")
        raise

    try:
        yield
    finally:
        logger.debug("Shutting down...")
        # Clear session cache
        session_manager.clear_cache()


# Initialize FastAPI app
app = FastAPI(title="Sentry Agent Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET, POST, OPTIONS"],
    allow_headers=["*"],
)


@app.options("/invocations")
async def handle_options():
    return {"message": "OK"}


@app.post("/invocations")
async def invoke(request: InvocationRequest, http_request: Request):
    """Process user input and return appropriate response type"""

    # Accept either X-Session-Id (local) or legacy AgentCore header
    session_header = (
        http_request.headers.get("X-Session-Id")
        or http_request.headers.get("X-Amzn-Bedrock-AgentCore-Runtime-Session-Id")
    )
    if not session_header:
        raise MissingHeader

    # Parse session header format: threat_model_id/session_seed
    if "/" in session_header:
        threat_model_id, _seed = session_header.rsplit("/", 1)
    else:
        threat_model_id = session_header

    # No-auth mode: use LOCAL_USER
    user_sub = get_user_id(http_request)

    # Create composite session key: sub/threat_model_id
    # Note: We ignore the session seed - it's only used by the UI for session management
    # The backend session is tied to user + threat model, not browser tab
    composite_session_key = (
        f"{user_sub}/{threat_model_id}" if user_sub else threat_model_id
    )

    # Get or create session ID for this composite session key
    session_id = session_manager.get_or_create_session_id(composite_session_key)

    request_type = request.input.get("type")

    if (not request_type) or (request_type == "resume_interrupt"):
        return await streaming_handler.handle_streaming_request(request, session_id)

    # Handle immediate response types with normal returns
    if request_type == "ping":
        return handlers.handle_ping()

    if request_type == "stop":
        return await cancel_stream_async(session_id)

    if request_type == "tools":
        return await handlers.handle_tools()

    if request_type == "history":
        return await handlers.handle_history(session_id)

    if request_type == "delete_history":
        await cancel_stream_async(session_id)
        return handlers.handle_delete_history(composite_session_key, session_id)

    if request_type == "prepare":
        return await handlers.handle_prepare(request)


@app.get("/ping")
async def ping():
    return JSONResponse({"status": "Healthy"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        loop="uvloop",
        http="httptools",
        timeout_keep_alive=75,
        access_log=False,
    )
