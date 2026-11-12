# Research

Edit `main.tex` to set document information and packages. Write in
`sections/body.tex`. There is no separate metadata file.

```zsh
latexmk -halt-on-error main.tex
open -a Skim build/main.pdf
```

If the local feature reference is installed, build `demonstration.tex` and read
`examples/body.tex` (these are excluded from the public repository):

```zsh
latexmk -halt-on-error demonstration.tex
open -a Skim build/demonstration.pdf
```

The demonstration has its own title and content. It shares this project's styles,
code examples, figures, data, and bibliography. It does not change your notes.
Default starter modules: core, links. Load optional modules before links.
Dates are stamped once by the creation helper; edit them to the lecture date.
The template date is a fixed fallback when copying files manually.
