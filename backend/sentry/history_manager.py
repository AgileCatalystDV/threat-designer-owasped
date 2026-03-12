from utils import logger
import time
import random
import string
import json
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from session_manager import session_manager


async def get_history(agent, id):
    config = {"configurable": {"thread_id": id}}
    history = agent.aget_state_history(config=config, limit=1)
    last = await anext(history, None)
    interrupt = None

    if last:
        # Check if there are interrupts and extract the first one
        if last.interrupts and len(last.interrupts) > 0:
            interrupt = last.interrupts[0].value

        msg = last.values.get("messages", [])
        formatted_history = format_chat_for_frontend(msg, interrupt)
        return formatted_history
    return None


def format_chat_for_frontend(backend_messages, interrupt=None):
    """
    Convert backend message format to frontend format.

    Args:
        backend_messages: List of message objects from backend (HumanMessages, AIMessages, ToolMessages)
        interrupt: Optional interrupt data to add at the end

    Returns:
        List of chatTurn objects for frontend consumption
    """
    chat_turns = []
    current_turn = None

    def generate_turn_id():
        timestamp = int(time.time() * 1000)
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=9)
        )
        return f"turn_{timestamp}_{random_suffix}"

    for message in backend_messages:
        if isinstance(message, HumanMessage):
            # Start a new turn
            if current_turn:
                # Add end marker before adding to chat_turns
                current_turn["aiMessage"].append({"end": True})
                chat_turns.append(current_turn)

            # Extract user message from the last element (user prompt is always last)
            user_message = ""
            if message.content:
                if isinstance(message.content, str):
                    # Simple string content
                    user_message = message.content
                elif isinstance(message.content, list) and len(message.content) > 0:
                    # List format - get the last item (user prompt is always last)
                    last_item = message.content[-1]
                    if isinstance(last_item, dict):
                        user_message = last_item.get("text", "")
                    elif isinstance(last_item, str):
                        user_message = last_item
                elif isinstance(message.content, dict):
                    # Dict format - extract text field
                    user_message = message.content.get("text", "")

            current_turn = {
                "id": generate_turn_id(),
                "userMessage": user_message,
                "aiMessage": [],
            }

        elif isinstance(message, AIMessage):
            if not current_turn:
                # Handle case where AI message comes without user message
                current_turn = {
                    "id": generate_turn_id(),
                    "userMessage": "",
                    "aiMessage": [],
                }

            # Process each content item in the AIMessage
            for content_item in message.content:
                if content_item.get("type") == "reasoning_content":
                    # Bedrock format
                    current_turn["aiMessage"].append(
                        {
                            "type": "think",
                            "content": content_item["reasoning_content"].get(
                                "text", " "
                            ),
                        }
                    )
                elif content_item.get("type") == "reasoning":
                    # OpenAI GPT-5 format: {"type": "reasoning", "summary": [{"type": "summary_text", "text": "..."}]}
                    summary = content_item.get("summary", [])
                    if summary and isinstance(summary, list):
                        # Combine all summary text items into one reasoning block
                        combined_text = "\n\n".join(
                            item.get("text", "")
                            for item in summary
                            if item.get("type") == "summary_text" and item.get("text")
                        )
                        if combined_text:
                            current_turn["aiMessage"].append(
                                {
                                    "type": "think",
                                    "content": combined_text,
                                }
                            )
                elif content_item.get("type") == "tool_use":
                    current_turn["aiMessage"].append(
                        {
                            "type": "tool",
                            "id": content_item["id"],
                            "tool_name": content_item["name"],
                            "tool_start": True,
                        }
                    )
                elif content_item.get("type") == "function_call":
                    # OpenAI function call format
                    current_turn["aiMessage"].append(
                        {
                            "type": "tool",
                            "id": content_item.get("call_id"),
                            "tool_name": content_item["name"],
                            "tool_start": True,
                        }
                    )
                else:
                    # Regular text content
                    text_content = content_item.get("text", "").strip()
                    if text_content:  # Only add non-empty text
                        current_turn["aiMessage"].append(
                            {"type": "text", "content": text_content}
                        )

        elif isinstance(message, ToolMessage):
            if current_turn:
                try:
                    content = json.loads(message.content)
                    current_turn["aiMessage"].append(
                        {
                            "type": "tool",
                            "id": message.tool_call_id,
                            "tool_name": message.name,
                            "tool_start": False,
                            "content": content,
                            "error": message.status == "error",
                        }
                    )
                except Exception:
                    logger.debug("Unable to parse tool message content")
                    current_turn["aiMessage"].append(
                        {
                            "type": "tool",
                            "id": message.tool_call_id,
                            "tool_name": message.name,
                            "tool_start": False,
                            "content": message.content,
                        }
                    )

    # Handle the last turn
    if current_turn:
        # Add interrupt as final message if provided
        if interrupt:
            current_turn["aiMessage"].append(
                {"type": "interrupt", "content": interrupt}
            )
        else:
            # Otherwise add end marker
            current_turn["aiMessage"].append({"end": True})
        chat_turns.append(current_turn)
    # Create a new turn for the interrupt if there's no current turn
    elif interrupt:
        chat_turns.append(
            {
                "id": generate_turn_id(),
                "userMessage": "",
                "aiMessage": [{"type": "interrupt", "content": interrupt}],
            }
        )

    return chat_turns


def delete_bedrock_session(session_header: str, session_id: str) -> bool:
    """Delete a local session (no Bedrock AgentCore in local mode)."""
    try:
        session_manager.delete_session(session_header)
        logger.debug(f"[history_manager] Deleted local session {session_id}")
        return True
    except Exception as exc:
        logger.error(f"[history_manager] Error deleting session {session_id}: {exc}")
        return False
