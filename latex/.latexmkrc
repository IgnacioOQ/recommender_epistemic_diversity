# Self-contained latexmk config for this paper folder.
# Encodes the toolchain locks: lualatex + biber + aux/out split.

# Engine: 1=pdflatex, 4=lualatex, 5=xelatex
$pdf_mode = 4;

$lualatex = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# biber for biblatex bibliographies (kept for future use; no bibliography
# is currently loaded by either .tex source).
$bibtex_use = 2;

# Aux files into build/; final PDF lands alongside the .tex
$aux_dir = 'build';
$out_dir = '.';

# Self-contained: each .tex source defines whatever macros it needs inline
# (no shared macros.sty), and no external bibliography is loaded, so the
# default TeX search path is sufficient — no TEXINPUTS manipulation needed.
