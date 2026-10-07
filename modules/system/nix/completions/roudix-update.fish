# fish completion for roudix-update (the `update` alias wraps it, so it inherits this)
complete -c roudix-update -f
complete -c roudix-update -s i -l inputs -d 'Also bump flake inputs (all, or the names that follow)'
complete -c roudix-update -l no-inputs -d 'Do not bump flake inputs'
complete -c roudix-update -s b -l boot -d 'Apply on next boot instead of switching now'
complete -c roudix-update -s n -l dry -d 'Dry run: change nothing'
complete -c roudix-update -s c -l check -d 'Only report whether new commits are available'
complete -c roudix-update -l changes -d 'Show what the next-boot system changes vs the running one'
complete -c roudix-update -l log -d 'Show the log of the last run'
complete -c roudix-update -l no-pull -d 'Do not git pull the config'
complete -c roudix-update -l no-flatpak -d 'Do not update Flatpaks'
complete -c roudix-update -s h -l help -d 'Show help'
