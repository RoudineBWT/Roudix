# gen-cosmic-theme

Generates the Roudix COSMIC theme shipped in `assets/cosmic/` from the colours
of `assets/palette/Roudix.json` (values are set in `src/main.rs`).

```sh
cd scripts/gen-cosmic-theme
rm -rf /tmp/roudix-cosmic && mkdir /tmp/roudix-cosmic
XDG_CONFIG_HOME=/tmp/roudix-cosmic cargo run --release
rm -rf ../../assets/cosmic && cp -r /tmp/roudix-cosmic/cosmic ../../assets/cosmic
```

`com.system76.CosmicTheme.{Dark,Light}.Builder` is what COSMIC Settings edits;
`com.system76.CosmicTheme.{Dark,Light}` is the derived theme the apps actually
read. Both are needed, hence a real build with libcosmic's own `build()`.
The `v2` folder name is the config version of the pinned COSMIC epoch.
