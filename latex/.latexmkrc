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

# Self-contained: macros.sty lives in this directory (./macros.sty), so the
# default TeX search path (current directory first) resolves \usepackage{macros}
# without any TEXINPUTS manipulation. No external bibliography is used either.
