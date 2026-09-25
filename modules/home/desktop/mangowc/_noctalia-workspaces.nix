{ config, lib, osConfig, ... }:

let
  isMangoNoctalia =
    (osConfig.roudix.desktop.type or null) == "mangowc"
    && (osConfig.roudix.desktop.shell or "noctalia") == "noctalia";

  pluginId = "roudix/mango-workspaces";
  pluginDir = "noctalia/plugins/mango-workspaces";

  pluginToml = ''
    id = "${pluginId}"
    name = "Roudix Mango Workspaces"
    version = "1.0.0"
    plugin_api = 9
    author = "Roudix"
    license = "MIT"
    description = "Mango workspace glyphs matching the Roudix Niri layout, per monitor."

    [[widget]]
    id = "workspaces"
    entry = "workspaces.luau"
  '';

  workspacesLuau = ''
    -- Roudix Mango workspace widget for Noctalia v5.
    --
    -- DP-1 / Legion:
    --   1 = web, 2 = code, 3 = terminal, 4 = games, 5 = files
    --
    -- DP-3 / HKC:
    --   1 = chat, 2 = music, 3 = browser
    --
    -- Mango keeps numeric tags. This widget only changes their presentation
    -- and sends viewcrossmon so clicks always target this bar's output.

    local maps = {
      ["DP-1"] = {
        { "󰈹", "web" },
        { "", "code" },
        { "", "term" },
        { "󰊗", "games" },
        { "󰉋", "files" },
      },
      ["DP-3"] = {
        { "", "chat" },
        { "󰝚", "music" },
        { "", "browser" },
      },
    }

    local function isActive(tag)
      if type(tag) ~= "table" then
        return false
      end

      return tag.active == true
        or tag.focused == true
        or tag.selected == true
        or tag.viewed == true
    end

    local function findTag(tags, index)
      if type(tags) ~= "table" then
        return nil
      end

      local direct = tags[tostring(index)] or tags[index]
      if type(direct) == "table" then
        return direct
      end

      for _, value in ipairs(tags) do
        if type(value) == "table" then
          local id = value.id or value.index or value.tag
          if tonumber(id) == index then
            return value
          end
        end
      end

      return nil
    end

    local function switchWorkspace(output, index)
      -- Mango's IPC dispatcher accepts:
      --   viewcrossmon,<tag>,<monitor>
      noctalia.runAsync({
        "mmsg",
        "dispatch",
        "viewcrossmon," .. tostring(index) .. "," .. output,
      })
    end

    local function renderWorkspace(output, index, glyph, label, tags)
      local tag = findTag(tags, index)
      local active = isActive(tag)

      return ui.button({
        key = output .. "-" .. tostring(index),
        text = glyph,
        fontSize = 17,
        variant = active and "primary" or "ghost",
        controlSize = "sm",
        tooltip = tostring(index) .. " · " .. label,
        onClick = function()
          switchWorkspace(output, index)
        end,
      })
    end

    function update()
      local output = barWidget.outputName()
      local entries = output and maps[output]

      if entries == nil then
        barWidget.setVisible(false)
        return
      end

      barWidget.setVisible(true)

      -- The compositor state is read asynchronously. The visual mapping itself
      -- is output-local and remains stable while mmsg answers.
      local tags = nil
      noctalia.runAsync(
        { "mmsg", "get", "tags", output },
        function(reply)
          if reply.exitCode == 0 then
            local decoded = noctalia.json.decode(reply.stdout)
            if decoded ~= nil then
              tags = decoded
            end
          end

          local children = {}

          for index, entry in ipairs(entries) do
            children[#children + 1] =
              renderWorkspace(output, index, entry[1], entry[2], tags)
          end

          barWidget.render(
            ui.row({
              gap = 2,
              align = "center",
            }, children)
          )
        end,
        1000
      )
    end

    noctalia.setUpdateInterval(250)
  '';
in
lib.mkIf isMangoNoctalia {
  # Noctalia v5 discovers plugins from:
  #   $XDG_DATA_HOME/noctalia/plugins/<plugin>
  #
  # The plugin is intentionally installed declaratively, but its bar placement
  # remains a Noctalia runtime choice: add
  #   roudix/mango-workspaces:workspaces
  # to the bar where you currently use "workspaces".
  xdg.dataFile."${pluginDir}/plugin.toml".text = pluginToml;
  xdg.dataFile."${pluginDir}/workspaces.luau".text = workspacesLuau;
}
