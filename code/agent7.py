"""agent7.py — Session 7 agent orchestrator.

The loop layout is unchanged from Session 6. The only thing that changed
underneath is the Memory service: writes now compute an embedding via the
gateway's V7 embed endpoint and append to a FAISS index; reads use vector
similarity first and fall back to keyword search when the vector path is
empty. Two new MCP tools, index_document and search_knowledge, surface
the same machinery to the model so the agent can ingest external
documents on demand.

The four typed layers:

    memory.read -> perception.observe -> decision.next_step ->
    action.execute -> memory.record_outcome

Perception is the only layer that maintains goal state across iterations.
Memory is a typed service (read / write). The artifact store carries raw
bytes; Decision sees them only when Perception attached them to the
current goal.

Run from this folder:
    uv run agent7.py "What is the current time in Tokyo and Bangalore?"
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import action
import artifacts
import decision
import memory
import perception
from gateway import ensure_gateway
from schemas import Goal

MCP_SERVER = Path(__file__).parent / "mcp_server.py"
MAX_ITERATIONS = 5


def _mcp_tools_for_decision(tools) -> list[dict]:
    """Convert MCP tool descriptors into the shape the gateway expects."""
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema or {"type": "object", "properties": {}},
        }
        for t in tools
    ]


async def run(query: str) -> str:
    ensure_gateway()
    run_id = uuid.uuid4().hex[:8]
    print(f"\n{'═' * 78}")
    print(f"run {run_id}  ─  query: {query}")
    print(f"{'═' * 78}")

    # Durable memory: classify the user's query so facts/preferences in it
    # survive into future runs. Tool outcomes get recorded later by Action;
    # the query itself only gets a memory record if we put it there now.
    try:
        memory.remember(query, source="user_query", run_id=run_id)
    except Exception as e:
        print(f"[memory.remember] skipped: {e}")

    server_params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)])
    history: list[dict] = []
    prior_goals: list[Goal] = []
    final_answer: str = ""

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools_for_decision = _mcp_tools_for_decision(mcp_tools)
            print(f"[mcp] loaded {len(mcp_tools)} tools: {[t.name for t in mcp_tools]}")

            for it in range(1, MAX_ITERATIONS + 1):
                print(f"\n─── iter {it} ─────────────────────────────────────────────")

                # 1. MEMORY READ
                hits = memory.read(query, history)
                print(f"[memory.read]   {len(hits)} hits")

                # 2. PERCEPTION
                obs = perception.observe(query, hits, history, prior_goals, run_id)
                prior_goals = obs.goals
                for g in obs.goals:
                    flag = "✓" if g.done else "○"
                    attach = f"  attach={g.attach_artifact_id}" if g.attach_artifact_id else ""
                    print(f"[perception]    {flag} {g.id} — {g.text}{attach}")

                if obs.all_done:
                    print(f"\n[done] all {len(obs.goals)} goals satisfied")
                    break

                goal = obs.next_unfinished()
                if goal is None:
                    print(f"\n[done] no unfinished goal — stopping")
                    break

                # Perception decided whether to attach an artifact.
                attached: list[tuple[str, bytes]] = []
                if goal.attach_artifact_id and artifacts.exists(goal.attach_artifact_id):
                    blob = artifacts.get_bytes(goal.attach_artifact_id)
                    attached.append((goal.attach_artifact_id, blob))
                    print(f"[attach]        {goal.attach_artifact_id} ({len(blob)} bytes)")

                # 3. DECISION
                out = decision.next_step(goal, hits, attached, history, tools_for_decision)

                if out.is_answer:
                    print(f"[decision]      ANSWER: {out.answer[:200]}{'...' if len(out.answer) > 200 else ''}")
                    history.append({
                        "iter": it,
                        "kind": "answer",
                        "goal_id": goal.id,
                        "text": out.answer,
                    })
                    final_answer = out.answer
                    continue

                # 4. ACTION
                tc = out.tool_call
                print(f"[decision]      TOOL_CALL: {tc.name}({json.dumps(tc.arguments)[:120]})")
                result_text, art_id = await action.execute(session, tc)
                preview = result_text[:200].replace("\n", " ")
                print(f"[action]        → {preview}{'...' if len(result_text) > 200 else ''}"
                      + (f"   +{art_id}" if art_id else ""))

                # 5. MEMORY WRITE (zero-LLM for tool outcomes)
                memory.record_outcome(
                    tool_call=tc,
                    result_text=result_text,
                    artifact_id=art_id,
                    run_id=run_id,
                    goal_id=goal.id,
                )
                history.append({
                    "iter": it,
                    "kind": "action",
                    "goal_id": goal.id,
                    "tool": tc.name,
                    "arguments": tc.arguments,
                    "result_descriptor": result_text[:300],
                    "artifact_id": art_id,
                })

    print(f"\n{'═' * 78}")
    print(f"FINAL: {final_answer}")
    print(f"{'═' * 78}\n")
    return final_answer


class TeeLogger:
    def __init__(self, filepath: Path, original_stdout):
        self.file = open(filepath, "w", encoding="utf-8")
        self.original_stdout = original_stdout

    def write(self, data):
        self.original_stdout.write(data)
        self.file.write(data)

    def flush(self):
        self.original_stdout.flush()
        self.file.flush()

    def close(self):
        self.file.close()


def load_queries() -> dict[str, tuple[str, str]]:
    """Load queries from queries.md.
    Returns a dict mapping the short key (e.g. 'a', 'b', 'c1')
    to a tuple of (full_heading, query_text).
    """
    path = Path(__file__).resolve().parents[1] / "Queries and Logs" / "queries.md"
    if not path.exists():
        return {}
    
    queries = {}
    current_heading = None
    
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_heading = line[3:].strip()
        elif line and current_heading:
            # The query text follows the heading.
            # Extract key prefix, e.g. "A. Shannon Wikipedia" -> "a"
            parts = current_heading.split(".", 1)
            if parts:
                key = parts[0].strip().lower()
                queries[key] = (current_heading, line)
            current_heading = None
            
    return queries


def main() -> None:
    query = " ".join(sys.argv[1:])
    if not query:
        queries = load_queries()
        if queries:
            sys.stderr.write("\nAvailable Reference Queries:\n")
            for key, (heading, _) in queries.items():
                sys.stderr.write(f"  [{key.upper()}] {heading}\n")
            sys.stderr.write("\nHow can I help you today? Please enter query code (e.g. A, B, C1) or custom query: ")
            sys.stderr.flush()
            user_input = sys.stdin.readline().strip()

            # Normalize inputs
            norm_input = user_input.lower().replace(".", "").strip()

            match_key = None
            # Only match shortcuts for short inputs (e.g. single word, length <= 4)
            if len(norm_input) <= 4 and " " not in norm_input:
                if norm_input in queries:
                    match_key = norm_input
                else:
                    matches = [k for k in queries if k.startswith(norm_input)]
                    if len(matches) == 1:
                        match_key = matches[0]
                    elif len(matches) > 1:
                        sys.stderr.write(f"\nAmbiguous code '{user_input}'. Did you mean: {', '.join(k.upper() for k in matches)}?\n")
                        sys.stderr.flush()
                        return
            else:
                # Support space-separated short codes like "c 1" or "f 2"
                no_spaces = norm_input.replace(" ", "")
                if len(no_spaces) <= 4 and no_spaces in queries:
                    match_key = no_spaces

            if match_key:
                heading, query_text = queries[match_key]
                log_dir = Path(__file__).resolve().parents[1] / "Queries and Logs"
                log_dir.mkdir(exist_ok=True)
                # Base log file name
                base_path = log_dir / f"{heading}.log"
                log_path = base_path
                version = 1
                # If a log already exists, create a new versioned file: <heading>_vN.log
                while log_path.exists():
                    log_path = log_dir / f"{heading}_v{version}.log"
                    version += 1

                sys.stderr.write(f"\n[logger] Running selected query and saving log to: {log_path.name}\n")
                sys.stderr.flush()

                logger = TeeLogger(log_path, sys.stdout)
                sys.stdout = logger
                try:
                    asyncio.run(run(query_text))
                finally:
                    sys.stdout = logger.original_stdout
                    logger.close()
                return
            else:
                query = user_input
        else:
            sys.stderr.write("How can I help you today? Please enter your query: ")
            sys.stderr.flush()
            query = sys.stdin.readline().strip()

    if not query:
        return
    asyncio.run(run(query))


if __name__ == "__main__":
    main()
