{ pkgs, osConfig, lib, ... }:
let
  # ── Content creation ──────────────────────────────────────────────────
  # Options declared in modules/system/apps/content-creation.nix
  ccPluginDefaults = {
    vkcapture.enable               = true;
    pipewireAudioCapture.enable    = true;
    backgroundRemoval.enable       = false;
    moveTransition.enable          = false;
    aitumMultistream.enable        = false;
    gstreamer.enable               = false;
    compositeBlur.enable           = false;
    advancedSceneSwitcher.enable   = false;
    inputOverlay.enable            = false;
    waveform.enable                = false;
  };
  ccCfg = osConfig.roudix.contentCreation or {
    enable = true;
    obs = { enable = true; plugins = ccPluginDefaults; };
    videoEditor = "kdenlive";
    streaming.chatterino.enable = false;
  };
  ccEnabled = ccCfg.enable or true;

  obsPluginCfg = (ccCfg.obs.plugins or {});
  obsPluginMap = with pkgs.obs-studio-plugins; {
    vkcapture               = obs-vkcapture;
    pipewireAudioCapture    = obs-pipewire-audio-capture;
    backgroundRemoval       = obs-backgroundremoval;
    moveTransition          = obs-move-transition;
    aitumMultistream        = obs-aitum-multistream;
    gstreamer               = obs-gstreamer;
    compositeBlur           = obs-composite-blur;
    advancedSceneSwitcher   = advanced-scene-switcher;
    inputOverlay            = input-overlay;
    waveform                = waveform;
  };

  obsPackage = pkgs.wrapOBS {
    plugins = lib.filter (p: p != null) (lib.mapAttrsToList
      (name: pkg: if ((obsPluginCfg.${name} or { enable = false; }).enable or false) then pkg else null)
      obsPluginMap);
  };

  videoEditorType = ccCfg.videoEditor or "kdenlive";
  videoEditorPackage = {
    kdenlive                = pkgs.kdePackages.kdenlive;
    davinci-resolve          = pkgs.davinci-resolve;
    davinci-resolve-studio   = pkgs.davinci-resolve-studio;
    shotcut                    = pkgs.shotcut;
    none                       = null;
  }.${videoEditorType};
in
{
  home.packages =
    # OBS Studio, with plugins picked individually (roudix.contentCreation.obs.plugins)
    lib.optional (ccEnabled && (ccCfg.obs.enable or true)) obsPackage
    # Chosen video editor (roudix.contentCreation.videoEditor)
    ++ lib.optional (ccEnabled && videoEditorPackage != null) videoEditorPackage
    # Client de chat Twitch (roudix.contentCreation.streaming.chatterino.enable)
    ++ lib.optional (ccEnabled && (ccCfg.streaming.chatterino.enable or false)) pkgs.chatterino2;
}
