# The effects of AI recommendation on epistemic diversity

- **Authors:** (working draft, unattributed)
- **Year:** 2026
- **Source:** [latex/main.tex](latex/main.tex) /
  [latex/main.pdf](latex/main.pdf)

## What this folder explores

A two-armed bandit model in which $n$ independent myopic Bayesian agents
each try to identify the better arm. An optional AI recommender $\rho$
injects a *common* latent state $Z$ into every agent's evidence, inducing
correlation across otherwise-independent histories. The paper's central
claim is that the AI raises every individual's discovery probability
while lowering the community's discovery probability, by reducing
epistemic diversity.

This folder builds the model from scratch, in phases:

| Phase | Scope | Sections of the paper |
|:---|:---|:---|
| 1 | Standard two-armed bandit + Beta-Bernoulli agents (no recommender) | §1–§2 |
| 2 | AI recommender with common state $Z$, agent conditions on $R_i^t$ | §3–§5 |
| 3 | Empirical verification of the mechanism (§6)                       | §6 |

**Phase 1 is implemented.** The recommender interface is stubbed
([model/recommender.py](model/recommender.py)) so Phase 2 is a drop-in.

## Repository structure

```text
recommender_epistemic_diversity/
├── README.md                                    # this file
├── CLAUDE.md                                    # per-project AI-agent context
├── HOUSEKEEPING.md                              # recurring health-check routine
├── TODO_WORKFLOW.md                             # cross-session task backlog
├── worklog.jsonl                                # append-only session log (oldest first)
├── housekeeping_log.jsonl                       # append-only housekeeping audit log
├── notes.md                                     # reading notes on the paper
├── requirements.txt                             # paper-specific Python deps
├── .gitignore                                   # LaTeX aux, __pycache__, .ipynb_checkpoints, ...
│
├── latex/                                       # paper source + compiled PDF
│   ├── .latexmkrc                               # lualatex + biber toolchain locks
│   ├── main.tex                                 # working paper source (\ignacio/\michael notes)
│   ├── main.pdf                                 # current compile
│   ├── main_backup.tex                          # backup copy of main.tex
│   ├── main_backup.pdf                          # compile of the backup
│   └── build/                                   # all build artifacts: aux, log, synctex (gitignored)
│
├── model/                                       # the model codebase (Phase 1)
│   ├── __init__.py
│   ├── bandit.py                                # BernoulliBandit (arms A, B; p_A > p_B)
│   ├── agent.py                                 # BetaBernoulliAgent (myopic Bayesian)
│   ├── recommender.py                           # Recommender interface + NullRecommender stub
│   ├── discovery.py                             # three operational definitions of D_i
│   └── simulation.py                            # run_simulation orchestrator
│
├── experiments/                                 # numbered notebooks, pipeline order
│   └── 1. Phase 1 - Unaided Bandit.ipynb       # §1–§2 reproduction; writes to results/
│
├── tests/                                       # pytest suite for model/
│   ├── __init__.py
│   └── test_model.py
│
└── results/                                     # notebook outputs (CSVs, PNGs)
    ├── phase1_posterior_trajectories.png
    └── phase1_summary_<YYYYMMDD_HHMMSS>.csv
```

**Conventions:**
- Logic lives in [model/](model/). Notebooks under [experiments/](experiments/)
  orchestrate and visualise only — they follow the knowledge-base
  `NOTEBOOK_WRITING_SKILL` (top-down structure, `%%time` on heavy cells,
  stable cell IDs, `SMOKE_TEST` flag, tiered compute budget).
- Notebooks are named `<stage>. <title>.ipynb` so the pipeline order is
  visible in the filename. Phase 2 will land as `2. Phase 2 - ...ipynb`.
- All artifacts (CSVs, PNGs, pickles) go under [results/](results/) with
  a timestamp so reruns under different parameters do not overwrite each
  other.
- Two LaTeX sources coexist in [latex/](latex/): `main.tex` is the working
  paper (full prose plus inline `\ignacio{}` / `\michael{}` drafting
  comments); `main_backup.tex` is a backup copy of it. The `latex/` root is
  kept to exactly these two `.tex` files, their two PDFs, and `.latexmkrc` —
  every other build artifact lives in `latex/build/`.

## Workflow files

This repo follows the knowledge-base `PROJECT_SETUP_WORKFLOW` scaffold:

- [CLAUDE.md](CLAUDE.md) — per-project AI-agent context (stack, run/test
  commands, mandatory first action).
- [TODO_WORKFLOW.md](TODO_WORKFLOW.md) — cross-session task backlog plus
  the canonical schema and append protocol for `worklog.jsonl`.
- [HOUSEKEEPING.md](HOUSEKEEPING.md) — recurring static / test / health
  check routine; latest report lives inline at the bottom.
- `worklog.jsonl`, `housekeeping_log.jsonl` — append-only JSONL audit
  logs (oldest first, one record per line, not registered with kb_mcp).

## Run

```bash
pip install -r requirements.txt
jupyter lab "experiments/1. Phase 1 - Unaided Bandit.ipynb"
```

## Test

```bash
pytest tests/
```

18 tests currently green: bandit input validation, conjugate Beta updates,
myopic-Bayesian choice, three discovery definitions, simulation
reproducibility under a fixed seed, and a long-run "concentrates on the
better arm" sanity check.

## Build the paper PDF

```bash
cd latex && latexmk
```

The `.latexmkrc` pins lualatex + biber and routes **all** build artifacts
(aux, log, synctex, intermediate PDF) into `build/`; a `$success_cmd` then
copies just the finished PDF back alongside the `.tex`. See
[LATEX_TYPESETTING_EXPLANATION.md](LATEX_TYPESETTING_EXPLANATION.md) for
the full toolchain reference (prerequisites, what `.latexmkrc` locks
down, common flags, troubleshooting, and adding a bibliography).
