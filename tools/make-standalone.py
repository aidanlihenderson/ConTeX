#!/usr/bin/env python3
"""Rebuild self-contained starters from shared modules; --check never writes."""
import argparse
from functools import cache
from pathlib import Path
from re import search
import sys

ROOT = Path(__file__).resolve().parents[1]
LORENZ_READER = 'plot file {tex/lorenz-xz.dat}'


@cache
def module(name):
    path = ROOT / 'shared' / f'{name}.sty'
    text = path.read_text()
    if name == 'title':
        if text.count(LORENZ_READER) != 1:
            sys.exit(f'{path}: expected exactly one Lorenz file plot')
        data = (ROOT / 'shared/lorenz-xz.dat').read_text().splitlines()
        coordinates = '\n'.join('(' + ','.join(row.split()) + ')' for row in data)
        text = text.replace(LORENZ_READER, 'plot coordinates {\n' + coordinates + '\n}')

    lines = []
    dependencies = []
    for line in text.splitlines():
        code = line.partition('%')[0].strip()
        if code.startswith(('\\NeedsTeXFormat', '\\ProvidesPackage')):
            continue
        if code.startswith(('\\RequirePackage', '\\usepackage')) and 'tex/' in code:
            command, _, argument = code.partition('{')
            package = argument.removesuffix('}')
            if (command.strip() != '\\RequirePackage' or not argument.endswith('}')
                    or not package.startswith('tex/') or not package[4:].isalpha()):
                sys.exit(f'{path}: unsupported local package declaration: {code}')
            dependencies.append(package[4:])
            continue
        lines.append(line)
    remaining_code = '\n'.join(line.partition('%')[0] for line in lines)
    if search(r'\\(?:RequirePackage(?:WithOptions)?|usepackage)\s*(?:\[[^]]*\]\s*)?\{[^{}]*tex/', remaining_code):
        sys.exit(f'{path}: unsupported local package declaration')
    return '\n'.join(lines) + '\n', tuple(dependencies)


def source(arabic=False, demo=False):
    names = ['fonts', 'title', 'core'] + (['language', 'arabic'] if arabic else ['math']) + ['links']
    content='% !TeX program = lualatex\n% Self-contained ConTeX snapshot. Regenerate with tools/make-standalone.py.\n\\documentclass[11pt,letterpaper,twocolumn]{article}\n'
    embedded = set()
    for name in names:
        text, dependencies = module(name)
        missing = sorted(set(dependencies) - embedded)
        if missing:
            sys.exit(f'{name}.sty: standalone requires earlier modules: {", ".join(missing)}')
        content += '\n% Shared module: ' + name + '\n' + text
        embedded.add(name)
    content+='\n'+('\\projectsetup{motif={arabic}}\n' if arabic else '')
    content+=r'''\title{Document Title}
\subtitle{}
\author{}
\date{2026-10-21} % creation-date
\projectsetup{
  affiliation = {},
  course = {},
  type = {Notes},
}
\begin{document}
\maketitle
'''
    if demo:
        original=ROOT/'standalone/examples'/('arabic-body.tex' if arabic else 'body.tex')
        content+=original.read_text()
    else:
        content+='\\section{Notes}\n\n% Write your notes here.\n'
    return content + '\\end{document}\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--require-demos', action='store_true', help='Fail if local demonstration inputs are absent')
    args = parser.parse_args()
    for name,arabic,demo in [('main',False,False),('arabic',True,False),('demonstration',False,True),('arabic-demonstration',True,True)]:
        path=ROOT/'standalone'/(name+'.tex')
        body=ROOT/'standalone/examples'/('arabic-body.tex' if arabic else 'body.tex')
        if demo and not body.is_file():
            if args.require_demos or path.exists():
                sys.exit('Missing demonstration input: '+str(body))
            print('SKIP optional demonstration (not distributed): '+name)
            continue
        text=source(arabic,demo)
        if args.check:
            if not path.exists() or path.read_text()!=text:sys.exit('Outdated standalone snapshot: '+str(path))
        else:path.write_text(text)
    print('Standalone snapshots match shared modules.' if args.check else 'Standalone snapshots regenerated.')


if __name__ == '__main__':
    main()
