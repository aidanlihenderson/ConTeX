# Project-local settings; VimTeX uses the matching out_dir setting supplied.
$pdf_mode = 4; # LuaLaTeX
$out_dir = 'build';
$aux_dir = 'build';
$lualatex = 'lualatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
