---
status: active
type: explanation
description: How to compile this paper's .tex sources to PDF via latexmk — what the toolchain pieces are, what .latexmkrc locks down, where the artifacts land, and the common commands.
label: [reference, human]
injection: informational
volatility: stable
scope: project-specific
last_checked: '2026-05-30'
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
latexmk                  # build every .tex in cwd (main.tex + main_backup.tex)
latexmk main.tex         # build just the working paper
latexmk main_backup.tex  # build the backup copy
```

`latexmk` reads [latex/.latexmkrc](latex/.latexmkrc), runs `lualatex` (and `biber` if a bibliography were loaded) repeatedly until cross-references stabilise. All build artifacts land in `build/`; a post-build `$success_cmd` then copies just the finished PDF back alongside the `.tex` (see below).

## What `.latexmkrc` locks down

Five settings, all in [latex/.latexmkrc](latex/.latexmkrc):

| Setting | Value | Effect |
|:---|:---|:---|
| `$pdf_mode` | `4` | Engine = lualatex (Unicode-native, modern fonts, big memory). |
| `$lualatex` | `lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S` | SyncTeX for editor↔PDF jumps; never stops for prompts; error lines tagged with `file:line`. |
| `$bibtex_use` | `2` | Use `biber` when a `biblatex` bibliography is loaded. None are loaded today. |
| `$aux_dir` / `$out_dir` | `build` / `build` | **Every** build artifact — `.aux`, `.log`, `.fls`, `.fdb_latexmk`, `.out`, `.synctex.gz`, and the PDF — is written under [latex/build/](latex/build/) (gitignored). |
| `$success_cmd` | `cp %D .` | After a fully successful compile, copies just the finished PDF (`%D`) from `build/` back to [latex/](latex/), so the root keeps only the `.tex` sources, their PDFs, and `.latexmkrc`. |

## Where the artifacts go

After one successful build:

```text
latex/
├── main.tex            # source you edit
├── main.pdf            # final output — committed to git
├── main_backup.tex     # backup copy of main.tex
├── main_backup.pdf     # the backup's compiled PDF
├── .latexmkrc          # toolchain lock
└── build/              # everything else: aux, log, fls, out, synctex, intermediate PDF — gitignored
```

When a build fails, the truth is in `build/<jobname>.log`. Errors there are prefixed `file:line:` thanks to `-file-line-error`.

## Macros

Each `.tex` source defines its own macros inline in the preamble — there is no shared `macros.sty`. Keeps every file self-describing: the `\newcommand` definitions sit alongside the `\usepackage` calls that enable them.

Currently [latex/main.tex](latex/main.tex) defines two drafting-comment commands — `\ignacio{...}` (blue) and `\michael{...}` (red) — used for the inline annotations. They depend on `xcolor` being loaded earlier in the preamble. `main_backup.tex`, being a copy of `main.tex`, carries the same definitions.

When the paper grows a macro it needs, add the `\newcommand` to the `main.tex` preamble (and refresh `main_backup.tex` from it). If macro management ever becomes painful, factor them into a local `macros.sty` then.

## Common operations

```bash
# Clean rebuild from scratch (drops everything in build/ first):
latexmk -C

# Watch the source and recompile on every save (preview workflow):
latexmk -pvc main.tex

# Build silently, surfacing only warnings/errors:
latexmk main.tex 2>&1 | grep -E "(Warning|Error|!)"
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
| `! Undefined control sequence. \ignacio` | The `.tex` file is missing its inline `\newcommand{\ignacio}{...}` definition (or the file was edited to remove it). | Restore the `\newcommand` in the preamble — see [main.tex](latex/main.tex). |
| Cross-references show as `??` in the PDF. | Single-pass build before refs stabilised. | Run `latexmk` again (it normally handles this automatically; if not, `latexmk -gg` forces a full rebuild). |
| Build leaves stale `build/*.aux` after a rename. | `latexmk` doesn't garbage-collect aux for removed jobs. | `latexmk -C` to clean. |
| `lualatex` runs slow. | Expected — lualatex is heavier than pdflatex. | For draft cycles, `latexmk -pvc` recompiles only on change. To switch engine, set `$pdf_mode = 1` (pdflatex) in `.latexmkrc`. |
