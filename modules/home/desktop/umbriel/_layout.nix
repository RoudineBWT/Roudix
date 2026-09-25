## _layout.nix — Umbriel: [layout], [layout.scrolling], [layout.dwindle],
## [layout.master].
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

    # Renamed from `width_presets` (confirmed via docs.noctalia.dev/umbriel/layout/
    # as of writing: top-level [layout] key, not nested under scrolling/master).
    # Feeds window-cycle-primary-extent/-back AND window-cycle-secondary-extent/-back
    # (both extent axes share this one list — see _binds.nix).
    extent_presets = [ 0.33333 0.5 0.66667 ];

    master = {
      position = "left";        # main column on the left, stack on the right
      default_width_fraction = 0.55;
      new_on_top = true;        # a new window joins the top of the stack
      # new_becomes_master defaults to false (new windows join the stack,
      # not the master slot) — already what we want for the chat workspace.
    };

    dwindle = {
      # Keeps split directions fixed once created instead of re-adapting to
      # geometry changes — steadier regions on the Zed/Term workspaces
      # (both dwindle) when windows open/close.
      preserve_split = true;
    };

    scrolling = {
      # `direction` was removed: scroll direction now follows the output's
      # `workspace_axis` (docs.noctalia.dev/umbriel/outputs/#settings).
      # Default is "vertical" (workspaces stacked vertically), which makes
      # the scrolling strip horizontal — the niri-style behavior we want —
      # so no output override is needed here.
      #
      # Renamed from `default_width_fraction` (confirmed via
      # docs.noctalia.dev/umbriel/layout/: scrolling-specific move, distinct
      # from the still-valid `layout.master.default_width_fraction` above).
      # Matches the packaged config's own default.
      default_extent_fraction = 0.5;
      center_underfull_strip = true;
      # `expand_single_column` still doesn't exist in the current docs —
      # confirmed gone, not just renamed. Left out.
      #
      # `center_focused` is a string enum, not a bool ("never" | "always" |
      # "on_overflow" — docs.noctalia.dev/umbriel/layout/), so the old
      # `= true` would have been rejected anyway. "on_overflow" is the
      # closest match to niri's center-focused-column behavior: only
      # recenters once the strip overflows the viewport.
      center_focused = "on_overflow";
    };
  };
  };
}
