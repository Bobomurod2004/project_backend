import ollama
from config import (
    OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_API_KEY,
    OLLAMA_TIMEOUT, NUM_PREDICT,
)
from llm.tools import get_tools, call_tool


def _make_client() -> ollama.Client:
    headers = {}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    return ollama.Client(
        host=OLLAMA_HOST,
        headers=headers,
        timeout=OLLAMA_TIMEOUT,
    )


def chat(
    messages: list[dict],
    system: str | None = None,
) -> tuple[str, list[dict], list[dict]]:
    """
    Returns: (reply_text, updated_messages, called_tools)
    called_tools: [{"name": "...", "args": {...}}, ...]
    """
    client = _make_client()
    tools = get_tools()

    full_messages: list[dict] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    called_tools: list[dict] = []

    while True:
        kwargs: dict = {
            "model": OLLAMA_MODEL,
            "messages": full_messages,
            "options": {"num_predict": NUM_PREDICT},
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat(**kwargs)
        msg = response.message

        if msg.tool_calls:
            full_messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                result = call_tool(
                    tc.function.name,
                    tc.function.arguments,
                )
                called_tools.append({
                    "name": tc.function.name,
                    "args": tc.function.arguments,
                    "result": result,
                })
                full_messages.append({
                    "role": "tool",
                    "content": result,
                    "name": tc.function.name,
                })
            continue

        reply_text = msg.content or ""
        full_messages.append({"role": "assistant", "content": reply_text})
        return reply_text, full_messages, called_tools
