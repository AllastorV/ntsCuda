import os
import sys
import ctypes
from pathlib import Path

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QLibraryInfo
import darkdetect

from app import NtscApp
from app import logger
from ui.themes import DARK_THEME, LIGHT_THEME


def set_window_dark_titlebar(window, dark=True):
    """Set Windows title bar to dark/light mode using DWM API."""
    if sys.platform != 'win32':
        return
    try:
        hwnd = int(window.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)


def crash_handler(exc_type, value, tb):
    import traceback
    tb_text = ''.join(traceback.format_exception(exc_type, value, tb))
    logger.error("Uncaught exception:\n{0}".format(tb_text))
    sys.exit(1)


sys.excepthook = crash_handler


def main():
    translator = QtCore.QTranslator()
    locale = QtCore.QLocale.system().name()

    print("ntsCuda by AllastorV (based on ntscQT by JargeZ)")

    # Locale / translation loading
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).absolute().parent

    locale_file = str((base_dir / 'translate' / f'{locale}.qm').resolve())
    print(f"Try load {locale} locale: {locale_file}")
    if translator.load(locale_file):
        print(f'Localization loaded: {locale}')
    else:
        print("Using default translation")

    app = QtWidgets.QApplication(sys.argv)
    app.installTranslator(translator)

    # Apply professional theme — dark or light based on OS preference
    if darkdetect.isDark():
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)

    window = NtscApp()

    # Set window icon (assets/ is the canonical location)
    icon_candidates = [
        base_dir / 'assets' / 'ntsCuda_icon.ico',
        base_dir / 'assets' / 'icon.png',
        base_dir / 'ntsCuda_icon.ico',   # legacy fallback for older layouts
        base_dir / 'icon.png',
    ]
    for icon_path in icon_candidates:
        if icon_path.exists():
            app.setWindowIcon(QtGui.QIcon(str(icon_path)))
            break

    is_dark = darkdetect.isDark()
    set_window_dark_titlebar(window, dark=is_dark)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
