import json


def log_request(
    agent_name: str,
    model: str,
    messages: list[dict],
    tools: list | None = None,
    stream: bool = False,
) -> None:
    mode = "stream" if stream else "sync"
    print(f"\n── {agent_name} request [{mode}] ──")
    print(f"  model: {model}")
    if tools:
        print(f"  tools: {[t['function']['name'] for t in tools]}")
    print("  messages:")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    print("──────────────────────────────────────\n")


def log_response(agent_name: str, response) -> None:
    msg = response.choices[0].message
    print(f"\n── {agent_name} response ──")
    if msg.content:
        print(f"  content: {msg.content[:400]}")
    if msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"  tool_call: {tc.function.name}({tc.function.arguments})")
    if response.usage:
        u = response.usage
        print(f"  tokens: input={u.prompt_tokens}  output={u.completion_tokens}  total={u.total_tokens}")
    print("──────────────────────────────────────\n")
