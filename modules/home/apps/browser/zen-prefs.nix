# ── Zen Browser tweaks (user.js prefs) ────────────────────────────────────
# Imported by modules/home/apps/browser/browser.nix.
#
# Each category = { prefs = { name = value; }; locked = [ name … ]; }
#   prefs  — written to the profile's user.js (programs.zen-browser.profiles
#            .<n>.settings → user_pref(...)), re-applied on every launch.
#   locked — prefs that were `locked` in the original pref() snippet.
#            user.js cannot lock a pref, so they are ALSO pushed through
#            policies.json (`Preferences`, Status = "locked") by browser.nix,
#            for the prefixes Firefox's policy engine accepts.
#
# Categories map to roudix.zen.tweaks.* options (modules/system/apps/browser).
{

  # ── base — always applied when roudix.zen.tweaks.enable = true ─────
  base = {
    prefs = {
      "intl.locale.requested" = "";
      "spellchecker.dictionary_path" = "/run/current-system/sw/share/hunspell"; # /usr/share/hunspell does not exist on NixOS
      "browser.shell.checkDefaultBrowser" = false;
      "skipDefaultBrowserCheckOnFirstRun" = false;
      "extensions.autoDisableScopes" = 11;
      "widget.use-xdg-desktop-portal.file-picker" = 1;
    };
    locked = [
      "skipDefaultBrowserCheckOnFirstRun"
    ];
  };

  # ── performance — roudix.zen.tweaks.performance ────────────────────
  performance = {
    prefs = {
      "media.hardware-video-decoding.force-enabled" = true;
      "media.webrtc.hw.h264.enabled" = true;
      "media.gpu-process-decoder" = true;
      "browser.cache.disk.enable" = false;
      "browser.cache.memory.capacity" = 1048576;
      "gfx.canvas.accelerated.cache-items" = 32768;
      "gfx.canvas.accelerated.cache-size" = 4096;
      "gfx.content.skia-font-cache-size" = 80;
      "gfx.webrender.all" = true;
      "gfx.webrender.precache-shaders" = true;
      "gfx.webrender.program-binary-disk" = true;
      "layers.gpu-process.enabled" = true; # Use dedicated GPU process
      "javascript.options.baselinejit.threshold" = 50; # Lower JIT threshold
      "javascript.options.ion.threshold" = 500; # Lower Ion threshold
      "image.cache.size" = 10485760; # Increase decoded image cache size (10MB)
      "image.mem.decode_bytes_at_a_time" = 65536; # Increase image decode chunk size
      "image.mem.shared.unmap.min_expiration_ms" = 120000;
      "media.cache_readahead_limit" = 7200; # Increase media readahead
      "media.cache_resume_threshold" = 3600; # Increase media resume threshold
      "media.memory_cache_max_size" = 1048576; # Increase media memory cache (1GB)
      "media.memory_caches_combined_limit_kb" = 3145728; # Increase combined media caches limit (3GB)
      "network.buffer.cache.size" = 65535; # Network buffer size
      "network.ssl_tokens_cache_capacity" = 32768; # Increase SSL token cache
      "browser.tabs.unloadOnLowMemory" = true; # Unload unused tabs
      "content.notify.interval" = 100000; # page reflow timer, lower redrawn rendering timer, increases responsiveness but increase total load time
      "network.dnsCacheExpiration" = 3600; # Time DNS entries are cached in seconds.
      "network.http.max-connections" = 1800; # https://kb.mozillazine.org/Network.http.max-connections
      "network.http.max-persistent-connections-per-server" = 10; # https://kb.mozillazine.org/Network.http.max-persistent-connections-per-server
      "network.http.max-urgent-start-excessive-connections-per-host" = 5; # Number of connections that we can open beyond the standard parallelism limit defined by max-persistent-connections-per-server/-proxy to handle urgent-start marked requests
      "network.http.pacing.requests.enabled" = false; # Disable pacing requests
    };
    locked = [
    ];
  };

  # ── privacy — roudix.zen.tweaks.privacy (debloat + telemetry + hardening) ──
  privacy = {
    prefs = {
      "app.normandy.api_url" = "";
      "app.normandy.enabled" = false;
      "breakpad.reportURL" = "";
      "browser.contentanalysis.default_result" = 0;
      "browser.contentanalysis.enabled" = false;
      "browser.contentblocking.report.hide_vpn_banner" = true;
      "browser.contentblocking.report.lockwise.enabled" = false;
      "browser.contentblocking.report.mobile-android.url" = "";
      "browser.contentblocking.report.mobile-ios.url" = "";
      "browser.contentblocking.report.monitor.enabled" = false;
      "browser.contentblocking.report.proxy.enabled" = false;
      "browser.contentblocking.report.proxy_extension.url" = "";
      "browser.contentblocking.report.show_mobile_app" = false;
      "browser.contentblocking.report.vpn-android.url" = "";
      "browser.contentblocking.report.vpn-ios.url" = "";
      "browser.contentblocking.report.vpn-promo.url" = "";
      "browser.contentblocking.report.vpn.url" = "";
      "browser.crashReports.unsubmittedCheck.autoSubmit2" = false;
      "browser.dataFeatureRecommendations.enabled" = false;
      "browser.discovery.enabled" = false;
      "browser.ipProtection.enabled" = false;
      "browser.ipProtection.guardian.endpoint" = "";
      "browser.ipProtection.variant" = "";
      "browser.ml.chat.enabled" = false;
      "browser.ml.chat.page" = ""; # was false in the source snippet; this pref is a string
      "browser.ml.enable" = false;
      "browser.ml.linkPreview.enabled" = false;
      "browser.newtabpage.activity-stream.feeds.aboutpreferences" = false;
      "browser.newtabpage.activity-stream.feeds.adsfeed" = false;
      "browser.newtabpage.activity-stream.feeds.discoverystreamfeed" = false;
      "browser.newtabpage.activity-stream.feeds.places" = false;
      "browser.newtabpage.activity-stream.feeds.recommendationprovider" = false;
      "browser.newtabpage.activity-stream.feeds.system.topsites" = false;
      "browser.newtabpage.activity-stream.feeds.system.topstories" = false;
      "browser.newtabpage.activity-stream.feeds.topsites" = false;
      "browser.newtabpage.activity-stream.showSponsoredCheckboxes" = false;
      "browser.newtabpage.activity-stream.system.showSponsored" = false;
      "browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint" = ""; # was 0 in the source snippet; this pref is a string
      "browser.newtabpage.activity-stream.telemetry.ut.event" = false;
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.enabled" = false;
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.spocs.enabled" = false;
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.tiles.enabled" = false;
      "browser.newtabpage.activity-stream.unifiedAds.endpoint" = "";
      "browser.newtabpage.activity-stream.unifiedAds.spocs.enabled" = false;
      "browser.newtabpage.activity-stream.unifiedAds.tiles.enabled" = false;
      "browser.newtabpage.enabled" = false;
      "browser.places.interactions.enabled" = false;
      "browser.privatebrowsing.vpnpromourl" = "";
      "browser.promo.cookiebanners.enabled" = false;
      "browser.promo.focus.enabled" = false;
      "browser.promo.pin.enabled" = false;
      "browser.protections_panel.infoMessage.seen" = true;
      "browser.send_to_device_locales" = "";
      "browser.tabs.crashReporting.sendReport" = false;
      "browser.tabs.groups.smart.userEnabled" = false;
      "browser.uitour.enabled" = false;
      "browser.uitour.url" = "";
      "browser.urlbar.quicksuggest.enabled" = false;
      "browser.urlbar.suggest.addons" = false;
      "browser.urlbar.suggest.quicksuggest.fakespot" = false;
      "browser.urlbar.suggest.quicksuggest.nonsponsored" = false;
      "browser.urlbar.suggest.quicksuggest.sponsored" = false;
      "browser.urlbar.suggest.quicksuggest.topsites" = false;
      "browser.urlbar.suggest.trending" = false;
      "browser.vpn_promo.enabled" = false;
      "captivedetect.canonicalURL" = "";
      "cookiebanners.ui.desktop.showCallout" = false;
      "devtools.debugger.remote-enabled" = false;
      "dom.private-attribution.submission.enabled" = false;
      "dom.push.enabled" = false;
      "dom.security.unexpected_system_load_telemetry_enabled" = false;
      "extensions.abuseReport.enabled" = false;
      "extensions.blocklist.enabled" = false;
      "extensions.getAddons.showPane" = false;
      "extensions.htmlaboutaddons.recommendations.enabled" = false;
      "extensions.pocket.enabled" = false;
      "extensions.webcompat-reporter.enabled" = false;
      "media.gmp-gmpopenh264.autoupdate" = false;
      "signon.firefoxRelay.feature" = "disabled";
      "security.OCSP.enabled" = 0;
      "security.pki.crlite_mode" = 2;
      "security.remote_settings.crlite_filters.enabled" = true;
      "services.settings.poll_interval" = 300;
      "browser.newtabpage.activity-stream.feeds.telemetry" = false;
      "browser.newtabpage.activity-stream.showSponsored" = false;
      "browser.newtabpage.activity-stream.showSponsoredTopSites" = false;
      "browser.newtabpage.activity-stream.telemetry" = false;
      "browser.newtabpage.activity-stream.telemetry.ut.events" = false;
      "browser.newtabpage.activity-stream.trendingSearch.blockedAds" = "";
      "browser.newtabpage.activity-stream.trendingSearch.enabled" = false;
      "browser.newtabpage.activity-stream.trendingSearch.variant" = "";
      "browser.ping-centre.telemetry" = false;
      "browser.search.serpEventTelemetryCategorization.enabled" = false;
      "browser.search.serpEventTelemetryCategorization.regionEnabled" = false;
      "browser.search.update" = false;
      "browser.shopping.experience2023.enabled" = false;
      "browser.startup.homepage_override.mstone" = "ignore";
      "browser.urlbar.addons.featureGate" = false;
      "browser.urlbar.fakespot.featureGate" = false;
      "browser.urlbar.mdn.featureGate" = false;
      "browser.urlbar.pocket.featureGate" = false;
      "browser.urlbar.weather.featureGate" = false;
      "browser.urlbar.yelp.featureGate" = false;
      "datareporting.healthreport.uploadEnabled" = false;
      "datareporting.policy.dataSubmissionEnabled" = false;
      "datareporting.usage.uploadEnabled" = false;
      "extensions.addonAbuseReport.url" = "";
      "extensions.getAddons.cache.enabled" = false;
      "network.captive-portal-service.enabled" = false;
      "network.connectivity-service.enabled" = false;
      "network.traffic_analyzer.enabled" = false;
      "network.trr.confirmation_telemetry_enabled" = false;
      "security.certerrors.recordEventTelemetry" = false;
      "toolkit.contentRelevancy.enabled" = false;
      "toolkit.coverage.endpoint.base" = "";
      "toolkit.coverage.opt-out" = true;
      "toolkit.telemetry.archive.enabled" = false;
      "toolkit.telemetry.bhrPing.enabled" = false;
      "toolkit.telemetry.cachedClientID" = "";
      "toolkit.telemetry.cachedProfileGroupID" = "";
      "toolkit.telemetry.coverage.opt-out" = true;
      "toolkit.telemetry.enabled" = false;
      "toolkit.telemetry.firstShutdownPing.enabled" = false;
      "toolkit.telemetry.newProfilePing.enabled" = false;
      "toolkit.telemetry.server" = "data:,";
      "toolkit.telemetry.shutdownPingSender.enabled" = false;
      "toolkit.telemetry.unified" = false;
      "toolkit.telemetry.updatePing.enabled" = false;
      "browser.contentblocking.category" = "strict"; # https://blog.mozilla.org/security/2021/02/23/total-cookie-protection/
      "browser.download.start_downloads_in_tmp_dir" = true; # start downloads in temp
      "browser.formfill.enable" = false;
      "dom.security.https_only_mode" = true; # only allow https in all windows, including private browsing
      "media.autoplay.default" = 5;
      "network.cookie.cookieBehavior.optInPartitioning" = true;
      "network.cookie.cookieBehavior.optInPartitioning.pbmode" = true;
      "network.predictor.enable-prefetch" = false; # Disable speculative website loading
      "network.predictor.enabled" = false; # Disable speculative website loading
      "network.prefetch-next" = false; # https://developer.mozilla.org/en-US/docs/Glossary/Prefetch
      "privacy.query_stripping.strip_list" = "__hsfp __hssc __hstc __s _hsenc _openstat dclid fbclid gbraid gclid hsCtaTracking igshid mc_eid ml_subscriber ml_subscriber_hash msclkid oft_c oft_ck oft_d oft_id oft_ids oft_k oft_lk oft_sk oly_anon_id oly_enc_id rb_clickid s_cid twclid vero_conv vero_id wbraid wickedid yclid"; # https://groups.google.com/a/mozilla.org/g/dev-platform/c/1vOSas0ptVQ?pli=1
      "urlclassifier.features.socialtracking.skipURLs" = "*.instagram.com, *.twitter.com, *.twimg.com"; # allow embedded social content
      "urlclassifier.trackingSkipURLs" = "*.reddit.com, *.twitter.com, *.twimg.com"; # allow embedded social content
    };
    locked = [
      "app.normandy.api_url"
      "app.normandy.enabled"
      "breakpad.reportURL"
      "browser.contentanalysis.default_result"
      "browser.contentanalysis.enabled"
      "browser.contentblocking.report.hide_vpn_banner"
      "browser.contentblocking.report.lockwise.enabled"
      "browser.contentblocking.report.mobile-android.url"
      "browser.contentblocking.report.mobile-ios.url"
      "browser.contentblocking.report.monitor.enabled"
      "browser.contentblocking.report.proxy_extension.url"
      "browser.contentblocking.report.show_mobile_app"
      "browser.contentblocking.report.vpn-android.url"
      "browser.contentblocking.report.vpn-ios.url"
      "browser.contentblocking.report.vpn-promo.url"
      "browser.contentblocking.report.vpn.url"
      "browser.crashReports.unsubmittedCheck.autoSubmit2"
      "browser.dataFeatureRecommendations.enabled"
      "browser.discovery.enabled"
      "browser.ipProtection.enabled"
      "browser.ipProtection.guardian.endpoint"
      "browser.ipProtection.variant"
      "browser.ml.chat.enabled"
      "browser.ml.chat.page"
      "browser.ml.enable"
      "browser.ml.linkPreview.enabled"
      "browser.newtabpage.activity-stream.feeds.aboutpreferences"
      "browser.newtabpage.activity-stream.feeds.adsfeed"
      "browser.newtabpage.activity-stream.feeds.discoverystreamfeed"
      "browser.newtabpage.activity-stream.feeds.places"
      "browser.newtabpage.activity-stream.feeds.recommendationprovider"
      "browser.newtabpage.activity-stream.feeds.system.topsites"
      "browser.newtabpage.activity-stream.feeds.system.topstories"
      "browser.newtabpage.activity-stream.feeds.topsites"
      "browser.newtabpage.activity-stream.showSponsoredCheckboxes"
      "browser.newtabpage.activity-stream.system.showSponsored"
      "browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint"
      "browser.newtabpage.activity-stream.telemetry.ut.event"
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.enabled"
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.spocs.enabled"
      "browser.newtabpage.activity-stream.unifiedAds.adsFeed.tiles.enabled"
      "browser.newtabpage.activity-stream.unifiedAds.endpoint"
      "browser.newtabpage.activity-stream.unifiedAds.spocs.enabled"
      "browser.newtabpage.activity-stream.unifiedAds.tiles.enabled"
      "browser.newtabpage.enabled"
      "browser.places.interactions.enabled"
      "browser.privatebrowsing.vpnpromourl"
      "browser.promo.cookiebanners.enabled"
      "browser.promo.focus.enabled"
      "browser.promo.pin.enabled"
      "browser.tabs.crashReporting.sendReport"
      "browser.tabs.groups.smart.userEnabled"
      "browser.uitour.enabled"
      "browser.uitour.url"
      "browser.urlbar.suggest.addons"
      "browser.urlbar.suggest.quicksuggest.fakespot"
      "browser.urlbar.suggest.quicksuggest.nonsponsored"
      "browser.urlbar.suggest.quicksuggest.sponsored"
      "browser.urlbar.suggest.quicksuggest.topsites"
      "browser.urlbar.suggest.trending"
      "browser.vpn_promo.enabled"
      "captivedetect.canonicalURL"
      "devtools.debugger.remote-enabled"
      "dom.private-attribution.submission.enabled"
      "dom.push.enabled"
      "dom.security.unexpected_system_load_telemetry_enabled"
      "extensions.abuseReport.enabled"
      "extensions.blocklist.enabled"
      "extensions.getAddons.showPane"
      "extensions.htmlaboutaddons.recommendations.enabled"
      "extensions.pocket.enabled"
      "extensions.webcompat-reporter.enabled"
      "media.gmp-gmpopenh264.autoupdate"
      "signon.firefoxRelay.feature"
      "security.OCSP.enabled"
      "security.pki.crlite_mode"
      "security.remote_settings.crlite_filters.enabled"
      "browser.newtabpage.activity-stream.feeds.telemetry"
      "browser.newtabpage.activity-stream.showSponsored"
      "browser.newtabpage.activity-stream.showSponsoredTopSites"
      "browser.newtabpage.activity-stream.telemetry"
      "browser.newtabpage.activity-stream.telemetry.ut.events"
      "browser.newtabpage.activity-stream.trendingSearch.blockedAds"
      "browser.newtabpage.activity-stream.trendingSearch.enabled"
      "browser.newtabpage.activity-stream.trendingSearch.variant"
      "browser.ping-centre.telemetry"
      "browser.search.serpEventTelemetryCategorization.enabled"
      "browser.search.serpEventTelemetryCategorization.regionEnabled"
      "browser.search.update"
      "browser.shopping.experience2023.enabled"
      "browser.startup.homepage_override.mstone"
      "browser.urlbar.addons.featureGate"
      "browser.urlbar.fakespot.featureGate"
      "browser.urlbar.mdn.featureGate"
      "browser.urlbar.pocket.featureGate"
      "browser.urlbar.weather.featureGate"
      "browser.urlbar.yelp.featureGate"
      "datareporting.healthreport.uploadEnabled"
      "datareporting.policy.dataSubmissionEnabled"
      "datareporting.usage.uploadEnabled"
      "extensions.addonAbuseReport.url"
      "extensions.getAddons.cache.enabled"
      "network.captive-portal-service.enabled"
      "network.connectivity-service.enabled"
      "network.traffic_analyzer.enabled"
      "network.trr.confirmation_telemetry_enabled"
      "security.certerrors.recordEventTelemetry"
      "toolkit.contentRelevancy.enabled"
      "toolkit.coverage.endpoint.base"
      "toolkit.coverage.opt-out"
      "toolkit.telemetry.archive.enabled"
      "toolkit.telemetry.bhrPing.enabled"
      "toolkit.telemetry.cachedClientID"
      "toolkit.telemetry.cachedProfileGroupID"
      "toolkit.telemetry.coverage.opt-out"
      "toolkit.telemetry.enabled"
      "toolkit.telemetry.firstShutdownPing.enabled"
      "toolkit.telemetry.newProfilePing.enabled"
      "toolkit.telemetry.server"
      "toolkit.telemetry.shutdownPingSender.enabled"
      "toolkit.telemetry.unified"
      "toolkit.telemetry.updatePing.enabled"
      "browser.download.start_downloads_in_tmp_dir"
      "dom.security.https_only_mode"
    ];
  };

  # ── safebrowsing — roudix.zen.tweaks.disableSafeBrowsing ───────────
  safebrowsing = {
    prefs = {
      "browser.safebrowsing.allowOverride" = false;
      "browser.safebrowsing.blockedURIs.enabled" = false;
      "browser.safebrowsing.debug" = false;
      "browser.safebrowsing.downloads.enabled" = false;
      "browser.safebrowsing.downloads.remote.block_dangerous" = false;
      "browser.safebrowsing.downloads.remote.block_dangerous_host" = false;
      "browser.safebrowsing.downloads.remote.block_potentially_unwanted" = false;
      "browser.safebrowsing.downloads.remote.block_uncommon" = false;
      "browser.safebrowsing.downloads.remote.enabled" = false;
      "browser.safebrowsing.downloads.remote.remote.url" = "";
      "browser.safebrowsing.downloads.remote.url" = "";
      "browser.safebrowsing.id" = "";
      "browser.safebrowsing.malware.enabled" = false;
      "browser.safebrowsing.phishing.enabled" = false;
      "browser.safebrowsing.provider.google.advisoryName" = "";
      "browser.safebrowsing.provider.google.advisoryURL" = "";
      "browser.safebrowsing.provider.google.gethashURL" = "";
      "browser.safebrowsing.provider.google.lists" = "";
      "browser.safebrowsing.provider.google.pver" = 0;
      "browser.safebrowsing.provider.google.reportMalwareMistakeURL" = "";
      "browser.safebrowsing.provider.google.reportPhishMistakeURL" = "";
      "browser.safebrowsing.provider.google.reportURL" = "";
      "browser.safebrowsing.provider.google.updateURL" = "";
      "browser.safebrowsing.provider.google4.advisoryName" = "";
      "browser.safebrowsing.provider.google4.advisoryURL" = "";
      "browser.safebrowsing.provider.google4.dataSharing.enabled" = false;
      "browser.safebrowsing.provider.google4.dataSharingURL" = "";
      "browser.safebrowsing.provider.google4.gethashURL" = "";
      "browser.safebrowsing.provider.google4.lists" = "";
      "browser.safebrowsing.provider.google4.pver" = 0;
      "browser.safebrowsing.provider.google4.reportMalwareMistakeURL" = "";
      "browser.safebrowsing.provider.google4.reportPhishMistakeURL" = "";
      "browser.safebrowsing.provider.google4.reportURL" = "";
      "browser.safebrowsing.provider.google4.updateURL" = "";
      "browser.safebrowsing.provider.mozilla.gethashURL" = "";
      "browser.safebrowsing.provider.mozilla.lastupdatetime" = 0;
      "browser.safebrowsing.provider.mozilla.lists" = "";
      "browser.safebrowsing.provider.mozilla.lists.base" = "";
      "browser.safebrowsing.provider.mozilla.lists.content" = "";
      "browser.safebrowsing.provider.mozilla.nextupdatetime" = 0;
      "browser.safebrowsing.provider.mozilla.pver" = 0;
      "browser.safebrowsing.provider.mozilla.reportURL" = "";
      "browser.safebrowsing.provider.mozilla.updateURL" = "";
      "browser.safebrowsing.reportPhishURL" = "";
    };
    locked = [
      "browser.safebrowsing.allowOverride"
      "browser.safebrowsing.blockedURIs.enabled"
      "browser.safebrowsing.debug"
      "browser.safebrowsing.downloads.enabled"
      "browser.safebrowsing.downloads.remote.block_dangerous"
      "browser.safebrowsing.downloads.remote.block_dangerous_host"
      "browser.safebrowsing.downloads.remote.block_potentially_unwanted"
      "browser.safebrowsing.downloads.remote.block_uncommon"
      "browser.safebrowsing.downloads.remote.enabled"
      "browser.safebrowsing.downloads.remote.remote.url"
      "browser.safebrowsing.downloads.remote.url"
      "browser.safebrowsing.id"
      "browser.safebrowsing.malware.enabled"
      "browser.safebrowsing.phishing.enabled"
      "browser.safebrowsing.provider.google.advisoryName"
      "browser.safebrowsing.provider.google.advisoryURL"
      "browser.safebrowsing.provider.google.gethashURL"
      "browser.safebrowsing.provider.google.lists"
      "browser.safebrowsing.provider.google.pver"
      "browser.safebrowsing.provider.google.reportMalwareMistakeURL"
      "browser.safebrowsing.provider.google.reportPhishMistakeURL"
      "browser.safebrowsing.provider.google.reportURL"
      "browser.safebrowsing.provider.google.updateURL"
      "browser.safebrowsing.provider.google4.advisoryName"
      "browser.safebrowsing.provider.google4.advisoryURL"
      "browser.safebrowsing.provider.google4.dataSharing.enabled"
      "browser.safebrowsing.provider.google4.dataSharingURL"
      "browser.safebrowsing.provider.google4.gethashURL"
      "browser.safebrowsing.provider.google4.lists"
      "browser.safebrowsing.provider.google4.pver"
      "browser.safebrowsing.provider.google4.reportMalwareMistakeURL"
      "browser.safebrowsing.provider.google4.reportPhishMistakeURL"
      "browser.safebrowsing.provider.google4.reportURL"
      "browser.safebrowsing.provider.google4.updateURL"
      "browser.safebrowsing.provider.mozilla.gethashURL"
      "browser.safebrowsing.provider.mozilla.lastupdatetime"
      "browser.safebrowsing.provider.mozilla.lists"
      "browser.safebrowsing.provider.mozilla.lists.base"
      "browser.safebrowsing.provider.mozilla.lists.content"
      "browser.safebrowsing.provider.mozilla.nextupdatetime"
      "browser.safebrowsing.provider.mozilla.pver"
      "browser.safebrowsing.provider.mozilla.reportURL"
      "browser.safebrowsing.provider.mozilla.updateURL"
      "browser.safebrowsing.reportPhishURL"
    ];
  };

  # ── ui — roudix.zen.tweaks.ui (smooth scrolling, masonry) ──────────
  ui = {
    prefs = {
      "general.smoothScroll.msdPhysics.continuousMotionMaxDeltaMS" = 12;
      "general.smoothScroll.msdPhysics.enabled" = true; # Use physics-based smooth scrolling
      "general.smoothScroll.msdPhysics.motionBeginSpringConstant" = 200;
      "general.smoothScroll.msdPhysics.regularSpringConstant" = 250;
      "general.smoothScroll.msdPhysics.slowdownMinDeltaMS" = 25;
      "general.smoothScroll.msdPhysics.slowdownMinDeltaRatio" = "2.0"; # Ensure float format if needed
      "general.smoothScroll.msdPhysics.slowdownSpringConstant" = 250;
      "general.smoothScroll.currentVelocityWeighting" = "1.0"; # Ensure float format if needed
      "general.smoothScroll.stopDecelerationWeighting" = "1.0"; # Ensure float format if needed
      "mousewheel.default.delta_multiplier_y" = 300; # Adjust mouse wheel scroll speed
      "layout.css.grid-template-masonry-value.enabled" = true; # Enable CSS Masonry layout
    };
    locked = [
    ];
  };
}
