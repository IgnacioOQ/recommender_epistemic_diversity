# MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**Before reading any file, answering any question, or starting any task — call this tool:**

```
mcp__kb_mcp__knowledge_base_read(path="content/workflows/CODING_AGENT_MAIN_WORKFLOW.md", skip_dependencies=True)
```

This is non-negotiable. Do not process the user's first message until this call completes. It is your root operating protocol and governs everything that follows: context discovery, task execution rules, knowledge capture, and session wrap-up.

---

## What this project is

A from-scratch Python implementation of the two-armed bandit + AI-recommender model from the paper **"The effects of AI recommendation on epistemic diversity"** ([latex/recommenders_v2.tex](latex/recommenders_v2.tex)). Phase 1 (unaided Beta-Bernoulli bandit, §1–§2) is implemented; Phase 2 (recommender with common latent state $Z$) is stubbed; Phase 3 (empirical verification, §6) is open.

## Stack

- **Language:** Python (deps pinned in [requirements.txt](requirements.txt) — `numpy`, `scipy`, `matplotlib`, `jupyterlab`, `pytest`, `tqdm`).
- **Paper:** LaTeX, compiled with `lualatex` + `biber` via `latexmk` ([latex/.latexmkrc](latex/.latexmkrc)).
- **No formatter / linter / type checker configured** — see `HOUSEKEEPING.md` § Outstanding if you intend to introduce one.

## Architecture

Monolith — the model lives in a single small package [model/](model/) (≈5 modules, ~600 lines total). Do not split into a modular shell.

- [model/bandit.py](model/bandit.py) — `BernoulliBandit(p_a, p_b)` with `p_A > p_B` invariant.
- [model/agent.py](model/agent.py) — `BetaBernoulliAgent`, independent Beta priors per arm, myopic Bayesian choice.
- [model/recommender.py](model/recommender.py) — `Recommender` interface + `NullRecommender` stub (Phase 2 drop-in).
- [model/discovery.py](model/discovery.py) — three operational definitions of the discovery indicator $D_i$.
- [model/simulation.py](model/simulation.py) — `run_simulation` orchestrator, reproducible via `SeedSequence`.

## How to run

```bash
pip install -r requirements.txt
jupyter lab "experiments/1. Phase 1 - Unaided Bandit.ipynb"
```

## How to test

```bash
pytest tests/
```

Current baseline: 18 tests, all green.

## How to build the paper PDF

```bash
cd latex && latexmk
```

`.latexmkrc` pins lualatex + biber, sends aux files to `latex/build/` (gitignored), and drops `recommenders_v2.pdf` alongside the `.tex`.

## Project-specific conventions

- **Logic in [model/](model/), orchestration in [experiments/](experiments/).** Notebooks visualise and parametrise only — no model logic lives in a notebook.
- **Notebooks are named `<stage>. <title>.ipynb`** so pipeline order is visible in the filename (e.g. `1. Phase 1 - ...`, future `2. Phase 2 - ...`).
- **All artifacts go under [results/](results/)** with a `YYYYMMDD_HHMMSS` timestamp so reruns under different parameters do not overwrite each other.
- **Two `.tex` sources in [latex/](latex/):**
  - `recommenders_v2.tex` — the current working paper.
  - `recommenders_commented.tex` — the original paper with `\ignacio{}` margin annotations that informed v2. Keep both; do not delete.
- **Workflow files live at repo root** — see `TODO_WORKFLOW.md` for the deferred-task backlog, `HOUSEKEEPING.md` for the recurring health check, `worklog.jsonl` and `housekeeping_log.jsonl` for their respective append-only audit logs.

## Relevant KB skills

- `content/workflows/CODING_AGENT_MAIN_WORKFLOW.md` — session protocol (loaded by the mandatory first action above).
- `content/how-to/NOTEBOOK_WRITING_SKILL.md` — conventions the experiment notebooks follow (top-down structure, `%%time` on heavy cells, stable cell IDs, `SMOKE_TEST` flag, tiered compute budget).
- `content/how-to/HOUSEKEEPING_SKILL.md` — how to drive this repo's `HOUSEKEEPING.md` workflow.
- `content/templates/TODO_WORKFLOW_TEMPLATE.md` — canonical schema for `worklog.jsonl` and the task-backlog format used here.
