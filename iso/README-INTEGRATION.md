# Où ça va dans ton repo

Sur ta nouvelle branche `feat/native-installer`, dans le dossier `iso/` :

    iso/flake.nix               <- remplace l'existant (overlay Calamares supprimé)
    iso/iso-configuration.nix   <- remplace l'existant (packages + autostart Calamares supprimés)
    iso/roudix-installer/       <- nouveau dossier, colle tout le contenu ici

Fichiers/dossiers à SUPPRIMER dans iso/ (plus utilisés) :
    iso/patches/calamares-nixos-extensions/   (tout le dossier)

À vérifier ensuite dans iso/branding.nix (pas modifié ici, pas eu le fichier) :
    - toute référence à roudixBranding.share."calamares/branding/..."
      doit être adaptée ou supprimée si branding.nix pousse des assets
      spécifiques au chemin calamares/

# Commandes

    git checkout feat/calamares-installer
    git checkout -b feat/native-installer
    # copier les fichiers ci-dessus dans iso/
    rm -rf iso/patches/calamares-nixos-extensions
    cd iso
    nix flake update          # résout le nouvel input disko + roudix-installer
    nix flake check            # sanity check avant de lancer un build complet
    nix build .#packages.x86_64-linux.iso --option sandbox false -L

Puis boot l'ISO en VM et vérifie que roudix-installer se lance en autostart.
