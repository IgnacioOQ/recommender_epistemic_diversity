---
status: active
type: plan
id: 'recommender_epistemic_diversity.todo_workflow'
description: Cross-session task backlog; each task is self-contained and can be picked up by a coding agent with kb_mcp MCP tool access.
label: [planning, agent]
injection: excluded
volatility: evolving
owner: agent
last_checked: '2026-05-28'
---

# TODO Workflow

Cross-session task backlog. Tasks are added here when work started in a session cannot be completed immediately. Each task must be fully self-contained — a fresh agent should be able to pick it up using only the task body and the kb_mcp tools, with no additional context required.

This file is the per-repository instance of the `TODO_WORKFLOW_TEMPLATE.md` pattern in the knowledge base. It lives at the root of the working repository alongside `worklog.jsonl` and is intentionally **not registered with kb_mcp** — agents access it via the regular filesystem `Read`/`Edit` tools, not via `knowledge_base_*` calls.

**Agent rules (picking up tasks):**
1. Read each task in full before starting. If its preconditions are unmet, skip it and note the blocker.
2. **Triage before committing.** If multiple tasks are open, scan them all and rank by value/difficulty ratio — do the cheapest high-value work first. Re-validate the author-set `difficulty` and `value` ratings against the current state of the repo before trusting them; conditions may have shifted since the task was written.
3. After completing a task, delete its entire block from this file (from the `---` divider above the `##` header through the `---` divider below the last line of the task body).
4. After completing one or more tasks, assess whether a `worklog.jsonl` entry is warranted (schema and append protocol below) — see also Phase 6 of `content/workflows/CODING_AGENT_MAIN_WORKFLOW.md`.
5. Confirm a task is still valid before executing; conditions may have changed since it was written.

**Adding tasks (session authors):**
- Copy the template at the bottom (without fences), fill in all fields, and insert it as a new `##` block above the Template section, preceded and followed by `---`.
- **Rate `difficulty` and `value`** (low / medium / high). Difficulty estimates effort and risk; value estimates impact on the repo, users, or future work. Pickup agents use this pair to triage the backlog.
- Be precise: include target file paths, specific tool calls, expected outcomes, and a verification step.
- Any `knowledge_base_update` call requires a current `content_hash` — capture it with a `knowledge_base_read` at execution time, not when writing the task.

## Worklog (`worklog.jsonl`) — Schema & Append Protocol

Each session that does non-trivial work appends one JSON object as a new line to `worklog.jsonl` at this repository's root. The file is plain JSONL — one JSON object per line, **oldest first** (chronological append order). It lives at root, outside any docs-discovery surface (kb_mcp, search indexers).

Bootstrap a new repo with an empty file: `touch worklog.jsonl`. The first entry's `entry_id` is just today's date (`YYYY-MM-DD`).

### Schema (`schema_version: 1`)

```json
{
  "schema_version": 1,
  "entry_id":      "YYYY-MM-DD",
  "date":          "YYYY-MM-DD",
  "session_id":    "5678ee055b7e48d2ba51b514652780e8",
  "summary":       "One-line task summary",
  "body_markdown": "- **Task:** ...\n- **Outcome:** ...\n- **Key decisions:** ...\n- **KB changes:** ...\n- **Follow-up:** ..."
}
```

| Field | Type | Notes |
|:--|:--|:--|
| `schema_version` | int | Currently `1`. Bump on breaking changes. |
| `entry_id` | string | Unique across the file. `YYYY-MM-DD-s{N}` where `N = prior -sN + 1`, or plain `YYYY-MM-DD` for the first entry of a new day. Same-key collisions get `-b` / `-c` / `-d` suffixes. |
| `date` | string | ISO `YYYY-MM-DD`. |
| `session_id` | string \| null | **kb_mcp server boot UUID** (32-char hex) when written via `knowledge_base_append` — matches the UUID in `kb_mcp/_logs/kb_performance_log.jsonl` from the same boot, enabling cross-log join. **`null`** when written via the direct-append fallback (no live kb_mcp to thread the UUID; do not fabricate one). |
| `summary` | string | One-line heading — what the session accomplished. |
| `body_markdown` | string | Full narrative (Task / Outcome / Key decisions / KB changes / Follow-up) as one opaque markdown blob. The inner bullet structure is convention, not schema — pick whatever shape suits the entry. Newlines inside the string must be JSON-escaped as `\n`. |

### Append protocol

**Default — `knowledge_base_append` via `repo://`.** When kb_mcp is reachable and `$EIKASIA` is set, route through the MCP tool. It auto-advances `entry_id` per the date-suffix scheme, threads the kb_mcp boot UUID into `session_id`, refreshes `date` to today, copies other fields verbatim from the prior line, and pre-write backs the file up to `.kb_backups/`.

```text
mcp__kb_mcp__knowledge_base_append(
    path="repo://recommender_epistemic_diversity/worklog.jsonl",
    reason="Log session close-out",
    text_content=(
        "- **Task:** ...\n"
        "- **Outcome:** ...\n"
        "- **Key decisions:** ...\n"
        "- **KB changes:** ...\n"
        "- **Follow-up:** ..."
    ),
)
```

`text_content` lands in `body_markdown`. Use `json_content` instead when the entry needs custom fields beyond the standard schema. JSON-escape newlines inside the markdown as `\n`.

**Fallback — direct filesystem append** (when kb_mcp is not reachable or `$EIKASIA` is unset). Compute the next `entry_id` from the prior record, then append a JSON line with `session_id: null`.

```bash
# 1. Compute the next entry_id (returns today's bare date if the file is empty
#    or the prior entry was from a different day; advances the -sN suffix otherwise):
NEXT_ID=$(if [[ -s worklog.jsonl ]]; then
  tail -1 worklog.jsonl | python3 -c "
import sys, json, datetime, re
prev = json.loads(sys.stdin.read())
today = datetime.date.today().isoformat()
m = re.match(r'^(\d{4}-\d{2}-\d{2})(?:-s(\d+))?$', prev['entry_id'])
print(f'{today}-s{int(m.group(2) or 1) + 1}' if m and m.group(1) == today else today)
"
else
  date -u +%Y-%m-%d
fi)

# 2. Construct and append the entry. session_id MUST be null on this path
#    (the kb_mcp boot UUID is only available from a live kb_mcp process).
python3 - <<PY
import json
entry = {
    "schema_version": 1,
    "entry_id":      "$NEXT_ID",
    "date":          "$(date -u +%Y-%m-%d)",
    "session_id":    None,
    "summary":       "...",
    "body_markdown": "- **Task:** ...\n- **Outcome:** ...",
}
with open("worklog.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
PY
```

Trade-offs vs. the default path: no pre-write backup to `.kb_backups/` (git history is the recovery path), and the entry cannot be joined with `kb_performance_log.jsonl` on `session_id`.

**Skip the worklog append entirely** for trivial one-line changes or purely exploratory sessions with no concrete output.

### Reading back

Render the latest N entries for reference / context loading:

```bash
tail -3 worklog.jsonl | python3 -c "import sys,json; [print(json.dumps(json.loads(l), indent=2)) for l in sys.stdin]"
```

Or query with `jq`:

```bash
jq -r 'select(.session_id != null) | "\(.entry_id): \(.summary)"' worklog.jsonl | tail -10
```

---

## Task Template

Copy the block below (without the outer fences), fill in all fields, and insert it as a new `## [Task Title]` task block. Per-`##` metadata uses a fenced ` ```yaml ` block immediately after the heading (this file is a `plan` document, so the parser lifts these blocks into per-task metadata).

````markdown
## [Task Title]

```yaml
status: todo
type: task
id: todo.[short_id]
description: One-sentence description of what this task accomplishes.
owner: agent
assigned_to: '{{github-handle-or-name}}'  # optional — omit if unassigned
estimate: Xm
difficulty: [low | medium | high]
value: [low | medium | high]
blocked_by: []
last_checked: '{{YYYY-MM-DD}}'
```

**Context:** Why this task exists and what triggered it. Include the KB path or repo file path it operates on.

**Preconditions:** Any state that must be true before starting (prior tasks complete, files present, etc.). Write `none` if there are none.

**Steps:**
1. (Include specific tool calls where possible, e.g., `knowledge_base_read(path="content/...", sections=["..."])`)
2. ...

**Verification:** How to confirm the task is complete (e.g., a grep that should return one match, a status field that should read `done`).

**On completion:** Delete this entire task block from TODO_WORKFLOW.md (from the `---` above the `##` header to the `---` below the last line).
````
