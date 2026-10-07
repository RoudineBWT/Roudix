# bash completion for roudix-update and its alias `update`
_roudix_update() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  mapfile -t COMPREPLY < <(compgen -W \
    '--inputs -i --no-inputs --boot -b --dry -n --check -c --changes --log --no-pull --no-flatpak --help -h' \
    -- "$cur")
}
complete -F _roudix_update roudix-update update
