---
status: active
type: explanation
description: How to compile this paper's .tex sources to PDF via latexmk — what the toolchain pieces are, what .latexmkrc locks down, where the artifacts land, and the common commands.
label: [reference, human]
injection: informational
volatility: stable
scope: project-specific
last_checked: '2026-05-28'
---

# LaTeX Typesetting

Short reference for compiling this paper's `.tex` sources to PDF. The build is self-contained — no dependency on any sibling repo or system-wide template.

## Prerequisites

A TeX distribution with `latexmk`, `lualatex`, and `biber` on `PATH`. On macOS this comes from [MacTeX](https://www.tug.org/mactex/); on Linux from [TeX Live](https://tug.org/texlive/) (`texlive-full` or the smaller `texlive-latex-extra` + `latexmk` + `biber`).

Verify with:

```bash
which latexmk lualatex biber
```

## Compile

From the [latex/](latex/) directory:

```bash
cd latex
latexmk                              # build the default target (every .tex in cwd)
latexmk recommenders_v2.tex          # build just the current paper
latexmk recommenders_commented.tex   # build the annotated variant
```

`latexmk` reads [latex/.latexmkrc](latex/.latexmkrc), runs `lualatex` (and `biber` if a bibliography were loaded) repeatedly until cross-references stabilise, and drops the PDF alongside the `.tex`.

## What `.latexmkrc` locks down

Four settings, all in [latex/.latexmkrc](latex/.latexmkrc):

| Setting | Value | Effect |
|:---|:---|:---|
| `$pdf_mode` | `4` | Engine = lualatex (Unicode-native, modern fonts, big memory). |
| `$lualatex` | `lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S` | SyncTeX for editor↔PDF jumps; never stops for prompts; error lines tagged with `file:line`. |
| `$bibtex_use` | `2` | Use `biber` when a `biblatex` bibliography is loaded. None are loaded today. |
| `$aux_dir` / `$out_dir` | `build` / `.` | Aux files (`.aux`, `.log`, `.fls`, `.fdb_latexmk`, `.out`) land in [latex/build/](latex/build/) (gitignored); the final PDF and `.synctex.gz` are moved back to [latex/](latex/). |

## Where the artifacts go

After one successful build:

```text
latex/
├── recommenders_v2.tex             # source (you edit)
├── recommenders_v2.pdf             # final output — committed to git
├── recommenders_v2.synctex.gz      # editor↔PDF position map
└── build/                          # aux / log / fls / out — gitignored
```

When a build fails, the truth is in `build/<jobname>.log`. Errors there are prefixed `file:line:` thanks to `-file-line-error`.

## Macros

Each `.tex` source defines its own macros inline in the preamble — there is no shared `macros.sty`. Keeps every file self-describing: the `\newcommand` definitions sit alongside the `\usepackage` calls that enable them.

Currently only [latex/recommenders_commented.tex](latex/recommenders_commented.tex) defines anything: two drafting-comment commands (`\ignacio{...}` in blue, `\michael{...}` in red), used for the margin annotations. They depend on `xcolor` being loaded earlier in the preamble. [latex/recommenders_v2.tex](latex/recommenders_v2.tex) defines no macros — it uses none.

When the paper grows a macro that both `.tex` sources need, add the same `\newcommand` to both preambles. If that ever becomes painful, factor it back into a local `macros.sty` then.

## Common operations

```bash
# Clean rebuild from scratch (drops everything in build/ first):
latexmk -C

# Watch the source and recompile on every save (preview workflow):
latexmk -pvc recommenders_v2.tex

# Build silently, surfacing only warnings/errors:
latexmk recommenders_v2.tex 2>&1 | grep -E "(Warning|Error|!)"
```

## Adding a bibliography (when the paper needs one)

Currently neither `.tex` source loads a bibliography. To wire one up:

1. Drop a `.bib` file into [latex/](latex/) (e.g. `latex/references.bib`).
2. In the preamble of the `.tex` source, add:

   ```latex
   \usepackage[backend=biber, style=authoryear]{biblatex}
   \addbibresource{references.bib}
   ```

3. At the end of the document, add `\printbibliography`.
4. Cite inline with `\cite{key}`, `\parencite{key}`, etc.

`$bibtex_use = 2` is already set, so `latexmk` will call `biber` automatically on the next build.

## Troubleshooting

| Symptom | Likely cause | Fix |
|:---|:---|:---|
| `! Undefined control sequence. \ignacio` | The `.tex` file is missing its inline `\newcommand{\ignacio}{...}` definition (or the file was edited to remove it). | Restore the `\newcommand` in the preamble — see [recommenders_commented.tex](latex/recommenders_commented.tex). |
| Cross-references show as `??` in the PDF. | Single-pass build before refs stabilised. | Run `latexmk` again (it normally handles this automatically; if not, `latexmk -gg` forces a full rebuild). |
| Build leaves stale `build/*.aux` after a rename. | `latexmk` doesn't garbage-collect aux for removed jobs. | `latexmk -C` to clean. |
| `lualatex` runs slow. | Expected — lualatex is heavier than pdflatex. | For draft cycles, `latexmk -pvc` recompiles only on change. To switch engine, set `$pdf_mode = 1` (pdflatex) in `.latexmkrc`. |
