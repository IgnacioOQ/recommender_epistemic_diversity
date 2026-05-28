# Self-contained latexmk config for this paper folder (external to latex_repo).
# Encodes the toolchain locks: lualatex + biber + aux/out split.

# Engine: 1=pdflatex, 4=lualatex, 5=xelatex
$pdf_mode = 4;

$lualatex = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# biber for biblatex bibliographies
$bibtex_use = 2;

# Aux files into build/; final PDF lands alongside the .tex
$aux_dir = 'build';
$out_dir = '.';

# Prepend latex_repo/shared/ to TEXINPUTS/BIBINPUTS so \usepackage{macros}
# (which provides \ignacio{...} and other shared macros) and the shared
# bibliography resolve without the caller having to set them by hand.
# Trailing ':' preserves the TeX default search paths.
my $shared = $ENV{HOME} . '/Documents/VS Code/GitHub Repositories/latex_repo/shared';
$ENV{TEXINPUTS} = ".:${shared}:" . ($ENV{TEXINPUTS} // '');
$ENV{BIBINPUTS} = ".:${shared}/bibliography:" . ($ENV{BIBINPUTS} // '');
