# Professional dark and light themes for ntsCuda
# Modern cyberpunk-inspired palette with cohesive color harmony

DARK_THEME = """
/* ────── Base ────── */
QMainWindow, QDialog {
    background-color: #0a0e14;
    color: #e0e4eb;
}
QWidget {
    background-color: transparent;
    color: #e0e4eb;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
}

/* ────── Left Panel ────── */
#leftPanel {
    background-color: #111820;
    min-width: 320px;
    max-width: 440px;
}
#panelHeader {
    background-color: #111820;
    border-bottom: 1px solid #1e2a3a;
}
#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #00d4aa;
    padding: 2px 0;
    letter-spacing: 1px;
}
#githubLink {
    font-size: 13px;
}
#cudaIndicator {
    font-size: 12px;
    font-weight: bold;
    border-radius: 4px;
    padding: 2px 8px;
}
#controlsScroll {
    border: none;
    background-color: transparent;
}
#scrollContent {
    background-color: transparent;
}
QScrollBar:vertical {
    background: #111820;
    width: 5px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #1e2a3a;
    border-radius: 2px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #00d4aa;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

/* ────── Section Headers ────── */
#sectionHeader {
    color: #4a5568;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1.5px;
    padding: 12px 4px 4px 4px;
    border-bottom: 1px solid #1a2332;
}

/* ────── Slider Cards ────── */
#sliderCard {
    background-color: #131a24;
    border: 1px solid #1a2332;
    border-radius: 6px;
    margin: 1px 0;
    min-height: 48px;
}
#sliderCard:hover {
    border-color: #00d4aa40;
    background-color: #151d28;
}
#paramLabel {
    color: #7a8599;
    font-size: 14px;
    min-height: 48px;
}
#paramValue {
    color: #00d4aa;
    font-size: 14px;
    font-weight: bold;
    min-width: 80px;
    min-height: 48px;
    qproperty-alignment: AlignRight;
}

/* ────── Audio Section ────── */
#audioSection {
    background-color: transparent;
}

/* ────── Sliders ────── */
QSlider::groove:horizontal {
    background: #1a2332;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #00d4aa;
    border: 2px solid #0a0e14;
    width: 14px;
    height: 14px;
    border-radius: 8px;
    margin: -5px 0;
}
QSlider::handle:horizontal:hover {
    background: #00f5c4;
    border-color: #00d4aa40;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #006b55,
        stop:1 #00d4aa
    );
    border-radius: 2px;
}
QSlider::sub-page:horizontal:disabled {
    background: #1a2332;
}

/* ────── Checkboxes ────── */
QCheckBox {
    spacing: 6px;
    color: #b8c0cc;
    font-size: 14px;
    padding: 2px 0;
    min-height: 48px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #2a3545;
    background: #0a0e14;
}
QCheckBox::indicator:checked {
    background-color: #00d4aa;
    border-color: #00f5c4;
    image: url(none);
}
QCheckBox::indicator:hover {
    border-color: #00d4aa;
}
QCheckBox::indicator:checked:hover {
    background-color: #00f5c4;
}

/* ────── Buttons ────── */
QPushButton {
    background-color: #151d28;
    color: #b8c0cc;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 14px;
    min-height: 48px;
}
QPushButton:hover {
    background-color: #1a2535;
    border-color: #00d4aa60;
    color: #e0e4eb;
}
QPushButton:pressed {
    background-color: #111820;
    border-color: #00d4aa;
}
QPushButton:disabled {
    color: #3a4555;
    border-color: #151d28;
    background-color: #0d1219;
}
QPushButton:checked {
    background-color: #0a2a22;
    border-color: #00d4aa;
    color: #00f5c4;
}
QPushButton:focus {
    border-color: #00d4aa80;
    outline: none;
}

/* Render Video — primary action */
#renderVideoButton {
    background-color: #0a2a22;
    color: #00d4aa;
    border-color: #006b55;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 14px;
}
#renderVideoButton:hover {
    background-color: #0d3a2e;
    border-color: #00d4aa;
    color: #00f5c4;
}
#renderVideoButton:pressed {
    background-color: #082018;
}
#renderVideoButton:disabled {
    background-color: #0d1219;
    color: #2a3a35;
    border-color: #151d28;
}

/* Save Image */
#saveImageButton {
    background-color: #151d28;
    color: #6cb4ee;
    border-color: #1e3a5a;
}
#saveImageButton:hover {
    background-color: #1a2a40;
    border-color: #6cb4ee;
}

/* Stop — danger action */
#stopRenderButton {
    background-color: #2a1216;
    color: #ff6b6b;
    border-color: #5a2228;
}
#stopRenderButton:hover {
    background-color: #3a181e;
    border-color: #ff6b6b;
}
#stopRenderButton:disabled {
    background-color: #0d1219;
    color: #3a4555;
    border-color: #151d28;
}

/* Open File */
#openFile {
    font-weight: bold;
    padding: 7px 14px;
}

/* Export / Import config */
#exportImportConfigButton {
    text-align: left;
    padding: 6px 10px;
    color: #5a6a7a;
    border: 1px dashed #1e2a3a;
}
#exportImportConfigButton:hover {
    color: #e0e4eb;
    border-color: #4a5a6a;
}

/* Pause render */
#pauseRenderButton:checked {
    background-color: #2a2510;
    color: #ffc857;
    border-color: #8a7520;
}

QToolButton {
    background-color: #151d28;
    color: #b8c0cc;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    padding: 5px 10px;
}
QToolButton:hover {
    background-color: #1a2535;
    border-color: #00d4aa60;
}

/* ────── SpinBox ────── */
QSpinBox, QDoubleSpinBox {
    background-color: #0a0e14;
    color: #e0e4eb;
    border: 1.5px solid #1e2a3a;
    border-radius: 5px;
    padding: 4px 6px;
    font-size: 14px;
    min-height: 38px;
    selection-background-color: #00d4aa;
    selection-color: #0a0e14;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00d4aa;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #151d28;
    border: none;
    width: 18px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background: #1e2a3a;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    width: 6px;
    height: 6px;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid #5a6a7a;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    width: 6px;
    height: 6px;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid #5a6a7a;
}

/* ────── Preview Area ────── */
#image_frame {
    background-color: #0a0e14;
    border: none;
    color: #3a4555;
    font-size: 13px;
}

/* ────── Compare Slider ────── */
#compareSlider::groove:horizontal {
    background: #1a2332;
    height: 6px;
    border-radius: 3px;
}
#compareSlider::handle:horizontal {
    background: #ffc857;
    border: 2px solid #0a0e14;
    width: 16px;
    height: 16px;
    border-radius: 9px;
    margin: -5px 0;
}
#compareSlider::handle:horizontal:hover {
    background: #ffe08a;
}
#compareSlider::sub-page:horizontal {
    background: #4a3a10;
    border-radius: 3px;
}

/* ────── Video Track Slider ────── */
#videoTrackSlider::groove:horizontal {
    background: #1a2332;
    height: 4px;
    border-radius: 2px;
}
#videoTrackSlider::handle:horizontal {
    background: #ffc857;
    border: 2px solid #0a0e14;
    width: 14px;
    height: 14px;
    border-radius: 8px;
    margin: -5px 0;
}
#videoTrackSlider::handle:horizontal:hover {
    background: #ffe08a;
}
#videoTrackSlider::sub-page:horizontal {
    background: #4a3a10;
    border-radius: 2px;
}

/* ────── Status & Progress ────── */
#statusLabel {
    color: #4a5568;
    font-size: 13px;
    padding: 1px 4px;
}
QProgressBar {
    background-color: #111820;
    border: 1px solid #1a2332;
    border-radius: 5px;
    color: #7a8599;
    text-align: center;
    font-size: 12px;
    max-height: 20px;
}
QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #006b55,
        stop:0.5 #00d4aa,
        stop:1 #00f5c4
    );
    border-radius: 5px;
}

/* ────── Dividers & Separators ────── */
#panelDivider {
    color: #1a2332;
    max-width: 1px;
}
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #1a2332;
}

/* ────── Refresh button ────── */
#refreshFrameButton {
    padding: 2px 4px;
    font-size: 14px;
    min-width: 26px;
    max-width: 28px;
}

/* ────── Config Dialog ────── */
QDialog {
    background-color: #0a0e14;
}
QPlainTextEdit, QTextEdit {
    background-color: #111820;
    color: #e0e4eb;
    border: 1.5px solid #1e2a3a;
    border-radius: 5px;
    font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
    font-size: 12px;
    selection-background-color: #00d4aa;
    selection-color: #0a0e14;
}
QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #00d4aa;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
    padding: 5px 16px;
}

/* ────── Labels ────── */
QLabel {
    color: #e0e4eb;
    background: transparent;
}
#label_2, #seedLabel {
    color: #5a6a7a;
    font-size: 14px;
    min-height: 48px;
}
"""


LIGHT_THEME = """
/* ────── Base ────── */
QMainWindow, QDialog {
    background-color: #f4f6f9;
    color: #1a2233;
}
QWidget {
    background-color: transparent;
    color: #1a2233;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
}

/* ────── Left Panel ────── */
#leftPanel {
    background-color: #ffffff;
    min-width: 320px;
    max-width: 440px;
}
#panelHeader {
    background-color: #f8fafb;
    border-bottom: 1px solid #dfe4ea;
}
#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #00a383;
    padding: 2px 0;
    letter-spacing: 1px;
}
#cudaIndicator {
    font-size: 12px;
    font-weight: bold;
    border-radius: 4px;
    padding: 2px 8px;
}
#controlsScroll {
    border: none;
    background-color: transparent;
}
#scrollContent {
    background-color: transparent;
}
QScrollBar:vertical {
    background: #f4f6f9;
    width: 5px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #ccd2da;
    border-radius: 2px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #00a383;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

/* ────── Section Headers ────── */
#sectionHeader {
    color: #8a94a6;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1.5px;
    padding: 12px 4px 4px 4px;
    border-bottom: 1px solid #e8ecf1;
}

/* ────── Slider Cards ────── */
#sliderCard {
    background-color: #ffffff;
    border: 1px solid #e8ecf1;
    border-radius: 6px;
    margin: 1px 0;
    min-height: 48px;
}
#sliderCard:hover {
    border-color: #00a38360;
}
#paramLabel {
    color: #5a6577;
    font-size: 14px;
    min-height: 48px;
}
#paramValue {
    color: #00a383;
    font-size: 14px;
    font-weight: bold;
    min-width: 80px;
    min-height: 48px;
    qproperty-alignment: AlignRight;
}

/* ────── Audio Section ────── */
#audioSection {
    background-color: transparent;
}

/* ────── Sliders ────── */
QSlider::groove:horizontal {
    background: #dfe4ea;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #00a383;
    border: 2px solid #f4f6f9;
    width: 14px;
    height: 14px;
    border-radius: 8px;
    margin: -5px 0;
}
QSlider::handle:horizontal:hover {
    background: #00c49e;
}
QSlider::sub-page:horizontal {
    background: #00a383;
    border-radius: 2px;
}

/* ────── Checkboxes ────── */
QCheckBox {
    spacing: 6px;
    color: #1a2233;
    font-size: 14px;
    padding: 2px 0;
    min-height: 48px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #ccd2da;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #00a383;
    border-color: #00a383;
}
QCheckBox::indicator:hover {
    border-color: #00a383;
}

/* ────── Buttons ────── */
QPushButton {
    background-color: #f4f6f9;
    color: #1a2233;
    border: 1px solid #dfe4ea;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 14px;
    min-height: 48px;
}
QPushButton:hover {
    background-color: #eaeff4;
    border-color: #00a38380;
    color: #00a383;
}
QPushButton:pressed {
    background-color: #dce4ef;
    border-color: #00a383;
}
QPushButton:disabled {
    color: #a0aab5;
    border-color: #eaeff4;
}
QPushButton:checked {
    background-color: #e0f5ee;
    border-color: #00a383;
    color: #00a383;
}

/* Render Video */
#renderVideoButton {
    background-color: #e0f5ee;
    color: #007d62;
    border-color: #80d4b8;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 14px;
}
#renderVideoButton:hover {
    background-color: #b8eadb;
    border-color: #007d62;
}
#renderVideoButton:disabled {
    background-color: #f4f6f9;
    color: #a0aab5;
    border-color: #dfe4ea;
}

/* Save Image */
#saveImageButton {
    color: #3a7bd5;
    border-color: #b8d4f0;
}
#saveImageButton:hover {
    background-color: #e8f0fa;
    border-color: #3a7bd5;
}

/* Stop */
#stopRenderButton {
    background-color: #fde8e8;
    color: #d32f2f;
    border-color: #f5b8b8;
}
#stopRenderButton:hover {
    background-color: #f5b8b8;
    border-color: #d32f2f;
}
#stopRenderButton:disabled {
    background-color: #f4f6f9;
    color: #a0aab5;
    border-color: #dfe4ea;
}

#openFile {
    font-weight: bold;
    padding: 7px 14px;
}
#exportImportConfigButton {
    text-align: left;
    padding: 6px 10px;
    color: #5a6577;
    border: 1px dashed #dfe4ea;
}
#exportImportConfigButton:hover {
    color: #1a2233;
    border-color: #a0aab5;
    background-color: #f8fafb;
}
#pauseRenderButton:checked {
    background-color: #fff8e0;
    color: #8a6d00;
    border-color: #d4a72c;
}

QToolButton {
    background-color: #f4f6f9;
    color: #1a2233;
    border: 1px solid #dfe4ea;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 48px;
}
QToolButton:hover {
    background-color: #eaeff4;
    border-color: #00a38380;
}

/* ────── SpinBox ────── */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #1a2233;
    border: 1.5px solid #dfe4ea;
    border-radius: 5px;
    padding: 4px 6px;
    font-size: 14px;
    min-height: 38px;
    selection-background-color: #00a383;
    selection-color: #ffffff;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00a383;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #f4f6f9;
    border: none;
    width: 18px;
}

/* ────── Preview Area ────── */
#image_frame {
    background-color: #f4f6f9;
    border: none;
    color: #a0aab5;
    font-size: 14px;
}

/* ────── Compare Slider ────── */
#compareSlider::groove:horizontal {
    background: #dfe4ea;
    height: 6px;
    border-radius: 3px;
}
#compareSlider::handle:horizontal {
    background: #d4a72c;
    border: 2px solid #f4f6f9;
    width: 16px;
    height: 16px;
    border-radius: 9px;
    margin: -5px 0;
}
#compareSlider::sub-page:horizontal {
    background: #e8d88a;
    border-radius: 3px;
}

/* ────── Video Track Slider ────── */
#videoTrackSlider::groove:horizontal {
    background: #dfe4ea;
    height: 4px;
    border-radius: 2px;
}
#videoTrackSlider::handle:horizontal {
    background: #d4a72c;
    border: 2px solid #f4f6f9;
    width: 14px;
    height: 14px;
    border-radius: 8px;
    margin: -5px 0;
}
#videoTrackSlider::sub-page:horizontal {
    background: #d4a72c;
    border-radius: 2px;
}

/* ────── Status & Progress ────── */
#statusLabel {
    color: #5a6577;
    font-size: 13px;
    padding: 1px 4px;
}
QProgressBar {
    background-color: #eaeff4;
    border: 1px solid #dfe4ea;
    border-radius: 5px;
    color: #5a6577;
    text-align: center;
    font-size: 12px;
    max-height: 20px;
}
QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00a383,
        stop:1 #007d62
    );
    border-radius: 5px;
}

/* ────── Dividers ────── */
#panelDivider {
    color: #dfe4ea;
    max-width: 1px;
}
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #dfe4ea;
}

#refreshFrameButton {
    padding: 2px 4px;
    font-size: 16px;
    min-width: 26px;
    max-width: 28px;
}

/* ────── Config Dialog ────── */
QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    color: #1a2233;
    border: 1.5px solid #dfe4ea;
    border-radius: 5px;
    font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
    font-size: 13px;
    selection-background-color: #00a383;
    selection-color: #ffffff;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
    padding: 5px 16px;
}

/* ────── Labels ────── */
QLabel {
    color: #1a2233;
    background: transparent;
}
#label_2, #seedLabel {
    color: #5a6577;
    font-size: 14px;
    min-height: 48px;
}
"""
