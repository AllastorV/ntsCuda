import json
from pathlib import Path
from random import randint
from typing import Tuple, Union, List, Dict
import requests
import cv2
import numpy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QSlider, QHBoxLayout, QLabel, QCheckBox, QInputDialog, QPushButton
from numpy import ndarray

from app.InterlacedRenderer import InterlacedRenderer
from app.config_dialog import ConfigDialog
from app.logs import logger
from app.Renderer import DefaultRenderer
from app.funcs import resize_to_height, pick_save_file, trim_to_4width, set_ui_element
from app.ntsc import random_ntsc, Ntsc
from app.cuda_utils import is_gpu_available
from ui import mainWindow
from ui.DoubleSlider import DoubleSlider


class TemplateLoader(QtCore.QThread):
    """Background thread — loads preset templates without blocking the UI."""
    templates_loaded = QtCore.pyqtSignal(dict)

    def run(self):
        try:
            res = requests.get(
                'https://raw.githubusercontent.com/JargeZ/vhs/master/builtin_templates.json',
                timeout=5,
            )
            if res.ok:
                self.templates_loaded.emit(json.loads(res.content))
        except Exception as e:
            logger.debug(f'Remote templates not loaded: {e}')


class NtscApp(QtWidgets.QMainWindow, mainWindow.Ui_MainWindow):
    def __init__(self):
        self.videoRenderer: DefaultRenderer = None
        self.current_frame: numpy.ndarray = False
        self.next_frame: numpy.ndarray = False
        self.scale_pixmap = False
        self.input_video = {}
        self.templates = {}
        self.orig_wh: Tuple[int, int] = (0, 0)
        self.compareMode: bool = False
        self.isRenderActive: bool = False
        self.mainEffect: bool = True
        self.loss_less_mode: bool = False
        self.__video_output_suffix = ".mp4"  # or .mkv for FFV1
        self.ProcessAudio: bool = False
        self.nt_controls = {}
        self.nt: Ntsc = None
        self.pro_mode_elements = []
        self._original_frame_for_export: numpy.ndarray = None
        super().__init__()
        self.supported_video_type = [
            '.mp4', '.mkv', '.avi', '.webm', '.mpg', '.mpeg', '.gif',
            '.mov', '.flv', '.wmv', '.ts', '.m4v', '.3gp', '.ogv',
            '.mxf', '.vob', '.m2ts', '.mts', '.f4v', '.rm', '.rmvb',
        ]
        self.supported_image_type = [
            '.png', '.jpg', '.jpeg', '.webp',
            '.bmp', '.tiff', '.tif', '.tga',
            '.ppm', '.pgm', '.pbm',
        ]
        self.setupUi(self)
        self.strings = {
            "_composite_preemphasis": self.tr("Composite preemphasis"),
            "_vhs_out_sharpen": self.tr("VHS out sharpen"),
            "_vhs_edge_wave": self.tr("Edge wave"),
            "_output_vhs_tape_speed": self.tr("VHS tape speed"),
            "_ringing": self.tr("Ringing"),
            "_ringing_power": self.tr("Ringing power"),
            "_ringing_shift": self.tr("Ringing shift"),
            "_freq_noise_size": self.tr("Freq noise size"),
            "_freq_noise_amplitude": self.tr("Freq noise amplitude"),
            "_color_bleed_horiz": self.tr("Color bleed horiz"),
            "_color_bleed_vert": self.tr("Color bleed vert"),
            "_video_chroma_noise": self.tr("Video chroma noise"),
            "_video_chroma_phase_noise": self.tr("Video chroma phase noise"),
            "_video_chroma_loss": self.tr("Video chroma loss"),
            "_video_noise": self.tr("Video noise"),
            "_video_scanline_phase_shift": self.tr("Video scanline phase shift"),
            "_video_scanline_phase_shift_offset": self.tr("Video scanline phase shift offset"),
            "_head_switching_speed": self.tr("Head switch move speed"),
            "_vhs_head_switching": self.tr("Head switching"),
            "_color_bleed_before": self.tr("Color bleed before"),
            "_enable_ringing2": self.tr("Enable ringing2"),
            "_composite_in_chroma_lowpass": self.tr("Composite in chroma lowpass"),
            "_composite_out_chroma_lowpass": self.tr("Composite out chroma lowpass"),
            "_composite_out_chroma_lowpass_lite": self.tr("Composite out chroma lowpass lite"),
            "_emulating_vhs": self.tr("VHS emulating"),
            "_nocolor_subcarrier": self.tr("Nocolor subcarrier"),
            "_vhs_chroma_vert_blend": self.tr("VHS chroma vert blend"),
            "_vhs_svideo_out": self.tr("VHS svideo out"),
            "_output_ntsc": self.tr("NTSC output"),
            "_black_line_cut": self.tr("Cut 2% black line"),
        }
        self.add_slider("_composite_preemphasis", 0, 10, float)
        self.add_slider("_vhs_out_sharpen", 1, 5)
        self.add_slider("_vhs_edge_wave", 0, 10)
        self.add_slider("_ringing", 0, 1, float, pro=True)
        self.add_slider("_ringing_power", 0, 10)
        self.add_slider("_ringing_shift", 0, 3, float, pro=True)
        self.add_slider("_freq_noise_size", 0, 2, float, pro=True)
        self.add_slider("_freq_noise_amplitude", 0, 5, pro=True)
        self.add_slider("_color_bleed_horiz", 0, 10)
        self.add_slider("_color_bleed_vert", 0, 10)
        self.add_slider("_video_chroma_noise", 0, 16384)
        self.add_slider("_video_chroma_phase_noise", 0, 50)
        self.add_slider("_video_chroma_loss", 0, 800)
        self.add_slider("_video_noise", 0, 4200)
        self.add_slider("_video_scanline_phase_shift", 0, 270, pro=True)
        self.add_slider("_video_scanline_phase_shift_offset", 0, 3, pro=True)

        self.add_slider("_head_switching_speed", 0, 100)

        self.add_checkbox("_vhs_head_switching", (1, 1))
        self.add_checkbox("_color_bleed_before", (1, 2), pro=True)
        self.add_checkbox("_enable_ringing2", (2, 1), pro=True)
        self.add_checkbox("_composite_in_chroma_lowpass", (2, 2), pro=True)
        self.add_checkbox("_composite_out_chroma_lowpass", (3, 1), pro=True)
        self.add_checkbox("_composite_out_chroma_lowpass_lite", (3, 2), pro=True)
        self.add_checkbox("_emulating_vhs", (4, 1))
        self.add_checkbox("_nocolor_subcarrier", (4, 2), pro=True)
        self.add_checkbox("_vhs_chroma_vert_blend", (5, 1), pro=True)
        self.add_checkbox("_vhs_svideo_out", (5, 2), pro=True)
        self.add_checkbox("_output_ntsc", (6, 1), pro=True)
        self.add_checkbox("_black_line_cut", (1, 2), pro=False)

        # ── Audio sliders ──────────────────────────────────────────────────
        self._add_audio_slider("audio_sat_beforevol", "Saturation Boost", 1.0, 10.0, 4.5)
        self._add_audio_slider("audio_lowpass", "Lowpass Cutoff (Hz)", 2000, 16000, 10896, is_int=True)
        self._add_audio_slider("audio_noise_volume", "Tape Noise Volume", 0.0, 0.3, 0.03)
        self._set_audio_controls_enabled(False)

        self.renderHeightBox.valueChanged.connect(
            lambda: self.set_current_frames(*self.get_current_video_frames())
        )
        self.openFile.clicked.connect(self.open_file)
        self.renderVideoButton.clicked.connect(self.render_video)
        self.saveImageButton.clicked.connect(self.render_image)
        self.stopRenderButton.clicked.connect(self.stop_render)
        self.compareModeButton.stateChanged.connect(self.toggle_compare_mode)
        self.toggleMainEffect.stateChanged.connect(self.toggle_main_effect)
        self.LossLessCheckBox.stateChanged.connect(self.lossless_exporting)
        self.processAudioCheckBox.stateChanged.connect(self.audio_filtering)
        self.pauseRenderButton.clicked.connect(self.toggle_pause_render)
        self.livePreviewCheckbox.stateChanged.connect(self.toggle_live_preview)
        self.refreshFrameButton.clicked.connect(self.nt_update_preview)
        self.openImageUrlButton.clicked.connect(self.open_image_by_url)
        self.exportImportConfigButton.clicked.connect(self.export_import_config)
        self.compareSlider.valueChanged.connect(self._on_compare_slider_changed)

        self.ProMode.clicked.connect(
            lambda: self.set_pro_mode(self.ProMode.isChecked())
        )

        self.seedSpinBox.valueChanged.connect(self.update_seed)

        # Enable drag & drop anywhere on the main window
        self.setAcceptDrops(True)

        presets = [18, 31, 38, 44]
        self.seedSpinBox.setValue(presets[randint(0, len(presets) - 1)])

        self.progressBar.setValue(0)
        self.progressBar.setMinimum(1)
        self.progressBar.hide()

        # ── CUDA indicator ─────────────────────────────────────────────────
        self._update_cuda_indicator()

        self.add_builtin_templates()

    # ── Audio UI helpers ─────────────────────────────────────────────────

    def _add_audio_slider(self, name, label_text, min_val, max_val, default, is_int=False):
        frame = QtWidgets.QFrame()
        frame.setObjectName("sliderCard")
        ly = QHBoxLayout(frame)
        ly.setContentsMargins(8, 4, 8, 4)
        ly.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("paramLabel")
        label.setMinimumWidth(130)

        if is_int:
            slider = QSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMinimum(int(min_val))
            slider.setMaximum(int(max_val))
            slider.setValue(int(default))
        else:
            slider = DoubleSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMaximum(max_val)
            slider.setMinimum(min_val)
            slider.setValue(default)

        slider.setObjectName(f"audio_{name}")

        value_label = QLabel(str(default)[:7])
        value_label.setObjectName("paramValue")
        value_label.setFixedWidth(80)
        value_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        if is_int:
            slider.valueChanged.connect(lambda v, vl=value_label: vl.setText(str(v)))
        else:
            slider.valueChanged.connect(lambda _, vl=value_label, s=slider: vl.setText(str(s.value())[:7]))

        ly.addWidget(label)
        ly.addWidget(slider, 1)
        ly.addWidget(value_label)

        self.audioSlidersLayout.addWidget(frame)

        if not hasattr(self, '_audio_sliders'):
            self._audio_sliders = {}
        self._audio_sliders[name] = slider

    def _set_audio_controls_enabled(self, enabled):
        if hasattr(self, '_audio_sliders'):
            for slider in self._audio_sliders.values():
                slider.setEnabled(enabled)

    def _get_audio_params(self):
        params = {}
        if hasattr(self, '_audio_sliders'):
            for name, slider in self._audio_sliders.items():
                params[name] = slider.value()
        return params

    def _update_cuda_indicator(self):
        if is_gpu_available():
            self.cudaIndicator.setText("CUDA")
            self.cudaIndicator.setStyleSheet(
                "background-color: #1a4a2a; color: #3fb950; border: 1px solid #238636; "
                "border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;"
            )
        else:
            self.cudaIndicator.setText("CPU")
            self.cudaIndicator.setStyleSheet(
                "background-color: #2d1b00; color: #e3b341; border: 1px solid #6b4f0d; "
                "border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;"
            )

    def _on_compare_slider_changed(self):
        if self.compareMode:
            self.nt_update_preview()

    def add_builtin_templates(self):
        local_path = Path(__file__).parent.parent / 'builtin_templates.json'
        if local_path.exists():
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    self._apply_templates(json.loads(f.read()))
            except Exception as e:
                logger.debug(f'Local templates load failed: {e}')

        self._template_loader = TemplateLoader()
        self._template_loader.templates_loaded.connect(self._apply_templates)
        self._template_loader.start()

    def _apply_templates(self, templates: dict):
        while self.templatesLayout.count():
            item = self.templatesLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.templates = templates
        for name, values in templates.items():
            button = QPushButton(name)
            set_values = (lambda v: lambda: self.nt_set_config(v))(values)
            button.clicked.connect(set_values)
            self.templatesLayout.addWidget(button)

    def get_render_class(self):
        is_interlaced = False
        if is_interlaced:
            return InterlacedRenderer
        else:
            return DefaultRenderer

    def setup_renderer(self):
        try:
            self.update_status("Terminating prev renderer")
            logger.debug("Terminating prev renderer")
            self.thread.quit()
            self.update_status("Waiting prev renderer")
            logger.debug("Waiting prev renderer")
            self.thread.wait()
        except AttributeError:
            logger.debug("Setup first renderer")
        self.thread = QtCore.QThread()
        RendererClass = self.get_render_class()
        self.videoRenderer = RendererClass()
        self.videoRenderer.moveToThread(self.thread)
        self.videoRenderer.newFrame.connect(self.render_preview)
        self.videoRenderer.frameMoved.connect(self.videoTrackSlider.setValue)
        self.videoRenderer.renderStateChanged.connect(self.set_render_state)
        self.videoRenderer.sendStatus.connect(self.update_status)
        self.videoRenderer.increment_progress.connect(self.increment_progress)
        self.thread.started.connect(self.videoRenderer.run)

    @QtCore.pyqtSlot()
    def stop_render(self):
        self.videoRenderer.stop()

    @QtCore.pyqtSlot()
    def increment_progress(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    @QtCore.pyqtSlot()
    def toggle_compare_mode(self):
        state = self.sender().isChecked()
        self.compareMode = state
        if state:
            self.compareSlider.show()
        else:
            self.compareSlider.hide()
        self.nt_update_preview()

    @QtCore.pyqtSlot()
    def toggle_pause_render(self):
        button = self.sender()
        if not self.isRenderActive:
            self.update_status("Render is not running")
            button.setChecked(False)
            return None
        state = button.isChecked()
        self.videoRenderer.pause = state

    def toggle_live_preview(self):
        button = self.sender()
        state = button.isChecked()
        try:
            self.videoRenderer.liveView = state
        except AttributeError:
            pass

    @QtCore.pyqtSlot()
    def toggle_main_effect(self):
        state = self.toggleMainEffect.isChecked()
        self.mainEffect = state
        try:
            self.videoRenderer.mainEffect = state
        except AttributeError:
            pass
        self.nt_update_preview()

    @QtCore.pyqtSlot()
    def lossless_exporting(self):
        lossless_state = self.LossLessCheckBox.isChecked()
        self.loss_less_mode = lossless_state
        self.__video_output_suffix = '.mkv' if lossless_state else '.mp4'
        try:
            self.videoRenderer.lossless = lossless_state
            logger.debug(f"Lossless: {str(lossless_state)}")
        except AttributeError:
            pass

    def audio_filtering(self):
        state = self.processAudioCheckBox.isChecked()
        self.ProcessAudio = state
        self._set_audio_controls_enabled(state)
        try:
            self.videoRenderer.audio_process = state
            if state and hasattr(self, '_audio_sliders'):
                params = self._get_audio_params()
                self.videoRenderer.audio_sat_beforevol = params.get('audio_sat_beforevol', 4.5)
                self.videoRenderer.audio_lowpass = int(params.get('audio_lowpass', 10896))
                self.videoRenderer.audio_noise_volume = params.get('audio_noise_volume', 0.03)
            logger.debug(f"Process audio: {str(state)}")
        except AttributeError:
            pass

    @QtCore.pyqtSlot(int)
    def update_seed(self, seed):
        self.nt = random_ntsc(seed)
        self.nt._enable_ringing2 = True
        self.sync_nt_to_sliders()

    @QtCore.pyqtSlot(str)
    def update_status(self, string):
        logger.info('[GUI STATUS] ' + string)
        self.statusLabel.setText(string)

    @QtCore.pyqtSlot(bool)
    def set_render_state(self, is_render_active):
        self.isRenderActive = is_render_active

        self.videoTrackSlider.blockSignals(is_render_active)

        self.openFile.setEnabled(not is_render_active)
        self.renderVideoButton.setEnabled(not is_render_active)
        self.stopRenderButton.setEnabled(is_render_active)

        self.seedSpinBox.setEnabled(not is_render_active)

        if is_render_active:
            self.progressBar.show()
        else:
            self.progressBar.hide()
            # Sync current_frame to the slider position after render finishes
            if self.input_video:
                self.set_current_frames(*self.get_current_video_frames())

        self.NearestUpScale.setEnabled(not is_render_active)

    def sync_nt_to_sliders(self):
        for parameter_name, element in self.nt_controls.items():
            value = getattr(self.nt, parameter_name)

            if isinstance(element, QSlider) and isinstance(value, float):
                value = int(value)

            set_ui_element(element, value)

            related_label = element.parent().findChild(QLabel, parameter_name)
            if related_label:
                related_label.setText(str(value)[:7])

            logger.debug(f"set {type(value)} {parameter_name} slider to {value}")
        self.nt_update_preview()

    def value_changed_slot(self):
        element = self.sender()
        parameter_name = element.objectName()
        if isinstance(element, (QSlider, DoubleSlider)):
            value = element.value()
            related_label = element.parent().findChild(QLabel, parameter_name)
            if related_label:
                related_label.setText(str(value)[:7])
        elif isinstance(element, QCheckBox):
            value = element.isChecked()

        logger.debug(f"Set {parameter_name} to {value}")
        setattr(self.nt, parameter_name, value)
        self.nt_update_preview()

    def add_checkbox(self, param_name, pos, pro=False):
        checkbox = QCheckBox()
        checkbox.setText(self.strings[param_name])
        checkbox.setObjectName(param_name)
        checkbox.stateChanged.connect(self.value_changed_slot)
        self.nt_controls[param_name] = checkbox
        self.checkboxesLayout.addWidget(checkbox, pos[0], pos[1])

        if pro:
            self.pro_mode_elements.append(checkbox)
            checkbox.hide()

    @QtCore.pyqtSlot(bool)
    def set_pro_mode(self, state):
        for frame in self.pro_mode_elements:
            if state:
                frame.show()
            else:
                frame.hide()

    def add_slider(self, param_name, min_val, max_val, slider_value_type: Union[int, float] = int, pro=False):
        slider_frame = QtWidgets.QFrame()
        slider_frame.setObjectName("sliderCard")
        ly = QHBoxLayout(slider_frame)
        ly.setContentsMargins(8, 4, 8, 4)
        ly.setSpacing(4)

        if pro:
            self.pro_mode_elements.append(slider_frame)
            slider_frame.hide()

        if slider_value_type is int:
            slider = QSlider()
            slider.valueChanged.connect(self.value_changed_slot)
        else:
            slider = DoubleSlider()
            slider.mouseRelease.connect(self.value_changed_slot)

        slider.blockSignals(True)
        slider.setEnabled(True)
        slider.setMaximum(max_val)
        slider.setMinimum(min_val)
        slider.setMouseTracking(False)
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setObjectName(param_name)
        slider.blockSignals(False)

        label = QLabel(self.strings[param_name])
        label.setObjectName("paramLabel")
        label.setMinimumWidth(120)
        label.setMaximumWidth(170)
        label.setMinimumHeight(38)

        value_label = QLabel()
        value_label.setObjectName(param_name)
        value_label.setProperty("ntsc_param", param_name)
        value_label.setFixedWidth(80)
        value_label.setMinimumHeight(38)
        value_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        ly.addWidget(label)
        ly.addWidget(slider, 1)
        ly.addWidget(value_label)

        self.nt_controls[param_name] = slider
        self.slidersLayout.addWidget(slider_frame)

    def get_current_video_frames(self):
        preview_h = self.renderHeightBox.value()
        if not self.input_video or preview_h < 10:
            return None, None
        frame_no = self.videoTrackSlider.value()
        self.input_video["cap"].set(1, frame_no)
        ret, frame1 = self.input_video["cap"].read()

        ret, frame2 = self.input_video["cap"].read()
        if not ret:
            frame2 = frame1

        return frame1, frame2

    def resize_to_preview_frame(self, frame):
        preview_h = self.renderHeightBox.value()
        try:
            crop_wh = resize_to_height(self.orig_wh, preview_h)
            frame = cv2.resize(frame, crop_wh)
        except ZeroDivisionError:
            self.update_status("ZeroDivisionError :DDDDDD")

        if frame.shape[1] % 4 != 0:
            frame = trim_to_4width(frame)

        return frame

    def set_current_frames(self, frame1: ndarray, frame2=None):
        current_frame_valid = isinstance(frame1, ndarray)
        preview_h = self.renderHeightBox.value()
        if not current_frame_valid or preview_h < 10:
            self.update_status("Trying to set invalid current frame")
            return None

        if frame2 is None:
            frame2 = frame1.copy()

        # Keep the original (full-res) frame for export
        self._original_frame_for_export = frame1.copy()

        self.current_frame = self.resize_to_preview_frame(frame1)
        self.next_frame = self.resize_to_preview_frame(frame2)

        self.nt_update_preview()

    @QtCore.pyqtSlot()
    def open_image_by_url(self):
        url, ok = QInputDialog.getText(self, self.tr('Open image by url'), self.tr('Image url:'))
        if ok:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, img = cap.read()
                self.set_image_mode()
                self.open_image(img)
            else:
                self.update_status(self.tr('Error opening image url :('))
                return None

    # ------------------------------------------------------------------ #
    #  Drag & drop                                                         #
    # ------------------------------------------------------------------ #

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                suffix = Path(urls[0].toLocalFile()).suffix.lower()
                all_supported = self.supported_video_type + self.supported_image_type
                if suffix in all_supported:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = Path(urls[0].toLocalFile())
        suffix = path.suffix.lower()
        if suffix in self.supported_video_type:
            self.set_video_mode()
            self.open_video(path)
        elif suffix in self.supported_image_type:
            img = cv2.imdecode(numpy.fromfile(path, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            self.set_image_mode()
            self.open_image(img)
        else:
            self.update_status(f"Unsupported file type {suffix}")

    def open_file(self):
        all_exts = self.supported_video_type + self.supported_image_type
        all_filter = 'All Supported Files (' + ' '.join(f'*{e}' for e in all_exts) + ')'
        video_filter = 'Video Files (' + ' '.join(f'*{e}' for e in self.supported_video_type) + ')'
        image_filter = 'Image Files (' + ' '.join(f'*{e}' for e in self.supported_image_type) + ')'
        file_filter = f'{all_filter};;{video_filter};;{image_filter};;All Files (*)'
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", '', file_filter)
        if file:
            path = Path(file[0])
        else:
            return None
        file_suffix = path.suffix.lower()
        if file_suffix in self.supported_video_type:
            self.set_video_mode()
            self.open_video(path)
        elif file_suffix in self.supported_image_type:
            img = cv2.imdecode(numpy.fromfile(path, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            self.set_image_mode()
            self.open_image(img)
        else:
            self.update_status(f"Unsupported file type {file_suffix}")

    def set_video_mode(self):
        self.videoTrackSlider.blockSignals(False)
        self.videoTrackSlider.show()
        self.pauseRenderButton.show()
        self.stopRenderButton.show()
        self.livePreviewCheckbox.show()
        self.renderVideoButton.show()

    def set_image_mode(self):
        self.videoTrackSlider.blockSignals(True)
        self.videoTrackSlider.hide()
        self.pauseRenderButton.hide()
        self.stopRenderButton.hide()
        self.livePreviewCheckbox.hide()
        self.renderVideoButton.hide()

    def set_render_heigth(self, height):
        if height > 600:
            self.renderHeightBox.setValue(600)
            self.update_status(
                self.tr('The image resolution is large. For the best effect, the output height is set to 600'))
        else:
            self.renderHeightBox.setValue(height // 120 * 120)

    def open_image(self, img: numpy.ndarray):
        self.setup_renderer()
        height, width, channels = img.shape
        self.orig_wh = width, height

        self.set_render_heigth(height)

        self.set_current_frames(img)

    def nt_get_config(self):
        values = {}
        element: Union[QCheckBox, QSlider, DoubleSlider]
        for parameter_name, element in self.nt_controls.items():
            if isinstance(element, QCheckBox):
                value = element.isChecked()
            elif isinstance(element, (QSlider, DoubleSlider)):
                value = element.value()

            values[parameter_name] = value

        return values

    def nt_set_config(self, values: List[Dict[str, Union[int, float]]]):
        for parameter_name, value in values.items():
            setattr(self.nt, parameter_name, value)

        self.sync_nt_to_sliders()

    def open_video(self, path: Path):
        self.setup_renderer()
        logger.debug(f"file: {path}")
        cap = cv2.VideoCapture(str(path.resolve()))
        logger.debug(f"cap: {cap} isOpened: {cap.isOpened()}")
        self.input_video = {
            "cap": cap,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "frames_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "orig_fps": cap.get(cv2.CAP_PROP_FPS),
            "path": path,
            "suffix": path.suffix.lower(),
        }
        logger.debug(f"selfinput: {self.input_video}")
        self.orig_wh = (int(self.input_video["width"]), int(self.input_video["height"]))
        self.set_render_heigth(self.input_video["height"])
        self.set_current_frames(*self.get_current_video_frames())
        self.videoTrackSlider.setMinimum(1)
        self.videoTrackSlider.setMaximum(self.input_video["frames_count"])
        try:
            self.videoTrackSlider.valueChanged.disconnect()
        except TypeError:
            pass
        self.videoTrackSlider.valueChanged.connect(
            lambda: self.set_current_frames(*self.get_current_video_frames())
        )
        self.progressBar.setMaximum(self.input_video["frames_count"])

    def render_image(self):
        image_save_formats = ['.png', '.jpg', '.bmp', '.tiff', '.webp']
        fmt_filter = ';;'.join(
            [f'{ext.upper()[1:]} (*{ext})' for ext in image_save_formats]
        ) + ';;All Files (*)'
        target_file_raw = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save image as', '', fmt_filter
        )
        if not target_file_raw[0]:
            return None

        # For video: re-read the frame at the current slider position so we
        # always export the frame the user is currently viewing.
        if self.input_video:
            frame1, frame2 = self.get_current_video_frames()
            if not isinstance(frame1, ndarray):
                self.update_status("Cannot read current frame")
                return None
            export_frame = frame1
        elif isinstance(self._original_frame_for_export, ndarray):
            export_frame = self._original_frame_for_export
        elif isinstance(self.current_frame, ndarray):
            export_frame = self.current_frame
        else:
            return None

        target_file = Path(target_file_raw[0])
        suffix = target_file.suffix.lower()
        if suffix not in image_save_formats:
            suffix = '.png'
            target_file = target_file.parent / (target_file.name + suffix)

        render_h = self.renderHeightBox.value()
        crop_wh = resize_to_height(self.orig_wh, render_h)
        image = cv2.resize(export_frame, crop_wh)
        if image.shape[1] % 4 != 0:
            image = trim_to_4width(image)

        if self.videoRenderer is None:
            self.setup_renderer()

        image = self.videoRenderer.apply_main_effect(self.nt, frame1=image)

        # Apply 2x upscale if enabled
        if self.NearestUpScale.isChecked():
            h, w = image.shape[:2]
            image = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)

        encode_params = []
        if suffix in ('.jpg', '.jpeg'):
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
        elif suffix == '.webp':
            encode_params = [cv2.IMWRITE_WEBP_QUALITY, 90]

        is_success, im_buf_arr = cv2.imencode(suffix, image, encode_params)
        if not is_success:
            self.update_status("Error while saving (!is_success)")
            return None
        im_buf_arr.tofile(target_file)
        self.update_status(f"Image saved: {target_file.name}")

    def render_video(self):
        if not self.input_video:
            self.update_status("No video loaded \u2014 open a video file first")
            return None
        if self.input_video.get('suffix') == ".gif":
            suffix = self.input_video['suffix']
        else:
            suffix = self.__video_output_suffix
        target_file = pick_save_file(self, title='Render video as', suffix=suffix)
        if not target_file:
            return None
        render_data = {
            "target_file": target_file,
            "nt": self.nt,
            "input_video": self.input_video,
            "input_heigth": self.renderHeightBox.value(),
            "upscale_2x": self.NearestUpScale.isChecked(),
        }
        self.setup_renderer()
        self.toggle_main_effect()
        self.lossless_exporting()
        self.audio_filtering()
        self.progressBar.setValue(1)
        self.videoRenderer.render_data = render_data
        self.thread.start()

    def nt_process(self, frame) -> ndarray:
        _ = self.nt.composite_layer(frame, frame, field=0, fieldno=0)
        ntsc_out_image = cv2.convertScaleAbs(_)
        ntsc_out_image[1:-1:2] = ntsc_out_image[0:-2:2] / 2 + ntsc_out_image[2::2] / 2
        return ntsc_out_image

    def nt_update_preview(self):
        current_frame_valid = isinstance(self.current_frame, ndarray)
        render_on_pause = self.pauseRenderButton.isChecked()
        if not current_frame_valid or (self.isRenderActive and not render_on_pause):
            return None

        if not self.mainEffect:
            self.render_preview(self.current_frame)
            return None

        if self.videoRenderer is None:
            return None

        ntsc_out_image = self.videoRenderer.apply_main_effect(self.nt, self.current_frame, self.next_frame)

        if self.compareMode:
            # Vertical split: left = original, right = processed
            split_ratio = self.compareSlider.value() / 100.0
            w = self.current_frame.shape[1]
            split_x = int(w * split_ratio)
            combined = ntsc_out_image.copy()
            combined[:, :split_x] = self.current_frame[:, :split_x]
            # Draw a thin white line at the split position
            if 0 < split_x < w:
                combined[:, max(0, split_x - 1):split_x + 1] = 255
            ntsc_out_image = combined

        self.render_preview(ntsc_out_image)

    def export_import_config(self):
        config = self.nt_get_config()
        config_json = json.dumps(config, indent=2)

        dialog = ConfigDialog()
        dialog.configJsonTextField.setPlainText(config_json)
        dialog.configJsonTextField.selectAll()

        code = dialog.exec_()
        if code:
            config_json = dialog.configJsonTextField.toPlainText()
            config = json.loads(config_json)
            self.nt_set_config(config)

    @QtCore.pyqtSlot(object)
    def render_preview(self, img: ndarray):
        height, width, _ = img.shape
        totalBytes = img.nbytes
        bytesPerLine = int(totalBytes / height)

        image = QtGui.QImage(img.tobytes(), width, height, bytesPerLine, QtGui.QImage.Format_RGB888) \
            .rgbSwapped()

        pixmap = QtGui.QPixmap.fromImage(image)
        label_size = self.image_frame.size()
        scaled = pixmap.scaled(label_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.image_frame.setPixmap(scaled)
