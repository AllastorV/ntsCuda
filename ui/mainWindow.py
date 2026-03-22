# -*- coding: utf-8 -*-
# Professional redesign — ntsCuda UI
# Maintains all original widget names for full NtscApp.py compatibility

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 800)
        MainWindow.setMinimumSize(QtCore.QSize(960, 640))

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # ── Root horizontal layout ──────────────────────────────────────────
        root_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.setObjectName("horizontalLayout_3")

        # ════════════════════════════════════════════════════════════════════
        # LEFT PANEL
        # ════════════════════════════════════════════════════════════════════
        self.leftPanel = QtWidgets.QWidget()
        self.leftPanel.setObjectName("leftPanel")
        self.leftPanel.setMinimumWidth(420)
        self.leftPanel.setMaximumWidth(560)
        self.leftPanel.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        left_vbox = QtWidgets.QVBoxLayout(self.leftPanel)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        # ── Panel header (title + CUDA indicator + GitHub link) ──────────
        header_widget = QtWidgets.QWidget()
        header_widget.setObjectName("panelHeader")
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

        title_lbl = QtWidgets.QLabel("ntsCuda")
        title_lbl.setObjectName("appTitle")
        header_layout.addWidget(title_lbl)

        # CUDA indicator
        self.cudaIndicator = QtWidgets.QLabel()
        self.cudaIndicator.setObjectName("cudaIndicator")
        self.cudaIndicator.setFixedHeight(20)
        header_layout.addWidget(self.cudaIndicator)

        header_layout.addStretch()

        self.label = QtWidgets.QLabel()
        self.label.setObjectName("githubLink")
        self.label.setOpenExternalLinks(True)
        header_layout.addWidget(self.label)

        left_vbox.addWidget(header_widget)

        # ── Scroll area for controls ────────────────────────────────────────
        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("controlsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        scroll_content = QtWidgets.QWidget()
        scroll_content.setObjectName("scrollContent")

        # controlLayout — the main VBox that NtscApp expects
        self.controlLayout = QtWidgets.QVBoxLayout(scroll_content)
        self.controlLayout.setObjectName("controlLayout")
        self.controlLayout.setContentsMargins(8, 6, 8, 10)
        self.controlLayout.setSpacing(2)
        self.controlLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        # ── Section: Effect Switches ────────────────────────────────────────
        cb_header = QtWidgets.QLabel("EFFECT SWITCHES")
        cb_header.setObjectName("sectionHeader")
        self.controlLayout.addWidget(cb_header)

        self.checkboxesLayout = QtWidgets.QGridLayout()
        self.checkboxesLayout.setObjectName("checkboxesLayout")
        self.checkboxesLayout.setSpacing(4)
        self.checkboxesLayout.setContentsMargins(4, 2, 4, 4)
        self.controlLayout.addLayout(self.checkboxesLayout)

        # ── Section: Parameters ─────────────────────────────────────────────
        param_header = QtWidgets.QLabel("PARAMETERS")
        param_header.setObjectName("sectionHeader")
        self.controlLayout.addWidget(param_header)

        self.slidersLayout = QtWidgets.QVBoxLayout()
        self.slidersLayout.setObjectName("slidersLayout")
        self.slidersLayout.setSpacing(1)
        self.slidersLayout.setContentsMargins(2, 2, 2, 2)
        self.controlLayout.addLayout(self.slidersLayout)

        # ── Section: VHS Audio ──────────────────────────────────────────────
        audio_header = QtWidgets.QLabel("VHS AUDIO")
        audio_header.setObjectName("sectionHeader")
        self.controlLayout.addWidget(audio_header)

        self.audioSectionWidget = QtWidgets.QWidget()
        self.audioSectionWidget.setObjectName("audioSection")
        audio_vbox = QtWidgets.QVBoxLayout(self.audioSectionWidget)
        audio_vbox.setContentsMargins(4, 4, 4, 4)
        audio_vbox.setSpacing(4)

        self.processAudioCheckBox = QtWidgets.QCheckBox()
        self.processAudioCheckBox.setObjectName("processAudioCheckBox")
        audio_vbox.addWidget(self.processAudioCheckBox)

        # Audio sliders
        self.audioSlidersLayout = QtWidgets.QVBoxLayout()
        self.audioSlidersLayout.setSpacing(1)
        self.audioSlidersLayout.setContentsMargins(0, 0, 0, 0)
        audio_vbox.addLayout(self.audioSlidersLayout)

        self.controlLayout.addWidget(self.audioSectionWidget)

        # ── Section: Presets ────────────────────────────────────────────────
        presets_header = QtWidgets.QLabel("PRESETS")
        presets_header.setObjectName("sectionHeader")
        self.controlLayout.addWidget(presets_header)

        presets_wrap = QtWidgets.QWidget()
        presets_vbox = QtWidgets.QVBoxLayout(presets_wrap)
        presets_vbox.setContentsMargins(2, 4, 2, 2)
        presets_vbox.setSpacing(4)

        self.templatesLayout = QtWidgets.QHBoxLayout()
        self.templatesLayout.setObjectName("templatesLayout")
        self.templatesLayout.setSpacing(4)
        presets_vbox.addLayout(self.templatesLayout)

        self.exportImportConfigButton = QtWidgets.QPushButton()
        self.exportImportConfigButton.setObjectName("exportImportConfigButton")
        presets_vbox.addWidget(self.exportImportConfigButton)

        self.controlLayout.addWidget(presets_wrap)
        self.controlLayout.addStretch()

        scroll.setWidget(scroll_content)
        left_vbox.addWidget(scroll, 1)
        root_layout.addWidget(self.leftPanel)

        # ── Vertical divider ────────────────────────────────────────────────
        divider = QtWidgets.QFrame()
        divider.setObjectName("panelDivider")
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setFrameShadow(QtWidgets.QFrame.Plain)
        divider.setMaximumWidth(1)
        root_layout.addWidget(divider)

        # ════════════════════════════════════════════════════════════════════
        # RIGHT PANEL
        # ════════════════════════════════════════════════════════════════════
        right_panel = QtWidgets.QWidget()
        right_panel.setObjectName("rightPanel")
        self.verticalLayout = QtWidgets.QVBoxLayout(right_panel)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(6)

        # ── Preview ─────────────────────────────────────────────────────────
        self.image_frame = QtWidgets.QLabel()
        self.image_frame.setObjectName("image_frame")
        img_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        img_policy.setHorizontalStretch(1)
        self.image_frame.setSizePolicy(img_policy)
        self.image_frame.setMinimumSize(QtCore.QSize(200, 150))
        self.image_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.image_frame.setScaledContents(False)
        self.verticalLayout.addWidget(self.image_frame, 1)

        # ── Compare slider (vertical split position) ───────────────────────
        self.compareSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.compareSlider.setObjectName("compareSlider")
        self.compareSlider.setMinimum(0)
        self.compareSlider.setMaximum(100)
        self.compareSlider.setValue(50)
        self.compareSlider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.compareSlider.hide()
        self.verticalLayout.addWidget(self.compareSlider)

        # ── Video track ─────────────────────────────────────────────────────
        self.positionControlLayout = QtWidgets.QHBoxLayout()
        self.positionControlLayout.setObjectName("positionControlLayout")
        self.positionControlLayout.setSpacing(6)

        self.refreshFrameButton = QtWidgets.QPushButton()
        self.refreshFrameButton.setObjectName("refreshFrameButton")
        self.refreshFrameButton.setFixedSize(28, 28)
        self.positionControlLayout.addWidget(self.refreshFrameButton)

        self.videoTrackSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.videoTrackSlider.setObjectName("videoTrackSlider")
        self.videoTrackSlider.setMinimum(1)
        self.videoTrackSlider.setMaximum(3000)
        self.videoTrackSlider.setTracking(True)
        self.positionControlLayout.addWidget(self.videoTrackSlider, 1)

        self.livePreviewCheckbox = QtWidgets.QCheckBox()
        self.livePreviewCheckbox.setObjectName("livePreviewCheckbox")
        self.positionControlLayout.addWidget(self.livePreviewCheckbox)

        self.verticalLayout.addLayout(self.positionControlLayout)

        # ── Settings grid ────────────────────────────────────────────────────
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_2.setSpacing(6)

        # Row 0 — Render height + Seed
        self.label_2 = QtWidgets.QLabel()
        self.label_2.setObjectName("label_2")
        self.label_2.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.gridLayout_2.addWidget(self.label_2, 0, 0)

        self.renderHeightBox = QtWidgets.QSpinBox()
        self.renderHeightBox.setObjectName("renderHeightBox")
        self.renderHeightBox.setMaximum(3000)
        self.renderHeightBox.setSingleStep(120)
        self.renderHeightBox.setMinimumWidth(70)
        self.gridLayout_2.addWidget(self.renderHeightBox, 0, 1)

        # Spacer between height and seed
        self.gridLayout_2.addItem(
            QtWidgets.QSpacerItem(
                16, 0,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Minimum,
            ),
            0, 2,
        )

        self.seedLabel = QtWidgets.QLabel()
        self.seedLabel.setObjectName("seedLabel")
        self.seedLabel.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.gridLayout_2.addWidget(self.seedLabel, 0, 3)

        self.seedSpinBox = QtWidgets.QSpinBox()
        self.seedSpinBox.setObjectName("seedSpinBox")
        self.seedSpinBox.setMinimumWidth(70)
        self.gridLayout_2.addWidget(self.seedSpinBox, 0, 4)

        # Row 1 — Toggle checkboxes
        self.NearestUpScale = QtWidgets.QCheckBox()
        self.NearestUpScale.setObjectName("NearestUpScale")
        self.gridLayout_2.addWidget(self.NearestUpScale, 1, 0)

        self.ProMode = QtWidgets.QCheckBox()
        self.ProMode.setObjectName("ProMode")
        self.gridLayout_2.addWidget(self.ProMode, 1, 1)

        self.toggleMainEffect = QtWidgets.QCheckBox()
        self.toggleMainEffect.setObjectName("toggleMainEffect")
        self.toggleMainEffect.setChecked(True)
        self.gridLayout_2.addWidget(self.toggleMainEffect, 1, 2)

        self.compareModeButton = QtWidgets.QCheckBox()
        self.compareModeButton.setObjectName("compareModeButton")
        self.gridLayout_2.addWidget(self.compareModeButton, 1, 3)

        self.LossLessCheckBox = QtWidgets.QCheckBox()
        self.LossLessCheckBox.setObjectName("LossLessCheckBox")
        self.gridLayout_2.addWidget(self.LossLessCheckBox, 1, 4)

        self.verticalLayout.addLayout(self.gridLayout_2)

        # ── Status ───────────────────────────────────────────────────────────
        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.statusLabel)

        # ── Progress bar ─────────────────────────────────────────────────────
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.verticalLayout.addWidget(self.progressBar)

        # ── Open buttons ─────────────────────────────────────────────────────
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_4.setSpacing(6)

        self.openFile = QtWidgets.QPushButton()
        self.openFile.setObjectName("openFile")
        self.horizontalLayout_4.addWidget(self.openFile, 1)

        self.openImageUrlButton = QtWidgets.QToolButton()
        self.openImageUrlButton.setObjectName("openImageUrlButton")
        self.horizontalLayout_4.addWidget(self.openImageUrlButton)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        # ── Render / action buttons ──────────────────────────────────────────
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSpacing(6)

        self.renderVideoButton = QtWidgets.QPushButton()
        self.renderVideoButton.setObjectName("renderVideoButton")
        self.renderVideoButton.setEnabled(True)
        self.horizontalLayout.addWidget(self.renderVideoButton, 3)

        self.saveImageButton = QtWidgets.QPushButton()
        self.saveImageButton.setObjectName("saveImageButton")
        self.horizontalLayout.addWidget(self.saveImageButton, 2)

        self.pauseRenderButton = QtWidgets.QPushButton()
        self.pauseRenderButton.setObjectName("pauseRenderButton")
        self.pauseRenderButton.setCheckable(True)
        self.pauseRenderButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.horizontalLayout.addWidget(self.pauseRenderButton, 1)

        self.stopRenderButton = QtWidgets.QPushButton()
        self.stopRenderButton.setObjectName("stopRenderButton")
        self.stopRenderButton.setEnabled(False)
        self.horizontalLayout.addWidget(self.stopRenderButton, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        root_layout.addWidget(right_panel, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _tr = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_tr("MainWindow", "ntsCuda \u2014 NTSC & VHS Studio"))

        self.label.setText(_tr(
            "MainWindow",
            '<a href="https://github.com/AllastorV/ntsCuda"'
            ' style="color:#58a6ff;text-decoration:none;">GitHub \u2197</a>'
        ))
        self.exportImportConfigButton.setText(_tr("MainWindow", "Export / Import Config"))
        self.processAudioCheckBox.setText(_tr("MainWindow", "Enable VHS Audio Effect"))

        self.image_frame.setText(_tr(
            "MainWindow",
            "No image or video loaded\nDrag & drop or open a file below"
        ))
        self.refreshFrameButton.setText(_tr("MainWindow", "\u21ba"))
        self.livePreviewCheckbox.setText(_tr("MainWindow", "Live Preview"))

        self.label_2.setText(_tr("MainWindow", "Height:"))
        self.seedLabel.setText(_tr("MainWindow", "Seed:"))

        self.NearestUpScale.setText(_tr("MainWindow", "\u00d72 Upscale"))
        self.ProMode.setText(_tr("MainWindow", "Pro Mode"))
        self.toggleMainEffect.setText(_tr("MainWindow", "Effect ON"))
        self.compareModeButton.setText(_tr("MainWindow", "Compare"))
        self.LossLessCheckBox.setText(_tr("MainWindow", "Lossless"))

        self.openFile.setText(_tr("MainWindow", "Open File  (video or image)"))
        self.openImageUrlButton.setText(_tr("MainWindow", "URL"))

        self.renderVideoButton.setText(_tr("MainWindow", "Render Video"))
        self.saveImageButton.setText(_tr("MainWindow", "Save Image"))
        self.pauseRenderButton.setText(_tr("MainWindow", "Pause"))
        self.stopRenderButton.setText(_tr("MainWindow", "Stop"))
