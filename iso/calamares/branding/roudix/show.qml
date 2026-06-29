/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 5000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Image {
            id: background1
            source: "languages.png"
            width: 800
            height: 440
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: background1.bottom
            text: "Bienvenue sur Roudix"
            font.pixelSize: 22
            color: "#FFFFFF"
        }
    }

    Slide {
        Text {
            anchors.centerIn: parent
            text: "Installation en cours…\nMerci de patienter."
            font.pixelSize: 20
            color: "#FFFFFF"
            horizontalAlignment: Text.AlignHCenter
        }
    }

    function onActivate() {}
    function onLeave() {}
}
