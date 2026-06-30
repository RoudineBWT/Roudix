// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import io.calamares.ui 1.0
import io.calamares.core 1.0

Item {
    id: page

    property string kernel: "cachyos-latest"
    property string browser: "brave"
    property string braveVariant: "brave"
    property bool zen: false
    property string de: "niri"
    property string desktopShell: "noctalia"
    property string shellDefault: "fish"
    property bool gaming: true

    function pushState() {
        config.setSoftware({
            kernel: kernel,
            browser: browser === "brave" ? braveVariant : browser,
            zen: zen,
            de: de,
            desktopShell: desktopShell,
            shellDefault: shellDefault,
            gaming: gaming
        })
    }

    Component.onCompleted: pushState()

    ListModel {
        id: kernelModel
        ListElement { value: "cachyos-latest";          label: "Standard latest CachyOS kernel" }
        ListElement { value: "cachyos-latest-v3";        label: "x86_64-v3 optimized (recommandé CPU récents)" }
        ListElement { value: "cachyos-latest-lto";       label: "LTO build — meilleures performances" }
        ListElement { value: "cachyos-latest-lto-v3";    label: "LTO + x86_64-v3 (meilleures perfs, CPU récents)" }
        ListElement { value: "cachyos-lts";              label: "Long-term support CachyOS kernel" }
        ListElement { value: "cachyos-lts-v3";           label: "LTS + x86_64-v3 optimized" }
        ListElement { value: "cachyos-lts-lto-v3";       label: "LTS + LTO + x86_64-v3 (stable + perfs)" }
        ListElement { value: "cachyos-rc";               label: "Release candidate — bleeding edge" }
    }

    ListModel {
        id: browserModel
        ListElement { value: "none";                label: "Aucun navigateur" }
        ListElement { value: "brave";                label: "Brave" }
        ListElement { value: "helium";               label: "Helium" }
        ListElement { value: "vivaldi";              label: "Vivaldi" }
        ListElement { value: "firefox";              label: "Firefox" }
        ListElement { value: "librewolf";            label: "LibreWolf" }
        ListElement { value: "google-chrome";        label: "Google Chrome" }
        ListElement { value: "microsoft-edge";       label: "Microsoft Edge" }
        ListElement { value: "ungoogled-chromium";   label: "Ungoogled Chromium" }
        ListElement { value: "chromium";             label: "Chromium" }
    }

    ListModel {
        id: braveVariantModel
        ListElement { value: "brave";                label: "Stable (recommandé)" }
        ListElement { value: "brave-beta";           label: "Beta" }
        ListElement { value: "brave-nightly";        label: "Nightly" }
        ListElement { value: "brave-origin-beta";    label: "Origin Beta" }
        ListElement { value: "brave-origin-nightly"; label: "Origin Nightly" }
    }

    ListModel {
        id: deModel
        ListElement { value: "niri";      label: "Niri" }
        ListElement { value: "gnome";     label: "GNOME" }
        ListElement { value: "kde";       label: "KDE Plasma" }
        ListElement { value: "hyprland";  label: "Hyprland" }
    }

    function shellOptionsFor(deValue) {
        if (deValue === "niri") {
            return [
                { value: "noctalia", label: "Noctalia — shell par défaut Roudix" },
                { value: "dms",      label: "DankMaterialShell — design Material 3" }
            ]
        } else if (deValue === "hyprland") {
            return [
                { value: "noctalia",  label: "Noctalia — shell par défaut Roudix" },
                { value: "dms",       label: "DankMaterialShell — design Material 3" },
                { value: "caelestia", label: "Caelestia — setup Quickshell esthétique" }
            ]
        }
        return []
    }

    Flickable {
        anchors.fill: parent
        contentHeight: column.height
        clip: true

        ColumnLayout {
            id: column
            width: page.width - 40
            x: 20
            spacing: 24

            Label {
                text: qsTr("Logiciels")
                font.pixelSize: 22
                font.bold: true
            }

            // ── Kernel ───────────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Kernel :"); font.bold: true }
                ComboBox {
                    Layout.fillWidth: true
                    model: kernelModel
                    textRole: "label"
                    currentIndex: 0
                    onActivated: { kernel = kernelModel.get(currentIndex).value; pushState() }
                }
            }

            // ── Browser ──────────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Navigateur :"); font.bold: true }
                ComboBox {
                    Layout.fillWidth: true
                    model: browserModel
                    textRole: "label"
                    currentIndex: 1
                    onActivated: { browser = browserModel.get(currentIndex).value; pushState() }
                }

                ColumnLayout {
                    visible: browser === "brave"
                    spacing: 4
                    Label { text: qsTr("Variante Brave :") }
                    ComboBox {
                        Layout.fillWidth: true
                        model: braveVariantModel
                        textRole: "label"
                        currentIndex: 0
                        onActivated: { braveVariant = braveVariantModel.get(currentIndex).value; pushState() }
                    }
                }
            }

            // ── Zen ──────────────────────────────────────────────
            RowLayout {
                spacing: 12
                Label { text: qsTr("Installer Zen Browser ?"); font.bold: true }
                Switch {
                    checked: zen
                    onCheckedChanged: { zen = checked; pushState() }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Desktop environment ──────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Environnement de bureau :"); font.bold: true }
                ComboBox {
                    Layout.fillWidth: true
                    model: deModel
                    textRole: "label"
                    currentIndex: 0
                    onActivated: {
                        de = deModel.get(currentIndex).value
                        var opts = shellOptionsFor(de)
                        desktopShell = opts.length > 0 ? opts[0].value : "noctalia"
                        pushState()
                    }
                }
            }

            // ── Desktop shell (only for niri/hyprland) ───────────
            ColumnLayout {
                visible: de === "niri" || de === "hyprland"
                spacing: 4
                Label { text: qsTr("Shell de bureau (bar/UI) :"); font.bold: true }
                Repeater {
                    model: shellOptionsFor(de)
                    delegate: RadioButton {
                        text: modelData.label
                        checked: desktopShell === modelData.value
                        onCheckedChanged: if (checked) { desktopShell = modelData.value; pushState() }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Default shell ────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Shell par défaut :"); font.bold: true }
                ButtonGroup { id: shellGroup }
                RadioButton {
                    text: qsTr("Fish — shell intelligent et convivial (recommandé)")
                    checked: shellDefault === "fish"
                    ButtonGroup.group: shellGroup
                    onCheckedChanged: if (checked) { shellDefault = "fish"; pushState() }
                }
                RadioButton {
                    text: qsTr("Bash — shell Unix classique")
                    checked: shellDefault === "bash"
                    ButtonGroup.group: shellGroup
                    onCheckedChanged: if (checked) { shellDefault = "bash"; pushState() }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Gaming ────────────────────────────────────────────
            RowLayout {
                spacing: 12
                Label { text: qsTr("Activer les paquets gaming ? (Steam, Wine, Lutris...)"); font.bold: true }
                Switch {
                    checked: gaming
                    onCheckedChanged: { gaming = checked; pushState() }
                }
            }
        }
    }
}
