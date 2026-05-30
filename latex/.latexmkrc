# Self-contained latexmk config for this paper folder.
# Encodes the toolchain locks: lualatex + biber + aux/out split.

# Engine: 1=pdflatex, 4=lualatex, 5=xelatex
$pdf_mode = 4;

$lualatex = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# biber for biblatex bibliographies (kept for future use; no bibliography
# is currently loaded by either .tex source).
$bibtex_use = 2;

# All build artifacts (aux, log, synctex, pdf) go to build/; only the final
# PDF is copied back to the latex/ root via $success_cmd, so the root stays
# limited to the .tex sources, their PDFs, and this config.
$aux_dir = 'build';
$out_dir = 'build';

# After a fully successful compile, copy the built PDF up to the latex/ root
# (%D is the built PDF path inside build/). This is what keeps main.pdf /
# main_backup.pdf sitting next to their .tex sources while everything else
# (synctex, log, aux) remains in build/.
$success_cmd = 'cp %D .';

# Self-contained: each .tex source defines whatever macros it needs inline
# (no shared macros.sty), and no external bibliography is loaded, so the
# default TeX search path is sufficient — no TEXINPUTS manipulation needed.
