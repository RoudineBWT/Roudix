// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import io.calamares.ui 1.0
import io.calamares.core 1.0

Item {
    id: page

    property var detected: config.detected || ({})

    property string gpu: detected.gpu || "amd"
    property string gpuAmdGen: "amd"
    property bool nvidiaLaptop: detected.nvidiaLaptop || false
    property string cpu: detected.cpu || "amd"
    property bool vmGuest: detected.vmGuest || false
    property bool gpuConfirmed: detected.gpu !== ""
    property bool cpuConfirmed: detected.cpu !== ""

    function pushState() {
        config.setHardware({
            gpu: gpu === "amd" && gpuAmdGen === "amd-legacy" ? "amd-legacy" : gpu,
            nvidiaLaptop: nvidiaLaptop,
            cpu: cpu,
            vmGuest: vmGuest
        })
    }

    Component.onCompleted: pushState()

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
                text: qsTr("Matériel détecté")
                font.pixelSize: 22
                font.bold: true
            }

            // ── GPU ──────────────────────────────────────────────
            ColumnLayout {
                spacing: 6
                Label {
                    text: detected.gpu !== ""
                        ? qsTr("GPU détecté : ") + detected.gpu + (detected.nvidiaLaptop ? qsTr(" (Optimus laptop)") : "")
                        : qsTr("GPU non détecté automatiquement — choisis manuellement :")
                    font.bold: true
                }

                RowLayout {
                    visible: detected.gpu !== ""
                    spacing: 12
                    Button {
                        text: qsTr("Confirmer")
                        highlighted: gpuConfirmed
                        onClicked: { gpuConfirmed = true; pushState() }
                    }
                    Button {
                        text: qsTr("Corriger")
                        highlighted: !gpuConfirmed
                        onClicked: { gpuConfirmed = false; pushState() }
                    }
                }

                ColumnLayout {
                    visible: !gpuConfirmed
                    spacing: 4
                    ButtonGroup { id: gpuGroup }
                    RadioButton {
                        text: qsTr("AMD GPU")
                        checked: gpu === "amd"
                        ButtonGroup.group: gpuGroup
                        onCheckedChanged: if (checked) { gpu = "amd"; pushState() }
                    }
                    RadioButton {
                        text: qsTr("AMD GPU legacy (GCN 1.x / 2.x — HD 7xxx, R9 2xx)")
                        checked: gpu === "amd-legacy"
                        ButtonGroup.group: gpuGroup
                        onCheckedChanged: if (checked) { gpu = "amd-legacy"; pushState() }
                    }
                    RadioButton {
                        text: qsTr("NVIDIA GPU")
                        checked: gpu === "nvidia"
                        ButtonGroup.group: gpuGroup
                        onCheckedChanged: if (checked) { gpu = "nvidia"; pushState() }
                    }
                    RadioButton {
                        text: qsTr("Intel GPU intégré")
                        checked: gpu === "intel"
                        ButtonGroup.group: gpuGroup
                        onCheckedChanged: if (checked) { gpu = "intel"; pushState() }
                    }
                }

                // AMD generation (only if amd was auto-confirmed)
                ColumnLayout {
                    visible: gpuConfirmed && detected.gpu === "amd"
                    spacing: 4
                    Label { text: qsTr("Génération AMD :") }
                    ButtonGroup { id: amdGenGroup }
                    RadioButton {
                        text: qsTr("Modern — RDNA / GCN 3+ (RX 400 series et plus récent)")
                        checked: gpuAmdGen === "amd"
                        ButtonGroup.group: amdGenGroup
                        onCheckedChanged: if (checked) { gpuAmdGen = "amd"; pushState() }
                    }
                    RadioButton {
                        text: qsTr("Legacy — GCN 1.x / 2.x (HD 7xxx, R9 2xx)")
                        checked: gpuAmdGen === "amd-legacy"
                        ButtonGroup.group: amdGenGroup
                        onCheckedChanged: if (checked) { gpuAmdGen = "amd-legacy"; pushState() }
                    }
                }

                // NVIDIA laptop / Optimus (only if manually picked nvidia)
                ColumnLayout {
                    visible: !gpuConfirmed && gpu === "nvidia"
                    spacing: 4
                    Label { text: qsTr("Laptop avec NVIDIA dGPU (Optimus) ?") }
                    ButtonGroup { id: optimusGroup }
                    RadioButton {
                        text: qsTr("Non — desktop ou NVIDIA seul")
                        checked: !nvidiaLaptop
                        ButtonGroup.group: optimusGroup
                        onCheckedChanged: if (checked) { nvidiaLaptop = false; pushState() }
                    }
                    RadioButton {
                        text: qsTr("Oui — laptop Intel/AMD + NVIDIA")
                        checked: nvidiaLaptop
                        ButtonGroup.group: optimusGroup
                        onCheckedChanged: if (checked) { nvidiaLaptop = true; pushState() }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── CPU ──────────────────────────────────────────────
            ColumnLayout {
                spacing: 6
                Label {
                    text: detected.cpu !== ""
                        ? qsTr("CPU détecté : ") + detected.cpu
                        : qsTr("CPU non détecté automatiquement — choisis manuellement :")
                    font.bold: true
                }

                RowLayout {
                    visible: detected.cpu !== ""
                    spacing: 12
                    Button {
                        text: qsTr("Confirmer")
                        highlighted: cpuConfirmed
                        onClicked: { cpuConfirmed = true; pushState() }
                    }
                    Button {
                        text: qsTr("Corriger")
                        highlighted: !cpuConfirmed
                        onClicked: { cpuConfirmed = false; pushState() }
                    }
                }

                ColumnLayout {
                    visible: !cpuConfirmed
                    spacing: 4
                    ButtonGroup { id: cpuGroup }
                    RadioButton {
                        text: qsTr("AMD CPU")
                        checked: cpu === "amd"
                        ButtonGroup.group: cpuGroup
                        onCheckedChanged: if (checked) { cpu = "amd"; pushState() }
                    }
                    RadioButton {
                        text: qsTr("Intel CPU")
                        checked: cpu === "intel"
                        ButtonGroup.group: cpuGroup
                        onCheckedChanged: if (checked) { cpu = "intel"; pushState() }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#33000000" }

            // ── VM Guest ─────────────────────────────────────────
            ColumnLayout {
                spacing: 6
                Label {
                    text: detected.vmGuest
                        ? qsTr("Machine virtuelle détectée — optimisations VM activées.")
                        : qsTr("Exécution dans une VM ?")
                    font.bold: true
                }
                ColumnLayout {
                    visible: !detected.vmGuest
                    spacing: 4
                    ButtonGroup { id: vmGroup }
                    RadioButton {
                        text: qsTr("Non — installation sur machine physique")
                        checked: !vmGuest
                        ButtonGroup.group: vmGroup
                        onCheckedChanged: if (checked) { vmGuest = false; pushState() }
                    }
                    RadioButton {
                        text: qsTr("Oui — activer les optimisations VM")
                        checked: vmGuest
                        ButtonGroup.group: vmGroup
                        onCheckedChanged: if (checked) { vmGuest = true; pushState() }
                    }
                }
            }
        }
    }
}
