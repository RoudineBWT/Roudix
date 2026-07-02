/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    // Demande à Calamares d'afficher les logs par défaut
    property bool showLogFile: true

    Timer {
        interval: 8000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#1E2030"

            Image {
                source: "logo.png"
                width: 220
                height: 220
                fillMode: Image.PreserveAspectFit
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -30
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 60
                text: "Installation de Roudix en cours…"
                color: "#E8956D"
                font.pixelSize: 18
                font.bold: true
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 36
                text: "NixOS Unstable"
                color: "#D4849A"
                font.pixelSize: 14
            }
        }
    }

    function onActivate() {}
    function onLeave() {}
}
