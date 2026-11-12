# Source this file from zsh. Does not change PATH or editor plugins.
export LATEX_HOME="${LATEX_HOME:-$HOME/Desktop/Notes}"
export LATEX_LIBRARY="${LATEX_LIBRARY:-$HOME/Code/ConTeX}"
alias texhome='cd "$LATEX_HOME"'
unalias newtex tex 2>/dev/null || true

# Only the marked date line is stamped; existing documents are never restamped.
_contex_write_starter() {
    local source_file="$1" target_file="$2" line created_date
    created_date=$(command date +%Y-%m-%d) || return 1
    ( setopt LOCAL_OPTIONS NOCLOBBER
      while IFS= read -r line || [[ -n "$line" ]]; do
          if [[ "$line" == *'% creation-date'* ]]; then
              if [[ "$line" == *'\date{'* ]]; then
                  print -r -- "\\date{$created_date} % creation-date"
              else
                  print -r -- "  date = {$created_date}, % creation-date"
              fi
          else
              print -r -- "$line"
          fi
      done < "$source_file" > "$target_file" )
}

newtex() {
    local name_re='^[A-Za-z0-9][A-Za-z0-9._ -]*$'
    if (( $# < 2 || $# > 3 )); then
        print -r -- 'Usage: newtex m|e|r|p|l "Project Name" [--arabic]'; return 1
    fi
    if [[ ! "$2" =~ $name_re ]]; then
        print -r -- 'Use a name starting with a letter/digit; then letters, digits, spaces, dots, underscores or hyphens.'; return 1
    fi
    local use_arabic=0
    if (( $# == 3 )); then
        if [[ "$3" != --arabic || "$1" != l ]]; then
            print -r -- '--arabic is the only optional flag and is supported with newtex l only.'; return 1
        fi
        use_arabic=1
    fi
    local profile
    case "$1" in
        m) profile=mathematics ;;
        e) profile=engineering ;;
        r) profile=research ;;
        p) profile=programming ;;
        l) profile=language ;;
        *) print -r -- 'Choose m (math), e (engineering), r (research), p (programming), l (language).'; return 1 ;;
    esac
    local destination="$LATEX_HOME/$2"
    local source_dir="$LATEX_LIBRARY/templates/$profile"
    if (( use_arabic )); then
        source_dir="$LATEX_LIBRARY/variants/language-arabic"
    fi
    if [[ ! -f "$source_dir/main.tex" || ! -d "$LATEX_LIBRARY/shared" ]]; then
        print -r -- "Template library incomplete or missing: $LATEX_LIBRARY"; return 1
    fi
    if [[ -e "$destination" || -L "$destination" ]]; then
        print -r -- "Already exists; nothing copied: $destination"; return 1
    fi
    mkdir -p "$LATEX_HOME" || return 1
    mkdir "$destination" || return 1
    if ! cp -R "$source_dir/." "$destination/"; then
        print -r -- "Copy failed; inspect the partial new project: $destination"; return 1
    fi
    local entry
    for entry in main.tex demonstration.tex; do
        if [[ -f "$source_dir/$entry" ]]; then
            _contex_write_starter "$source_dir/$entry" "$destination/.$entry.new" || return 1
            mv "$destination/.$entry.new" "$destination/$entry" || return 1
        fi
    done
    mkdir "$destination/tex" "$destination/build" || return 1
    if ! cp -R "$LATEX_LIBRARY/shared/." "$destination/tex/"; then
        print -r -- "Module copy failed; inspect: $destination"; return 1
    fi
    print -r -- "Created $profile project: $destination"
    cd "$destination" || return 1
    nvim main.tex
}

tex() {
    local name_re='^[A-Za-z0-9][A-Za-z0-9._ -]*$'
    if (( $# < 1 || $# > 2 )); then
        print -r -- 'Usage: tex "filename" [--arabic]'; return 1
    fi
    if [[ ! "$1" =~ $name_re ]]; then
        print -r -- 'Use a simple filename in the current directory, starting with a letter or digit.'; return 1
    fi
    local use_arabic=0
    if (( $# == 2 )); then
        if [[ "$2" != --arabic ]]; then
            print -r -- 'The only optional flag is --arabic.'; return 1
        fi
        use_arabic=1
    fi
    local filename="$1"
    [[ "$filename" == *.tex ]] || filename="${filename}.tex"
    if [[ -L "$filename" || ( -e "$filename" && ! -f "$filename" ) ]]; then
        print -r -- "Not a regular non-link file: $filename"; return 1
    fi
    if [[ -e "$filename" ]]; then
        if (( use_arabic )); then
            print -r -- 'Opening existing file unchanged; --arabic selects a starter only for a new file.'
        fi
    else
        local template_file="$LATEX_LIBRARY/standalone/main.tex"
        if (( use_arabic )); then
            template_file="$LATEX_LIBRARY/standalone/arabic.tex"
        fi
        if [[ ! -f "$template_file" || ! -r "$template_file" ]]; then
            print -r -- "Standalone template not readable: $template_file"; return 1
        fi
        _contex_write_starter "$template_file" "$filename" || return 1
    fi
    nvim "$filename"
}
