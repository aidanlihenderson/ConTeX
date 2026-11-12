# ConTeX

LuaLaTeX styles and starters for technical and language notes.

Use LuaLaTeX and latexmk from TeX Live or MacTeX, with BibTeX for bibliographies.
The fonts are Libertinus Serif, TeX Gyre Heros, Latin Modern Mono, and Latin Modern
Math. Language notes use Charis SIL for IPA and Amiri for Arabic.

The shared styles use fontspec, mathtools, amsthm, unicode-math, TikZ, tcolorbox,
and hyperref with cleveref. Optional modules add PGFPlots, CircuitikZ, tikz-timing,
siunitx, listings, algorithm and algpseudocode, natbib, and Babel.

## Setup

Source the helper from zsh. Run these lines again in any open shell that points
to an earlier library location.

```zsh
export LATEX_LIBRARY="$HOME/Code/ConTeX"
source "$LATEX_LIBRARY/shell/latex.sh"

newtex e "Engineering Notes"
newtex l "Arabic Notes" --arabic
tex "Quick Notes"
tex "Arabic Notes" --arabic
```

`newtex` creates a project under `LATEX_HOME`, which defaults to
`$HOME/Desktop/Notes`. `tex` creates or opens a self-contained file in the current
directory. Both open the source in Neovim.

## Write and build

Set the title fields in the project’s `main.tex` and write in
`sections/body.tex`. In a standalone file, write directly below `\maketitle`.

```latex
\title{Fourier Analysis}
\subtitle{Series and transforms}
\author{Example Author}
\date{2026-11-10}

\begin{document}
\maketitle
\input{sections/body}
\end{document}
```

Build a project with `latexmk -halt-on-error main.tex` or a standalone file with
`latexmk -lualatex -outdir=build -halt-on-error "Quick Notes.tex"`.

Add `\ConTeXBackgroundOff` in the preamble to omit the page background for
printing. Topic starters select their cover motif. Use
`\projectsetup{motif={none}}` to hide it or choose `engineering`, `programming`,
`phonetics`, `arabic`, `mathematics`, or `research`. General standalone notes
default to `none`, and Arabic standalone notes default to `arabic`.

## Topics and environments

| Profile | Available features with the relevant modules |
|---|---|
| Mathematics (`m`) | `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `example`, `problem`, `remark`, `proof`, `solution` |
| Engineering (`e`) | `circuitikz`, `tikztimingtable`, SI units |
| Programming (`p`) | `lstlisting`, `algorithm`, `algorithmic` |
| Research (`r`) | `tikzpicture`, PGFPlots `axis`, BibTeX citations |
| Language (`l`) | `lingexample` and IPA commands |
| Arabic (`l --arabic`) | `arabicparagraph`, `lingexample`, inline Arabic and IPA |
| All profiles | `notebox` |

In projects, load `tex/core` first, any optional `tex/<name>` modules next, and
`tex/links` last.
