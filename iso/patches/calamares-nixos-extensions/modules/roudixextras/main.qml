// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import io.calamares.ui 1.0
import io.calamares.core 1.0

Item {
    id: page

    property bool gtaFix: false
    property bool flatpak: false
    property bool virtualization: false
    property bool autoupdate: true
    property string autoupdateInterval: "1h"
    property string bootloader: "limine"
    property string matrixClient: "none"
    property bool waydroid: false

    function pushState() {
        config.setExtras({
            gtaFix: gtaFix,
            flatpak: flatpak,
            virtualization: virtualization,
            autoupdate: autoupdate,
            autoupdateInterval: autoupdateInterval,
            bootloader: bootloader,
            matrixClient: matrixClient,
            waydroid: waydroid
        })
    }

    Component.onCompleted: pushState()

    ListModel {
        id: matrixModel
        ListElement { value: "none";    label: "Aucun" }
        ListElement { value: "element"; label: "Element Desktop — client Matrix complet" }
        ListElement { value: "cinny";   label: "Cinny — client Matrix web léger" }
    }

    Flickable {
        anchors.fill: parent
        contentHeight: column.height
        clip: true

        ColumnLayout {
            id: column
            width: page.width - 40
            x: 20
            spacing: 22

            Label {
                text: qsTr("Extras")
                font.pixelSize: 22
                font.bold: true
            }

            RowLayout {
                spacing: 12
                Label { text: qsTr("Activer le fix GTA Online ? (bloque l'IP pour jouer sous Linux)"); font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                Switch { checked: gtaFix; onCheckedChanged: { gtaFix = checked; pushState() } }
            }

            RowLayout {
                spacing: 12
                Label { text: qsTr("Activer Flatpak ?"); font.bold: true; Layout.fillWidth: true }
                Switch { checked: flatpak; onCheckedChanged: { flatpak = checked; pushState() } }
            }

            RowLayout {
                spacing: 12
                Label { text: qsTr("Activer la virtualisation ? (libvirt, virt-manager...)"); font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                Switch { checked: virtualization; onCheckedChanged: { virtualization = checked; pushState() } }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            ColumnLayout {
                spacing: 8
                RowLayout {
                    spacing: 12
                    Label { text: qsTr("Activer les mises à jour automatiques ?"); font.bold: true; Layout.fillWidth: true }
                    Switch { checked: autoupdate; onCheckedChanged: { autoupdate = checked; pushState() } }
                }
                RowLayout {
                    visible: autoupdate
                    spacing: 12
                    Label { text: qsTr("Intervalle de vérification (ex. 1h, 6h, 12h, 24h) :") }
                    TextField {
                        text: autoupdateInterval
                        placeholderText: "1h"
                        Layout.preferredWidth: 100
                        onEditingFinished: { autoupdateInterval = text.length > 0 ? text : "1h"; pushState() }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Bootloader ───────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Bootloader :"); font.bold: true }
                ButtonGroup { id: bootGroup }
                RadioButton {
                    text: qsTr("Limine — moderne, rapide, multi-disque (recommandé)")
                    checked: bootloader === "limine"
                    ButtonGroup.group: bootGroup
                    onCheckedChanged: if (checked) { bootloader = "limine"; pushState() }
                }
                RadioButton {
                    text: qsTr("systemd-boot — bootloader UEFI simple")
                    checked: bootloader === "systemd-boot"
                    ButtonGroup.group: bootGroup
                    onCheckedChanged: if (checked) { bootloader = "systemd-boot"; pushState() }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Matrix client ────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Label { text: qsTr("Client Matrix :"); font.bold: true }
                ComboBox {
                    Layout.fillWidth: true
                    model: matrixModel
                    textRole: "label"
                    currentIndex: 0
                    onActivated: { matrixClient = matrixModel.get(currentIndex).value; pushState() }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── Waydroid ─────────────────────────────────────────
            RowLayout {
                spacing: 12
                Label { text: qsTr("Activer Waydroid ? (conteneur Android)"); font.bold: true; Layout.fillWidth: true }
                Switch { checked: waydroid; onCheckedChanged: { waydroid = checked; pushState() } }
            }
        }
    }
}
