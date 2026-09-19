## _layout.nix — Umbriel: [layout], [layout.scrolling].
##
## Docs: https://docs.noctalia.dev/umbriel/layout/
{ ... }:
{
  programs.umbriel.settings = {
  layout = {
    # layout.mode in a [[workspace]] rule accepts "scrolling", "dwindle" and
    # "master" directly (docs.noctalia.dev/umbriel/workspaces/#available-fields).
    # The global mode stays "scrolling"; chat/games get an explicit
    # layout.mode = "master" override per-workspace in _output.nix.
    mode = "scrolling";
    gap = 9; # niri: layout { gaps 9 }

    # ⚠ width_presets is rejected by `umbriel validate` ("unknown key
    # layout.width_presets") even though it's still documented as of this
    # writing. The window-cycle-width action it fed has also been renamed
    # to window-cycle-primary-extent/-back (see _binds.nix), so the key
    # likely moved too (maybe `primary_extent_presets`) but the exact name
    # isn't confirmed. Check `examples/config.toml` next to your installed
    # umbriel binary (`readlink -f $(which umbriel)`, look for share/umbriel/)
    # or `umbriel msg --help` before re-enabling.
    # width_presets = [ 0.33333 0.5 0.66667 ];

    master = {
      position = "left";        # main column on the left, stack on the right
      default_width_fraction = 0.55;
      new_on_top = true;        # a new window joins the top of the stack
    };

    scrolling = {
      # `direction` was removed: scroll direction now follows the output's
      # `workspace_axis` (docs.noctalia.dev/umbriel/outputs/#settings).
      # Default is "vertical" (workspaces stacked vertically), which makes
      # the scrolling strip horizontal — the niri-style behavior we want —
      # so no output override is needed here.
      # ⚠ `default_width_fraction` is rejected here ("unknown key
      # layout.scrolling.default_width_fraction") even though it's still
      # documented and referenced by the Window Rules doc, and even though
      # the same key under [layout.master] above IS accepted — so this
      # looks like a scrolling-specific move/rename rather than a global
      # one (possibly to a per-output setting; the Layout doc mentions an
      # "output-specific default" for the initial scrolling width). Left
      # commented until the exact name is confirmed; new columns keep
      # whatever size the client requests in the meantime.
      # default_width_fraction = 0.5;
      center_underfull_strip = true;
      # ⚠ `expand_single_column` is rejected by `umbriel validate`
      # ("unknown key layout.scrolling.expand_single_column") and isn't
      # confirmed under another name in the current docs. Umbriel's keys
      # move fast between versions — re-test later if you want this
      # behavior (a single column filling the viewport).
      # expand_single_column = true;
      #
      # ⚠ `center_focused` (partial niri center-focused-column equivalent)
      # has the same unconfirmed status. Left commented — decomment to
      # test, but check `umbriel validate` before reloading.
      # center_focused = true;
    };
  };
  };
}
