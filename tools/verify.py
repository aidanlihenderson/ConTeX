#!/usr/bin/env python3
"""Verify library creation helpers, configuration, PDFs, logs, and examples locally."""
from pathlib import Path
from datetime import datetime
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,help='New directory for results (must not exist)')
    ap.add_argument('--render',action='store_true',help='Render every successful PDF page with pdftoppm')
    ap.add_argument('--require-demos',action='store_true',help='Require all local demonstration files and inputs')
    ap.add_argument('--font-cache', type=Path, metavar='DIR',
                    help='Reuse a LuaLaTeX font cache from the same TeX and font installation')
    args=ap.parse_args()
    templates=[*ROOT.glob('templates/*/main.tex'),ROOT/'variants/language-arabic/main.tex']
    if args.require_demos:
        required=[p.parent/name for p in templates for name in ('demonstration.tex','examples/body.tex')]
        missing=[str(p.relative_to(ROOT)) for p in required if not p.is_file()]
        if missing:raise RuntimeError('Required demonstrations missing: '+', '.join(missing))
    out=args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='contex-verify-'))
    if args.output:out.mkdir(parents=True,exist_ok=False)
    font_cache = args.font_cache.resolve() if args.font_cache else out / 'cache'
    font_cache.mkdir(parents=True, exist_ok=args.font_cache is not None)
    env = os.environ.copy()
    env.update(TZ='America/Chicago', PYTHONDONTWRITEBYTECODE='1',
               TEXMFVAR=str(font_cache), TEXMFCACHE=str(font_cache))
    env.pop('TEXINPUTS', None)
    results=[];checks=[];skipped=[];start=time.time()
    def run(argv,cwd=ROOT,check=True):
        p=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if check and p.returncode:raise RuntimeError('Command failed: '+repr(argv)+'\n'+p.stdout[-6000:])
        return p
    for command in ('zsh','latexmk','lualatex','bibtex','pdfinfo','pdftotext'):
        if not shutil.which(command):raise RuntimeError('Required command missing: '+command)
    if args.render and not shutil.which('pdftoppm'):raise RuntimeError('--render requires pdftoppm')
    run([sys.executable,str(ROOT/'tools/make-lorenz.py'),'--check'])
    checks.append('Deterministic finite bounded Lorenz dataset matches generator')
    run(['zsh','-n',str(ROOT/'shell/latex.sh')])
    if (ROOT/'shell/latex.zsh').is_file():run(['zsh','-n',str(ROOT/'shell/latex.zsh')])
    checks.append('Shell syntax')
    if list(ROOT.rglob('metadata.tex')):raise AssertionError('Unexpected metadata.tex remains')
    # Generate projects through the real shell helpers; stub only the editor.
    env.update(LATEX_HOME=str(out/'projects'),LATEX_LIBRARY=str(ROOT))
    def shell(code,check=True,cwd=None):
        return run(['zsh','-f','-c','source "$LATEX_LIBRARY/shell/latex.sh"\nnvim() { print -r -- "$#:$*"; }\n'+code],cwd or out,check)
    profiles=[('e','Engineering Notes'),('m','Mathematics Notes'),('p','Programming Notes'),('l','Language Notes')]
    for profile,name in profiles:shell('newtex '+profile+' "'+name+'"')
    shell('newtex l "Arabic Notes" --arabic')
    projects=sorted((out/'projects').iterdir())
    stamp=run(['date','+%Y-%m-%d']).stdout.strip()
    for d in projects:
        text=(d/'main.tex').read_text()
        assert '\\date{'+stamp+'} % creation-date' in text
        assert 'twocolumn' in re.search(r'\\documentclass\[([^]]+)\]',text).group(1).split(',')
        assert not (d/'metadata.tex').exists()
        assert (d/'tex/core.sty').is_file()
        motif={'Engineering':'engineering','Programming':'programming','Mathematics':'mathematics','Language':'phonetics','Arabic':'arabic'}[d.name.removesuffix(' Notes')]
        assert re.search(r'motif\s*=\s*\{'+motif+r'\}',text)
        assert (d/'tex/lorenz-xz.dat').read_bytes()==(ROOT/'shared/lorenz-xz.dat').read_bytes()
        template=ROOT/('variants/language-arabic' if d.name=='Arabic Notes' else 'templates/'+d.name.removesuffix(' Notes').lower())
        assert (d/'demonstration.tex').is_file()==(template/'demonstration.tex').is_file()
    legacy=out/'legacy-date-source.tex'
    legacy.write_text('  date = {2000-01-01}, % creation-date\n')
    shell('_contex_write_starter legacy-date-source.tex legacy-date-target.tex')
    assert (out/'legacy-date-target.tex').read_text()=='  date = {'+stamp+'}, % creation-date\n'
    checks.append('All five real creation paths; spaces in names; fixed creation dates')
    original=(projects[0]/'main.tex').read_bytes()
    assert shell('newtex e "'+projects[0].name+'"',False).returncode
    assert (projects[0]/'main.tex').read_bytes()==original
    before=set((out/'projects').iterdir())
    for code in ('newtex r Retired','newtex x Bad','newtex e "../Bad"','newtex e Bad --arabic','newtex l Bad --unknown','newtex l Bad --arabic extra'):
        assert shell(code,False).returncode,code
    assert set((out/'projects').iterdir())==before
    shell('newtex l "Trailing dot."')
    checks.append('Existing-project preservation; invalid names/profiles/flags; trailing-dot name')
    notes = out / 'existing-notes'
    notes.mkdir()
    assert shell('tex missing', False, notes).returncode
    assert shell('tex missing --arabic', False, notes).returncode
    assert not list(notes.iterdir())
    existing = notes / 'quick notes.tex'
    original_note = r'\date{2000-01-01}' + '\n'
    existing.write_text(original_note)
    for code in ('tex "quick notes"', 'tex "quick notes.tex"', 'tex "quick notes" --arabic'):
        assert shell(code, cwd=notes).stdout.strip() == '1:quick notes.tex'
        assert existing.read_text() == original_note
    assert shell('tex "quick notes" --unknown', False, notes).returncode
    (notes / 'directory.tex').mkdir()
    (notes / 'link.tex').symlink_to(existing)
    assert shell('tex directory', False, notes).returncode
    assert shell('tex link', False, notes).returncode
    # A project destination link, including a dangling link, must also be refused.
    (out/'projects/Linked').symlink_to(out/'absent')
    assert shell('newtex e Linked',False).returncode
    assert shell('LATEX_LIBRARY="$LATEX_HOME/missing"; newtex e Missing',False).returncode
    checks.append('tex opens existing files unchanged and refuses missing files, directories, links and invalid flags')
    def build(d,entry,label,expected=None,engine=None):
        argv=engine or ['latexmk','-lualatex','-outdir=build','-halt-on-error',entry]
        p=run(argv,d,False);logfile=out/(re.sub('[^A-Za-z0-9_-]','-',label)+'.txt');logfile.write_text(p.stdout)
        logpath=d/'build'/(Path(entry).stem+'.log')
        log=logpath.read_text(errors='replace') if logpath.exists() else p.stdout
        if expected:
            assert p.returncode and expected in log, (label,p.stdout[-3000:]);checks.append(label);return
        if p.returncode:raise RuntimeError(label+' failed: '+str(logfile)+'\n'+p.stdout[-3000:])
        issues=[s for s in log.splitlines() if re.search(r'Warning:|^\s*warning\b|Overfull|Underfull|Missing character|Undefined control sequence|undefined references|undefined citations',s,re.I)]
        if issues:raise RuntimeError(label+' log issues:\n'+'\n'.join(issues))
        pdf=d/'build'/(Path(entry).stem+'.pdf'); info=run(['pdfinfo',str(pdf)]).stdout
        assert pdf.is_file()
        cover=run(['pdftotext','-f','1','-l','1',str(pdf),'-']).stdout
        assert '28' in cover and '10' in cover, (label,'Lorenz parameters missing')
        result={'label':label,'pdf':str(pdf),'pages':int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1)),'warnings':issues}
        results.append(result)
        if args.render:
            preview=out/'renders'/re.sub('[^A-Za-z0-9_-]','-',label);preview.mkdir(parents=True)
            run(['pdftoppm','-scale-to','1100','-png',str(pdf),str(preview/'page')])
        print('PASS',label,flush=True)
        return info
    for d in projects:
        build(d,'main.tex',d.name+' starter',engine=['latexmk','-halt-on-error','main.tex'])
        if (d/'demonstration.tex').is_file():
            build(d,'demonstration.tex',d.name+' demonstration',
                  engine=['latexmk','-halt-on-error','demonstration.tex'])
        else:skipped.append(d.name+' demonstration')
        fls=(d/'build/main.fls').read_text()
        excluded=['circuitikz.sty','pgfplots.sty','listings.sty','natbib.sty','algorithm.sty']
        assert not any('/'+name in fls for name in excluded),(d,'Starter unexpectedly loaded optional modules')
    checks.append('Minimal starter dependency audit')
    fixtures=out/'fixtures';fixtures.mkdir();shutil.copytree(ROOT/'shared',fixtures/'tex')
    pre='\\documentclass[11pt,twocolumn]{article}\n\\usepackage{tex/core}\n\\usepackage{tex/links}\n'
    def fixture(name,content,expected=None):
        (fixtures/(name+'.tex')).write_text(content)
        return build(fixtures,name+'.tex',name,expected)
    info=fixture('late-setup',pre+r'''
\projectsetup{title={Initial title},author={Initial author},date={2001-02-03}}
\projectsetup{title={Final title},author={Final author},subtitle={A section description},short-title={Final}}
\begin{document}\makeprojecttitle\section{Notes}Configuration test.\end{document}
''')
    assert 'Title:           Final title' in info and 'Author:          Final author' in info
    checks.append('PDF title/author use final setup after links; repeatable setup')
    fixture('minimal-optional-fields',pre+r'\projectsetup{title={A Minimal Note},subtitle={   }}\begin{document}\makeprojecttitle Body.\end{document}')
    fixture('general-info',pre+r'\projectsetup{title={Custom Information},date={1999-01-01},general-info={Lecture 3 - October 21, 2026}}\begin{document}\makeprojecttitle Body.\end{document}')
    text=run(['pdftotext','-f','1','-l','1',str(fixtures/'build/general-info.pdf'),'-']).stdout
    assert 'Lecture 3' in text and '1999-01-01' not in text
    assert '1999-01-01' in run(['pdftotext','-f','2',str(fixtures/'build/general-info.pdf'),'-']).stdout
    fixture('long-title',pre+r'\projectsetup{title={Fourier Analysis Techniques for Continuous-Time Signals and Linear Time-Invariant Systems},subtitle={Series representations, transforms, and applications},short-title={Fourier Analysis},author={Example Author},affiliation={Example Institution},course={Example Course},date={2026-10-21}}\begin{document}\makeprojecttitle\section{Notes}Long title test.\end{document}')
    for name,token in [('note-01','FIRST-NOTE'),('note-02','SECOND-NOTE')]:
        fixture(name,pre+'\\projectsetup{title={'+token+'},date={2026-10-21}}\\begin{document}\\makeprojecttitle '+token+'\\end{document}')
    for name,own,other in [('note-01','FIRST-NOTE','SECOND-NOTE'),('note-02','SECOND-NOTE','FIRST-NOTE')]:
        text=run(['pdftotext',str(fixtures/'build'/(name+'.pdf')),'-']).stdout
        assert own in text and other not in text
    checks.append('Independent main files produce distinct PDFs in shared build directory')
    info=fixture('missing-title',pre+r'\begin{document}\maketitle Body.\end{document}')
    assert 'Title:           Untitled notes' in info
    fixture('unknown-key',pre+r'\projectsetup{titel={Typo}}\begin{document}Body.\end{document}',"contex/project/titel")
    fixture('setup-in-body',pre+r'\projectsetup{title={Test}}\begin{document}\projectsetup{title={Too late}}\end{document}','Can be used only in preamble')
    # Engine mistakes should stop at the library's own actionable error.
    (fixtures/'wrong-engine.tex').write_text(pre+r'\projectsetup{title={Engine Check}}\begin{document}Body.\end{document}')
    build(fixtures,'wrong-engine.tex','wrong-engine','Use LuaLaTeX',
          ['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=build','wrong-engine.tex'])
    # Integration covers all optional features, bibliography, Unicode/Arabic, and notation.
    inter = out / 'integration'
    inter.mkdir()
    shutil.copytree(ROOT / 'shared', inter / 'tex')
    (inter / 'references.bib').write_text("""@article{shannon1948,
  author = {Shannon, Claude E.},
  title = {A Mathematical Theory of Communication},
  journal = {The Bell System Technical Journal},
  year = {1948}
}
""")
    modules=['core','math','theorems','diagrams','plots','engineering','code','algorithms','bibliography','language','arabic','links']
    content='\\documentclass[twocolumn]{article}\n'+''.join('\\usepackage{tex/'+m+'}\n' for m in modules)+r'''
\projectsetup{title={Optional Module Integration},short-title={Integration}}
\begin{document}\makeprojecttitle
\begin{notebox}{Note}This note uses the default green accent.\end{notebox}
\begin{notebox}[NoteRed]{Warning}This warning uses the optional red accent.\end{notebox}
\section{Notation}\label{sec:test}
\begin{theorem}For $x\in\R$, $\abs{x}\ge0$.\end{theorem}
\begin{proof}By definition.\end{proof}
$\norm*{\vect{x}}_2$, $\coloneqq$, $\overbracket{a+b}$.
\qty{1}{\kilo\ohm}. \arabictext{كِتَاب} \phonemic{kitaːb}.
\begin{arabicparagraph}هٰذَا كِتَابٌ. \phonemic{kitaːb}.\end{arabicparagraph}
\begin{lingexample}An example.\end{lingexample}
\cref{sec:test}; \citep{shannon1948}.\par
\begin{tikzpicture}\node[block] {Block};\end{tikzpicture}\par
\begin{circuitikz}\draw (0,0) to[R,l=$R$] (2,0);\end{circuitikz}\par
\begin{tikztimingtable}clk & 4{C} \\\end{tikztimingtable}\par
\begin{tikzpicture}\begin{axis}[width=5cm,height=4cm,domain=0:1]\addplot{x};\end{axis}\end{tikzpicture}\par
\begin{algorithm}\caption{Example}\begin{algorithmic}\State $x\gets1$\end{algorithmic}\end{algorithm}
'''
    for language,code in [('Python','x = 1'),('C','int x = 1;'),('C++','int x = 1;'),('VHDL',"q <= '1';"),('Verilog',"assign q = 1'b1;"),('SystemVerilog',"logic q;"),('Rust','let x = 1;'),('RiscV','addi t0, zero, 1')]:
        content+='\\begin{lstlisting}[language='+language+']\n'+code+'\n\\end{lstlisting}\n'
    content+='\\printprojectbibliography\n\\end{document}\n';(inter/'main.tex').write_text(content)
    build(inter,'main.tex','all optional modules')
    test=run([sys.executable,'-B','code/test_search.py'],out/'projects/Programming Notes');checks.append(test.stdout.strip())

    # Verify the shared title/running system with complete and omitted fields.
    def title_body():
        return r'''
\begin{document}\typeout{CONTEX-MOTIF=\ProjectMotif}\maketitle
\makeatletter
\if@twocolumn\typeout{CONTEX-TWOCOLUMN=YES}\else\errmessage{Two-column mode lost after title}\fi
\makeatother
\section{First section}Content after the cover.
\newpage\section{Next column}Content after a column break.
\clearpage\section{Next page}Content after a page break.\thispagestyle{plain}
\end{document}
'''
    motifs={'Engineering Notes':'engineering','Programming Notes':'programming',
            'Mathematics Notes':'mathematics',
            'Language Notes':'phonetics','Arabic Notes':'arabic'}
    for d in projects:
        preamble=(d/'main.tex').read_text().split(r'\title{',1)[0]
        preamble+='\\projectsetup{motif={'+motifs[d.name]+'}}\n'
        title='Complete '+d.name
        if d.name=='Arabic Notes':title=r'Arabic \arabictext{اللغة} and \phonemic{luɣa}'
        fields='\\title{'+title+'}\n\\subtitle{Models and observations}\n\\author{Example Author}\n\\date{2026-11-08}\n'
        fields+='\\projectsetup{short-title={Complete '+d.name+'},motif={'+motifs[d.name]+'}}\n'
        (d/'verify-complete.tex').write_text(preamble+fields+title_body())
        build(d,'verify-complete.tex',d.name+' complete title')
        log=(d/'build/verify-complete.log').read_text()
        assert 'CONTEX-TWOCOLUMN=YES' in log
        assert 'CONTEX-MOTIF='+motifs[d.name] in log
        missing='\\title{Minimal '+d.name+'}\n'
        (d/'verify-missing.tex').write_text(preamble+missing+title_body())
        build(d,'verify-missing.tex',d.name+' missing fields')
        assert 'CONTEX-MOTIF='+motifs[d.name] in (d/'build/verify-missing.log').read_text()
        text=run(['pdftotext',str(d/'build/verify-missing.pdf'),'-']).stdout
        assert 'Example Author' not in text and '2026-11-08' not in text
    checks.append('Complete/missing standard fields and two-column restoration in every profile')
    fixture('explicit-no-motif',pre+r'\projectsetup{motif={engineering}}\projectsetup{motif={none}}\begin{document}\typeout{CONTEX-MOTIF=\ProjectMotif}\maketitle Body.\end{document}')
    assert 'CONTEX-MOTIF=none' in (fixtures/'build/explicit-no-motif.log').read_text()
    fixture('research-cover-motif',pre+r'\title{Selected motif}\projectsetup{motif={research}}\begin{document}\typeout{CONTEX-MOTIF=\ProjectMotif}\maketitle\ConTeXSpiralArtwork\end{document}')
    assert 'CONTEX-MOTIF=research' in (fixtures/'build/research-cover-motif.log').read_text()
    checks.append('Default motifs, explicit none, research cover motif and legacy artwork alias')
    chapter=pre.replace('{article}','{report}')+r'''
\title{Chapter style check}\subtitle{Running matter on plain pages}\author{Example Author}\date{2026-11-08}
\begin{document}\maketitle\chapter{First chapter}Chapter-start content.
\newpage Second column.\clearpage\chapter{Second chapter}Next chapter.\end{document}
'''
    fixture('chapter-style',chapter)
    fixture('printing-off',pre+r'\ConTeXBackgroundOff\title{Printing check}\begin{document}\maketitle Body.\end{document}')
    info=fixture('mixed-title-interface',pre+r'\title{First title}\projectsetup{title={Legacy title},author={Legacy author}}\title{Canonical title}\author{Canonical author}\begin{document}\maketitle\ProjectTitle.\end{document}')
    assert 'Title:           Canonical title' in info and 'Author:          Canonical author' in info
    info=fixture('title-before-core',r'\documentclass[11pt,twocolumn]{article}\title{Early title}\author{Early author}\date{2026-11-08}\usepackage{tex/core}\usepackage{tex/links}\begin{document}\maketitle Body.\end{document}')
    assert 'Title:           Early title' in info and 'Author:          Early author' in info
    fixture('long-running-fields',pre+r'''\title{A long running title used to verify that measured header height accommodates multiple lines without truncating the text or colliding with the document body}
\author{A deliberately long example author field that wraps within its own footer area}
\date{A deliberately long date or session label that wraps within its own footer area}
\begin{document}\maketitle Body.\clearpage\thispagestyle{plain}Another page.\end{document}''')
    fixture('unknown-motif',pre+r'\projectsetup{motif={invalid}}\begin{document}Body.\end{document}','motif')
    checks.append('Canonical/legacy setters, pre-core metadata, missing-title fallback, chapter/plain pages, printing switch and long running fields')

    report={'library_version':(ROOT/'VERSION').read_text().strip(),'verified_at':datetime.now().astimezone().isoformat(),'seconds':round(time.time()-start,1),'font_cache':str(font_cache),'reusable_font_cache':args.font_cache is not None,'checks':checks,'successful_builds':len(results),'builds':results,'skipped_demonstrations':skipped,'rendered':args.render,'visual_review':'Not established by this script; inspect every rendered page separately.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for label in skipped:print('SKIP optional demonstration (not distributed):',label,flush=True)
    print('PASS:',len(results),'successful builds;',len(checks),'behavior checks. Results:',out,flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('FAIL:',exc,file=sys.stderr);sys.exit(1)
