from __future__ import annotations

import sys
import threading
from pathlib import Path

from PySide6.QtCore import (
    QObject, QRunnable, QSettings, Qt, QThreadPool, Signal,
    QTimer, QSize
)
from PySide6.QtGui import (
    QPixmap, QFont, QColor, QIcon, QPainter, QPen, QBrush
)
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget, QFrame, QScrollArea,
    QComboBox, QSlider, QCheckBox, QToolButton, QSystemTrayIcon, QMenu
)

from processor import (
    DEFAULT_TEXT, PreviewConfig, preview_jpeg_bytes, process_folder,
    SUPPORTED_EXTENSIONS, SUPPORTED_3D_EXTENSIONS, SUPPORTED_CAD_EXTENSIONS
)


# ──────────────────────────────────────────────────────────────────────
# Theme Definitions
# ──────────────────────────────────────────────────────────────────────
LIGHT = "light"
DARK = "dark"

THEME = {
    LIGHT: {
        "bg":           "#D6E6EF",
        "card_bg":      "#EBF3F8",
        "card_border":  "#BACED9",
        "text":         "#1C2E38",
        "text_sec":     "#46606F",
        "text_muted":   "#6A8594",
        "field_bg":     "#EBF3F8",
        "field_border": "#BACED9",
        "field_focus":  "#7FA6B8",
        "accent":       "#7FA6B8",
        "accent_hover": "#6A93A6",
        "accent_press": "#558094",
        "danger":       "#E05252",
        "danger_hover": "rgba(224, 82, 82, 0.10)",
        "chip_bg":      "#D6E6EF",
        "chip_border":  "#BACED9",
        "chip_hover":   "#C6DAE5",
        "scroll_bg":    "#D6E6EF",
        "scroll_handle":"#BACED9",
        "scroll_hover": "#7FA6B8",
        "slider_track": "#BACED9",
        "slider_fill":  "#7FA6B8",
        "slider_knob":  "#EBF3F8",
        "check_border": "#A0BAC8",
        "check_active": "#7FA6B8",
        "preview_bg":   "#EBF3F8",
        "preview_bdr":  "#BACED9",
        "success_bg":   "#D1FAE5",
        "success_fg":   "#065F46",
        "fail_bg":      "#FEE2E2",
        "fail_fg":      "#991B1B",
        "info_bg":      "#D6E6EF",
        "info_fg":      "#1E4E63",
        "disabled_fg":  "#8FA7B5",
        "disabled_bg":  "#D6E6EF",
        "dropdown_arr": "#46606F",
        "toggle_bg":    "#BACED9",
        "toggle_bdr":   "#A0BAC8",
    },
    DARK: {
        "bg":           "#121212",
        "card_bg":      "#1E1E1E",
        "card_border":  "#2D2D2D",
        "text":         "#F0F0F0",
        "text_sec":     "#9E9E9E",
        "text_muted":   "#707070",
        "field_bg":     "#262626",
        "field_border": "#383838",
        "field_focus":  "#7FA6B8",
        "accent":       "#7FA6B8",
        "accent_hover": "#92B7C8",
        "accent_press": "#6A93A6",
        "danger":       "#F87171",
        "danger_hover": "rgba(248, 113, 113, 0.14)",
        "chip_bg":      "#282828",
        "chip_border":  "#383838",
        "chip_hover":   "#333333",
        "scroll_bg":    "#121212",
        "scroll_handle":"#2D2D2D",
        "scroll_hover": "#444444",
        "slider_track": "#303030",
        "slider_fill":  "#7FA6B8",
        "slider_knob":  "#E0E0E0",
        "check_border": "#383838",
        "check_active": "#7FA6B8",
        "preview_bg":   "#0E0E0E",
        "preview_bdr":  "#2D2D2D",
        "success_bg":   "#064E3B",
        "success_fg":   "#6EE7B7",
        "fail_bg":      "#7F1D1D",
        "fail_fg":      "#FCA5A5",
        "info_bg":      "#262626",
        "info_fg":      "#7FA6B8",
        "disabled_fg":  "#555555",
        "disabled_bg":  "#1A1A1A",
        "dropdown_arr": "#9E9E9E",
        "toggle_bg":    "#282828",
        "toggle_bdr":   "#383838",
    },
}


def build_stylesheet(t: dict) -> str:
    return f"""
QMainWindow {{
    background-color: {t["bg"]};
}}

QWidget#CentralWidget {{
    background-color: {t["bg"]};
}}

/* ── Scrollbars ── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QScrollBar:vertical {{
    border: none; background: {t["scroll_bg"]}; width: 7px; border-radius: 3px; margin: 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {t["scroll_handle"]}; border-radius: 3px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {t["scroll_hover"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    border: none; background: {t["scroll_bg"]}; height: 7px; border-radius: 3px; margin: 0 2px;
}}
QScrollBar::handle:horizontal {{
    background: {t["scroll_handle"]}; border-radius: 3px; min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {t["scroll_hover"]}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

/* ── Cards ── */
QFrame[class="Card"] {{
    background-color: {t["card_bg"]};
    border: 1px solid {t["card_border"]};
    border-radius: 12px;
}}

/* ── Labels ── */
QLabel {{
    color: {t["text"]};
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI Variable", "Segoe UI", sans-serif;
}}
QLabel[class="CardTitle"] {{
    font-size: 13px; font-weight: 700; color: {t["text"]}; letter-spacing: -0.1px;
}}
QLabel[class="FieldLabel"] {{
    font-size: 11px; font-weight: 600; color: {t["text_sec"]};
}}
QLabel[class="HelpText"] {{
    font-size: 11px; color: {t["text_muted"]};
}}

/* ── Inputs ── */
QLineEdit {{
    background-color: {t["field_bg"]};
    color: {t["text"]};
    border: 1px solid {t["field_border"]};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI Variable", "Segoe UI", sans-serif;
    selection-background-color: {t["accent"]};
    selection-color: #FFFFFF;
}}
QLineEdit:hover {{ border-color: {t["scroll_hover"]}; }}
QLineEdit:focus {{ border-color: {t["field_focus"]}; }}
QLineEdit:disabled {{
    background-color: {t["disabled_bg"]}; color: {t["disabled_fg"]}; border-color: {t["card_border"]};
}}

/* ── Combos ── */
QComboBox {{
    background-color: {t["field_bg"]};
    color: {t["text"]};
    border: 1px solid {t["field_border"]};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI Variable", "Segoe UI", sans-serif;
    min-height: 20px;
}}
QComboBox:hover {{ border-color: {t["scroll_hover"]}; }}
QComboBox:focus {{ border-color: {t["field_focus"]}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right; width: 26px; border-left: none;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {t["dropdown_arr"]}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {t["card_bg"]};
    color: {t["text"]};
    border: 1px solid {t["card_border"]};
    border-radius: 8px;
    selection-background-color: {t["accent"]};
    selection-color: #FFFFFF;
    padding: 4px;
}}

/* ── Checkboxes ── */
QCheckBox {{
    font-size: 12px; color: {t["text"]}; font-weight: 500; spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid {t["check_border"]}; background-color: {t["field_bg"]};
}}
QCheckBox::indicator:hover {{ border-color: {t["check_active"]}; }}
QCheckBox::indicator:checked {{
    background-color: {t["check_active"]}; border-color: {t["check_active"]};
}}

/* ── Sliders ── */
QSlider::groove:horizontal {{
    border: none; height: 4px; background: {t["slider_track"]}; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {t["slider_fill"]}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t["slider_knob"]};
    border: 1.5px solid {t["slider_fill"]};
    width: 16px; margin-top: -6px; margin-bottom: -6px; border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: {t["slider_fill"]}; }}

/* ── Buttons ── */
QPushButton {{
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 12px; font-weight: 500; border-radius: 8px; padding: 7px 14px;
}}

QPushButton[class="SecondaryButton"] {{
    background-color: {t["card_bg"]}; color: {t["text"]}; border: 1px solid {t["card_border"]};
}}
QPushButton[class="SecondaryButton"]:hover {{
    background-color: {t["chip_hover"]}; border-color: {t["scroll_hover"]};
}}
QPushButton[class="SecondaryButton"]:pressed {{
    background-color: {t["slider_track"]};
}}

QPushButton[class="PresetChip"] {{
    background-color: {t["chip_bg"]}; color: {t["text_sec"]}; border: 1px solid {t["chip_border"]};
    border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600;
}}
QPushButton[class="PresetChip"]:hover {{
    background-color: {t["chip_hover"]}; border-color: {t["scroll_hover"]}; color: {t["text"]};
}}

QPushButton[class="PrimaryButton"] {{
    background-color: {t["accent"]}; color: #FFFFFF; border: none;
    font-size: 13px; font-weight: 600; padding: 11px 22px; border-radius: 8px;
}}
QPushButton[class="PrimaryButton"]:hover {{ background-color: {t["accent_hover"]}; }}
QPushButton[class="PrimaryButton"]:pressed {{ background-color: {t["accent_press"]}; }}
QPushButton[class="PrimaryButton"]:disabled {{
    background-color: {t["disabled_fg"]}; color: {t["disabled_bg"]};
}}

QPushButton[class="DangerButton"] {{
    background-color: transparent; color: {t["danger"]}; border: 1px solid {t["danger"]}; border-radius: 8px;
}}
QPushButton[class="DangerButton"]:hover {{ background-color: {t["danger_hover"]}; }}
QPushButton[class="DangerButton"]:disabled {{
    color: {t["disabled_fg"]}; border-color: {t["disabled_fg"]};
}}

/* ── Progress ── */
QProgressBar {{
    background-color: {t["slider_track"]}; border: none; border-radius: 4px; height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {t["accent"]}; border-radius: 4px;
}}
"""
# ──────────────────────────────────────────────────────────────────────
# Theme Toggle Switch Widget
# ──────────────────────────────────────────────────────────────────────
class ThemeSwitch(QWidget):
    """A custom animated-looking toggle switch for dark/light mode."""
    toggled = Signal(bool)  # True = dark mode

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._is_dark = False
        self.setFixedSize(72, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def set_dark(self, dark: bool) -> None:
        self._is_dark = dark
        self.update()

    def mousePressEvent(self, event) -> None:
        self._is_dark = not self._is_dark
        self.update()
        self.toggled.emit(self._is_dark)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2

        # Track
        if self._is_dark:
            track_color = QColor("#223542")
        else:
            track_color = QColor("#D6E6EF")
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Knob
        knob_margin = 3
        knob_d = h - knob_margin * 2
        knob_x = (w - knob_d - knob_margin) if self._is_dark else knob_margin
        knob_y = knob_margin

        p.setBrush(QBrush(QColor("#0E171E") if self._is_dark else QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(knob_x), int(knob_y), int(knob_d), int(knob_d))

        # Icon — sun or moon
        icon_font = QFont("Segoe UI Emoji", 14)
        p.setFont(icon_font)
        if self._is_dark:
            p.setPen(QPen(QColor("#FBBF24")))
            p.drawText(int(knob_margin + 4), 0, int(knob_d), h, Qt.AlignmentFlag.AlignCenter, "☀")
        else:
            p.setPen(QPen(QColor("#7FA6B8")))
            p.drawText(int(w - knob_d - knob_margin - 4), 0, int(knob_d), h, Qt.AlignmentFlag.AlignCenter, "🌙")
        p.end()


# ──────────────────────────────────────────────────────────────────────
# Interactive Color Swatch Button
# ──────────────────────────────────────────────────────────────────────
class ColorSwatchButton(QPushButton):
    colorChanged = Signal(QColor)

    def __init__(self, initial_color: str | QColor = "#FFFFFF", title: str = "Select Color", parent=None):
        super().__init__(parent)
        self._color = QColor(initial_color)
        self._title = title
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        self.setMinimumWidth(88)
        self.update_style()
        self.clicked.connect(self._on_click)

    def color(self) -> QColor:
        return self._color

    def rgb_tuple(self) -> tuple[int, int, int]:
        return (self._color.red(), self._color.green(), self._color.blue())

    def set_color(self, new_color: str | QColor) -> None:
        c = QColor(new_color)
        if c.isValid() and c != self._color:
            self._color = c
            self.update_style()
            self.colorChanged.emit(self._color)

    def update_style(self) -> None:
        hex_code = self._color.name().upper()
        lum = self._color.red() * 0.299 + self._color.green() * 0.587 + self._color.blue() * 0.114
        fg = "#FFFFFF" if lum < 140 else "#111111"
        border = "#7FA6B8" if hex_code in ("#FFFFFF", "#F8FAFC", "#F7FBFD", "#F1F5F9", "#F3F4F6") else hex_code
        self.setText(f"  {hex_code}  ")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_code};
                color: {fg};
                border: 2px solid {border};
                border-radius: 8px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                border-color: #7FA6B8;
            }}
        """)

    def _on_click(self) -> None:
        dialog = QColorDialog(self._color, self.window())
        dialog.setWindowTitle(self._title)
        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            selected = dialog.selectedColor()
            if selected.isValid():
                self.set_color(selected)

# ──────────────────────────────────────────────────────────────────────
# Interactive 3D Orbit Preview Label
# ──────────────────────────────────────────────────────────────────────
class InteractivePreviewLabel(QLabel):
    orbitDelta = Signal(float, float)  # dyaw, dpitch

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._is_dragging = False
        self._drag_start = None
        self._is_3d = False

    def set_3d_mode(self, is_3d: bool) -> None:
        self._is_3d = is_3d
        if is_3d:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if self._is_3d and event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_start is not None:
            dx = event.pos().x() - self._drag_start.x()
            dy = event.pos().y() - self._drag_start.y()
            self._drag_start = event.pos()
            self.orbitDelta.emit(float(dx * 0.7), float(-dy * 0.7))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            if self._is_3d:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

# ──────────────────────────────────────────────────────────────────────
# Async Preview Worker (Single-Flight Non-Blocking Background Engine)
# ──────────────────────────────────────────────────────────────────────
class PreviewTaskSignals(QObject):
    ready = Signal(int, QPixmap, str, int, int)
    error = Signal(int, str)


class AsyncPreviewWorker(QRunnable):
    def __init__(self, task_id: int, source_path: Path, config: PreviewConfig):
        super().__init__()
        self.task_id = task_id
        self.source_path = source_path
        self.config = config
        self.signals = PreviewTaskSignals()

    def run(self):
        try:
            jpeg_bytes = preview_jpeg_bytes(self.source_path, self.config, max_dimension=850)
            pix = QPixmap()
            if pix.loadFromData(jpeg_bytes, "JPG"):
                self.signals.ready.emit(
                    self.task_id,
                    pix,
                    self.source_path.name,
                    pix.width(),
                    pix.height(),
                )
            else:
                self.signals.error.emit(self.task_id, "Could not decode preview image")
        except Exception as exc:
            self.signals.error.emit(self.task_id, str(exc))


# ──────────────────────────────────────────────────────────────────────
# Background Batch Worker
# ──────────────────────────────────────────────────────────────────────
class WorkerSignals(QObject):
    progress = Signal(int, int, str)
    finished = Signal(int, int, list, bool)
    failed = Signal(str)

class BatchWorker(QRunnable):
    def __init__(self, input_folder: Path, output_folder: Path, config: PreviewConfig) -> None:
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.config = config
        self.signals = WorkerSignals()
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            success, failed, errors = process_folder(
                self.input_folder,
                self.output_folder,
                self.config,
                lambda current, total, status: self.signals.progress.emit(current, total, status),
                self.cancel_event.is_set,
            )
            self.signals.finished.emit(success, failed, errors, self.cancel_event.is_set())
        except Exception as exc:
            self.signals.failed.emit(str(exc))


# ──────────────────────────────────────────────────────────────────────
# Main Application Window
# ──────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PreviewGen")
        self.resize(1280, 860)
        self.setMinimumSize(1000, 700)

        self.settings = QSettings("MustaqeemTools", "PreviewGen")
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(2)
        self.worker: BatchWorker | None = None
        self.preview_source: Path | None = None
        self.file_list: list[Path] = []
        self.current_file_idx: int = 0
        self.logo_path: str = ""
        self.custom_font_path: str = ""
        self.app_icon: QIcon | None = None
        self.app_icon_path: str = ""
        self.tray_icon: QSystemTrayIcon | None = None
        self._session_zip_dir: Path | None = None
        self._raw_pixmap: QPixmap | None = None
        self._fit_to_view = True
        self._current_theme = LIGHT
        self.preview_thread_pool = QThreadPool()
        self.preview_thread_pool.setMaxThreadCount(1)
        self._current_preview_task_id = 0

        # Responsive debounce timer (40ms for instantaneous 60fps interaction)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(40)
        self._preview_timer.timeout.connect(self._do_refresh_preview)

        self._build_ui()
        self._load_app_icon()
        self._setup_system_tray()
        self._ensure_desktop_shortcut()
        self._load_saved_settings()
    # ──────────────────────────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(16)

        # ─── Header ───
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._app_title = QLabel("PreviewGen")
        self._app_title.setStyleSheet("font-size: 24px; font-weight: 800;")
        self._app_sub = QLabel("Create marketplace-ready JPG previews with customizable diagonal backgrounds & text")
        self._app_sub.setStyleSheet("font-size: 13px;")
        title_col.addWidget(self._app_title)
        title_col.addWidget(self._app_sub)
        header.addLayout(title_col)
        header.addStretch()

        # Theme toggle
        self.theme_switch = ThemeSwitch()
        self.theme_switch.toggled.connect(self._on_theme_toggled)
        header.addWidget(self.theme_switch)

        root.addLayout(header)

        # ─── Two-Column Split ───
        columns = QHBoxLayout()
        columns.setSpacing(18)

        # LEFT: scrollable controls
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(465)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left_content = QWidget()
        left = QVBoxLayout(left_content)
        left.setContentsMargins(0, 0, 12, 0)
        left.setSpacing(16)

        # CARD 1 — Folders
        left.addWidget(self._build_folders_card())
        # CARD 2 — Background
        left.addWidget(self._build_background_card())
        # CARD 3 — Text
        left.addWidget(self._build_text_card())
        # CARD 4 — Actions
        left.addWidget(self._build_actions_card())
        left.addStretch()

        left_scroll.setWidget(left_content)
        columns.addWidget(left_scroll)

        # RIGHT: preview
        columns.addWidget(self._build_preview_card(), 1)

        root.addLayout(columns, 1)

    # ── Card builders ──

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setProperty("class", "Card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)
        return frame, lay

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "CardTitle")
        return lbl

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "FieldLabel")
        return lbl

    def _build_folders_card(self) -> QFrame:
        card, lay = self._card()
        lay.addWidget(self._section_title("1 ·  Folders"))

        lay.addWidget(self._field_label("Input Folder or ZIP (PNG, WebP, SVG, TIFF, PSD, 3D, ZIP)"))
        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Folder containing 2D assets, 3D models, or ZIP archives")
        self.input_browse_btn = QPushButton("Browse…")
        self.input_browse_btn.setProperty("class", "SecondaryButton")
        self.input_browse_btn.clicked.connect(self.choose_input)
        in_row.addWidget(self.input_edit, 1)
        in_row.addWidget(self.input_browse_btn)
        lay.addLayout(in_row)

        self.same_folder_chk = QCheckBox("Save preview JPGs in the same folder as input files")
        self.same_folder_chk.toggled.connect(self.on_same_folder_toggled)
        lay.addWidget(self.same_folder_chk)

        self.out_lbl = self._field_label("Output JPG Folder")
        lay.addWidget(self.out_lbl)
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Destination folder for previews")
        self.output_browse_btn = QPushButton("Browse…")
        self.output_browse_btn.setProperty("class", "SecondaryButton")
        self.output_browse_btn.clicked.connect(self.choose_output)
        self.output_open_btn = QPushButton("Open")
        self.output_open_btn.setProperty("class", "SecondaryButton")
        self.output_open_btn.setToolTip("Open output folder in file manager")
        self.output_open_btn.clicked.connect(self.open_output_folder)
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(self.output_browse_btn)
        out_row.addWidget(self.output_open_btn)
        lay.addLayout(out_row)
        return card

    def _build_background_card(self) -> QFrame:
        card, lay = self._card()
        lay.addWidget(self._section_title("2 ·  Background Triangle & Colors"))

        lay.addWidget(self._field_label("Diagonal Split Direction"))
        self.triangle_combo = QComboBox()
        self.triangle_combo.addItem("Left Solid / Right Transparent (Recommended)", True)
        self.triangle_combo.addItem("Left Transparent / Right Solid", False)
        self.triangle_combo.currentIndexChanged.connect(self.schedule_preview)
        lay.addWidget(self.triangle_combo)

        lay.addWidget(self._field_label("Solid Background Color"))
        solid_row = QHBoxLayout()
        solid_row.setSpacing(6)
        self.solid_color_btn = ColorSwatchButton("#FFFFFF", "Choose Solid Background Color")
        self.solid_color_btn.colorChanged.connect(self.schedule_preview)
        solid_row.addWidget(self.solid_color_btn)
        for name, color in [("White", "#FFFFFF"), ("Off-White", "#F8FAFC"), ("Light Gray", "#E2E8F0"), ("Dark", "#1E293B")]:
            btn = QPushButton(name)
            btn.setProperty("class", "PresetChip")
            btn.clicked.connect(lambda _, c=color: self.solid_color_btn.set_color(c))
            solid_row.addWidget(btn)
        solid_row.addStretch()
        lay.addLayout(solid_row)
        return card

    def _build_text_card(self) -> QFrame:
        card, lay = self._card()
        lay.addWidget(self._section_title("3 ·  Branding & Watermark (Logo + Text)"))

        # ── Logo / Icon Upload Section ──
        lay.addWidget(self._field_label("Brand Logo / Icon (Optional)"))
        logo_btn_row = QHBoxLayout()
        logo_btn_row.setSpacing(8)
        self.upload_logo_btn = QPushButton("Upload Logo / Icon…")
        self.upload_logo_btn.setProperty("class", "SecondaryButton")
        self.upload_logo_btn.clicked.connect(self.choose_logo)
        self.clear_logo_btn = QPushButton("Clear")
        self.clear_logo_btn.setProperty("class", "DangerButton")
        self.clear_logo_btn.setEnabled(False)
        self.clear_logo_btn.clicked.connect(self.clear_logo)
        logo_btn_row.addWidget(self.upload_logo_btn, 1)
        logo_btn_row.addWidget(self.clear_logo_btn)
        lay.addLayout(logo_btn_row)

        self.logo_info_lbl = QLabel("No logo uploaded")
        self.logo_info_lbl.setStyleSheet("font-size: 11px; color: #6B7280;")
        lay.addWidget(self.logo_info_lbl)

        # Logo controls widget
        self.logo_options_widget = QWidget()
        lol = QVBoxLayout(self.logo_options_widget)
        lol.setContentsMargins(0, 0, 0, 0)
        lol.setSpacing(8)

        l_scale_hdr = QHBoxLayout()
        l_scale_hdr.addWidget(self._field_label("Logo Scale"))
        l_scale_hdr.addStretch()
        self.logo_scale_lbl = QLabel("100%")
        self.logo_scale_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        l_scale_hdr.addWidget(self.logo_scale_lbl)
        lol.addLayout(l_scale_hdr)

        self.logo_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_scale_slider.setRange(20, 250)
        self.logo_scale_slider.setValue(100)
        self.logo_scale_slider.valueChanged.connect(self.on_logo_scale_changed)
        lol.addWidget(self.logo_scale_slider)

        l_op_hdr = QHBoxLayout()
        l_op_hdr.addWidget(self._field_label("Logo Opacity"))
        l_op_hdr.addStretch()
        self.logo_op_lbl = QLabel("90%")
        self.logo_op_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        l_op_hdr.addWidget(self.logo_op_lbl)
        lol.addLayout(l_op_hdr)

        self.logo_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_opacity_slider.setRange(10, 100)
        self.logo_opacity_slider.setValue(90)
        self.logo_opacity_slider.valueChanged.connect(self.on_logo_opacity_changed)
        lol.addWidget(self.logo_opacity_slider)

        lol.addWidget(self._field_label("Logo Position Preset"))
        self.logo_pos_combo = QComboBox()
        self.logo_pos_combo.addItem("Top-Right (Default)", (0.88, 0.05))
        self.logo_pos_combo.addItem("Top-Left", (0.05, 0.05))
        self.logo_pos_combo.addItem("Center", (0.50, 0.50))
        self.logo_pos_combo.addItem("Bottom-Right", (0.88, 0.90))
        self.logo_pos_combo.addItem("Bottom-Left", (0.05, 0.90))
        self.logo_pos_combo.addItem("Custom Coordinates", "custom")
        self.logo_pos_combo.currentIndexChanged.connect(self.on_logo_pos_combo_changed)
        lol.addWidget(self.logo_pos_combo)

        l_xy_row = QHBoxLayout()
        l_xy_row.setSpacing(6)
        l_xy_row.addWidget(self._field_label("Logo X:"))
        self.logo_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_x_slider.setRange(0, 100)
        self.logo_x_slider.setValue(88)
        self.logo_x_slider.valueChanged.connect(self.on_logo_coords_changed)
        self.logo_x_lbl = QLabel("88%")
        self.logo_x_lbl.setFixedWidth(30)
        self.logo_x_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        l_xy_row.addWidget(self.logo_x_slider, 1)
        l_xy_row.addWidget(self.logo_x_lbl)

        l_xy_row.addWidget(self._field_label("Logo Y:"))
        self.logo_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_y_slider.setRange(0, 100)
        self.logo_y_slider.setValue(5)
        self.logo_y_slider.valueChanged.connect(self.on_logo_coords_changed)
        self.logo_y_lbl = QLabel("5%")
        self.logo_y_lbl.setFixedWidth(30)
        self.logo_y_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        l_xy_row.addWidget(self.logo_y_slider, 1)
        l_xy_row.addWidget(self.logo_y_lbl)
        lol.addLayout(l_xy_row)

        self.logo_options_widget.setVisible(False)
        lay.addWidget(self.logo_options_widget)

        # ── Text Watermark Section ──
        lay.addWidget(self._field_label("Watermark Text (leave empty for none)"))
        self.text_edit = QLineEdit(DEFAULT_TEXT)
        self.text_edit.setPlaceholderText("e.g. 100% TRANSPARENT (or blank for none)")
        self.text_edit.textChanged.connect(self.schedule_preview)
        lay.addWidget(self.text_edit)

        lay.addWidget(self._field_label("Text Position Preset"))
        self.position_combo = QComboBox()
        self.position_combo.addItem("Top-Left Corner (Recommended)", (0.05, 0.05))
        self.position_combo.addItem("Top-Right Corner", (0.95, 0.05))
        self.position_combo.addItem("Center of Image", (0.50, 0.50))
        self.position_combo.addItem("Bottom-Left Corner", (0.05, 0.95))
        self.position_combo.addItem("Bottom-Right Corner", (0.95, 0.95))
        self.position_combo.addItem("Custom Coordinates", "custom")
        self.position_combo.currentIndexChanged.connect(self.on_text_pos_combo_changed)
        lay.addWidget(self.position_combo)

        t_xy_row = QHBoxLayout()
        t_xy_row.setSpacing(6)
        t_xy_row.addWidget(self._field_label("Text X:"))
        self.text_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_x_slider.setRange(0, 100)
        self.text_x_slider.setValue(5)
        self.text_x_slider.valueChanged.connect(self.on_text_coords_changed)
        self.text_x_lbl = QLabel("5%")
        self.text_x_lbl.setFixedWidth(30)
        self.text_x_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        t_xy_row.addWidget(self.text_x_slider, 1)
        t_xy_row.addWidget(self.text_x_lbl)

        t_xy_row.addWidget(self._field_label("Text Y:"))
        self.text_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_y_slider.setRange(0, 100)
        self.text_y_slider.setValue(5)
        self.text_y_slider.valueChanged.connect(self.on_text_coords_changed)
        self.text_y_lbl = QLabel("5%")
        self.text_y_lbl.setFixedWidth(30)
        self.text_y_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        t_xy_row.addWidget(self.text_y_slider, 1)
        t_xy_row.addWidget(self.text_y_lbl)
        lay.addLayout(t_xy_row)
        lay.addWidget(self._field_label("Text Fill Color"))
        t_color_row = QHBoxLayout()
        t_color_row.setSpacing(6)
        self.text_color_btn = ColorSwatchButton("#FFFFFF", "Choose Text Color")
        self.text_color_btn.colorChanged.connect(self.schedule_preview)
        t_color_row.addWidget(self.text_color_btn)
        for name, color in [("White", "#FFFFFF"), ("Black", "#0F172A"), ("Yellow", "#FACC15")]:
            btn = QPushButton(name)
            btn.setProperty("class", "PresetChip")
            btn.clicked.connect(lambda _, c=color: self.text_color_btn.set_color(c))
            t_color_row.addWidget(btn)
        t_color_row.addStretch()
        lay.addLayout(t_color_row)
        # Custom Font Selection
        lay.addWidget(self._field_label("Typography & Custom Font (.ttf, .otf, .woff)"))
        font_btn_row = QHBoxLayout()
        font_btn_row.setSpacing(6)
        self.choose_font_btn = QPushButton("Browse Font File…")
        self.choose_font_btn.setProperty("class", "SecondaryButton")
        self.choose_font_btn.clicked.connect(self.choose_font)
        self.reset_font_btn = QPushButton("Reset")
        self.reset_font_btn.setProperty("class", "DangerButton")
        self.reset_font_btn.setEnabled(False)
        self.reset_font_btn.clicked.connect(self.reset_font)
        font_btn_row.addWidget(self.choose_font_btn, 1)
        font_btn_row.addWidget(self.reset_font_btn)
        lay.addLayout(font_btn_row)

        self.font_info_lbl = QLabel("Font: System Default Bold")
        self.font_info_lbl.setStyleSheet("font-size: 11px; color: #4D6775;")
        lay.addWidget(self.font_info_lbl)
        # Font scale
        scale_hdr = QHBoxLayout()
        scale_hdr.addWidget(self._field_label("Font Size Scale"))
        scale_hdr.addStretch()
        self.scale_val_lbl = QLabel("100%")
        self.scale_val_lbl.setStyleSheet("font-size: 12px; font-weight: 700;")
        scale_hdr.addWidget(self.scale_val_lbl)
        lay.addLayout(scale_hdr)

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(50, 180)
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        lay.addWidget(self.scale_slider)

        # Outline
        self.outline_chk = QCheckBox("Add Outline / Stroke to Text")
        self.outline_chk.setChecked(True)
        self.outline_chk.toggled.connect(self.on_outline_toggled)
        lay.addWidget(self.outline_chk)

        self.outline_options_widget = QWidget()
        ol = QVBoxLayout(self.outline_options_widget)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(10)

        ol.addWidget(self._field_label("Outline Color"))
        o_row = QHBoxLayout()
        o_row.setSpacing(6)
        self.outline_color_btn = ColorSwatchButton("#000000", "Choose Outline Color")
        self.outline_color_btn.colorChanged.connect(self.schedule_preview)
        o_row.addWidget(self.outline_color_btn)
        for name, color in [("Black", "#000000"), ("White", "#FFFFFF"), ("Dark Gray", "#334155")]:
            btn = QPushButton(name)
            btn.setProperty("class", "PresetChip")
            btn.clicked.connect(lambda _, c=color: self.outline_color_btn.set_color(c))
            o_row.addWidget(btn)
        o_row.addStretch()
        ol.addLayout(o_row)

        thick_hdr = QHBoxLayout()
        thick_hdr.addWidget(self._field_label("Outline Thickness"))
        thick_hdr.addStretch()
        self.thick_val_lbl = QLabel("Normal")
        self.thick_val_lbl.setStyleSheet("font-size: 12px; font-weight: 700;")
        thick_hdr.addWidget(self.thick_val_lbl)
        ol.addLayout(thick_hdr)
        self.thick_slider = QSlider(Qt.Orientation.Horizontal)
        self.thick_slider.setRange(1, 5)
        self.thick_slider.setValue(2)
        self.thick_slider.valueChanged.connect(self.on_thickness_changed)
        ol.addWidget(self.thick_slider)
        lay.addWidget(self.outline_options_widget)

        # Opacity
        op_hdr = QHBoxLayout()
        op_hdr.addWidget(self._field_label("Text Opacity"))
        op_hdr.addStretch()
        self.op_val_lbl = QLabel("90%")
        self.op_val_lbl.setStyleSheet("font-size: 12px; font-weight: 700;")
        op_hdr.addWidget(self.op_val_lbl)
        lay.addLayout(op_hdr)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        lay.addWidget(self.opacity_slider)
        return card

    def _build_actions_card(self) -> QFrame:
        card, lay = self._card()
        lay.addWidget(self._section_title("4 ·  Process Previews"))

        self.generate_btn = QPushButton("Generate All JPG Previews")
        self.generate_btn.setProperty("class", "PrimaryButton")
        self.generate_btn.clicked.connect(self.start_processing)
        lay.addWidget(self.generate_btn)

        self.cancel_btn = QPushButton("Cancel Processing")
        self.cancel_btn.setProperty("class", "DangerButton")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        lay.addWidget(self.cancel_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        lay.addWidget(self.progress_bar)

        self.stats_widget = QWidget()
        sl = QHBoxLayout(self.stats_widget)
        sl.setContentsMargins(0, 4, 0, 4)
        sl.setSpacing(8)
        self.chip_success = QLabel("0 Success")
        self.chip_failed = QLabel("0 Failed")
        self.chip_pending = QLabel("0 Total")
        sl.addWidget(self.chip_success)
        sl.addWidget(self.chip_failed)
        sl.addWidget(self.chip_pending)
        sl.addStretch()
        self.stats_widget.setVisible(False)
        lay.addWidget(self.stats_widget)

        self.status_lbl = QLabel("Ready to process")
        self.status_lbl.setStyleSheet("font-size: 12px;")
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)
        return card

    def _build_preview_card(self) -> QFrame:
        card, lay = self._card()
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self._section_title("Live Preview"))

        # File navigation controls (Previous / Counter / Next)
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setProperty("class", "SecondaryButton")
        self.prev_btn.setEnabled(False)
        self.prev_btn.setToolTip("View previous image in folder (Left Arrow)")
        self.prev_btn.clicked.connect(self.go_prev_file)

        self.file_counter_lbl = QLabel("0 / 0")
        self.file_counter_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; padding: 4px 10px; "
            "background: rgba(99, 102, 241, 0.12); color: #818CF8; border-radius: 6px;"
        )

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setProperty("class", "SecondaryButton")
        self.next_btn.setEnabled(False)
        self.next_btn.setToolTip("View next image in folder (Right Arrow)")
        self.next_btn.clicked.connect(self.go_next_file)

        toolbar.addWidget(self.prev_btn)
        toolbar.addWidget(self.file_counter_lbl)
        toolbar.addWidget(self.next_btn)
        toolbar.addStretch()

        self.fit_view_btn = QPushButton("Fit to View")
        self.fit_view_btn.setProperty("class", "SecondaryButton")
        self.fit_view_btn.setCheckable(True)
        self.fit_view_btn.setChecked(True)
        self.fit_view_btn.clicked.connect(self.toggle_view_mode)
        toolbar.addWidget(self.fit_view_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setProperty("class", "SecondaryButton")
        self.refresh_btn.clicked.connect(self.schedule_preview)
        toolbar.addWidget(self.refresh_btn)
        lay.addLayout(toolbar)

        # ─── 3D Orbit Control Bar (Visible for 3D assets) ───
        self.panel_3d = QFrame()
        self.panel_3d.setStyleSheet("background: transparent; border: none;")
        p3d_lay = QVBoxLayout(self.panel_3d)
        p3d_lay.setContentsMargins(0, 0, 0, 4)
        p3d_lay.setSpacing(6)

        h3d_row = QHBoxLayout()
        h3d_row.setSpacing(6)
        self.orbit_hint = QLabel("🎮 3D 360° View: Drag preview or use angle presets:")
        self.orbit_hint.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        h3d_row.addWidget(self.orbit_hint)
        h3d_row.addStretch()

        for name, (yaw, pitch) in [
            ("Isometric 3/4", (45, 30)),
            ("Front", (0, 0)),
            ("Side", (90, 0)),
            ("Top", (0, 85)),
            ("Back", (180, 0)),
        ]:
            btn = QPushButton(name)
            btn.setProperty("class", "PresetChip")
            btn.clicked.connect(lambda _, y=yaw, p=pitch: self.set_3d_angle(y, p))
            h3d_row.addWidget(btn)
        p3d_lay.addLayout(h3d_row)

        s3d_row = QHBoxLayout()
        s3d_row.setSpacing(10)
        s3d_row.addWidget(self._field_label("Yaw (0-360°):"))
        self.yaw_slider = QSlider(Qt.Orientation.Horizontal)
        self.yaw_slider.setRange(0, 360)
        self.yaw_slider.setValue(45)
        self.yaw_slider.valueChanged.connect(self.on_yaw_changed)
        self.yaw_val_lbl = QLabel("45°")
        self.yaw_val_lbl.setFixedWidth(36)
        self.yaw_val_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        s3d_row.addWidget(self.yaw_slider, 1)
        s3d_row.addWidget(self.yaw_val_lbl)

        s3d_row.addWidget(self._field_label("Pitch:"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-85, 85)
        self.pitch_slider.setValue(30)
        self.pitch_slider.valueChanged.connect(self.on_pitch_changed)
        self.pitch_val_lbl = QLabel("30°")
        self.pitch_val_lbl.setFixedWidth(36)
        self.pitch_val_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #818CF8;")
        s3d_row.addWidget(self.pitch_slider, 1)
        s3d_row.addWidget(self.pitch_val_lbl)
        p3d_lay.addLayout(s3d_row)

        self.panel_3d.setVisible(False)
        lay.addWidget(self.panel_3d)

        # Scrollable image canvas with interactive drag orbit
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = InteractivePreviewLabel("Select an input folder to view preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.orbitDelta.connect(self.on_orbit_drag)
        self.preview_scroll.setWidget(self.preview_label)
        lay.addWidget(self.preview_scroll, 1)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        self.file_info_lbl = QLabel("No file loaded")
        self.file_info_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
        self.res_info_lbl = QLabel("")
        self.res_info_lbl.setStyleSheet("font-size: 12px;")
        info_row.addWidget(self.file_info_lbl)
        info_row.addStretch()
        info_row.addWidget(self.res_info_lbl)
        lay.addLayout(info_row)
        return card

    # ──────────────────────────────────────────────────────────────────
    # Theme Management
    # ──────────────────────────────────────────────────────────────────
    def _apply_theme(self, theme: str) -> None:
        t = THEME[theme]
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(t))

        self.theme_switch.set_dark(theme == DARK)

        self.preview_scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {t['preview_bg']}; "
            f"border: 1px solid {t['preview_bdr']}; border-radius: 10px; }}"
        )
        self.preview_label.setStyleSheet(
            f"color: {t['text_muted']}; font-size: 14px; background: transparent;"
        )

        # Status chips
        self.chip_success.setStyleSheet(
            f"background: {t['success_bg']}; color: {t['success_fg']}; "
            "padding: 4px 12px; border-radius: 8px; font-weight: 700; font-size: 11px;"
        )
        self.chip_failed.setStyleSheet(
            f"background: {t['fail_bg']}; color: {t['fail_fg']}; "
            "padding: 4px 12px; border-radius: 8px; font-weight: 700; font-size: 11px;"
        )
        self.chip_pending.setStyleSheet(
            f"background: {t['info_bg']}; color: {t['info_fg']}; "
            "padding: 4px 12px; border-radius: 8px; font-weight: 700; font-size: 11px;"
        )

        # Accent-coloured value labels
        for lbl in (self.scale_val_lbl, self.thick_val_lbl, self.op_val_lbl, self.yaw_val_lbl, self.pitch_val_lbl):
            lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['accent']};")

        self.orbit_hint.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['accent']};")
        self.file_counter_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 700; padding: 4px 10px; "
            f"background: {t['chip_bg']}; color: {t['accent']}; border: 1px solid {t['chip_border']}; border-radius: 6px;"
        )

        self.status_lbl.setStyleSheet(f"font-size: 12px; color: {t['text_muted']};")
        self.file_info_lbl.setStyleSheet(f"font-size: 12px; color: {t['text_sec']}; font-weight: 600;")
        self.res_info_lbl.setStyleSheet(f"font-size: 12px; color: {t['text_muted']};")

    def _on_theme_toggled(self, is_dark: bool) -> None:
        self._current_theme = DARK if is_dark else LIGHT
        self._apply_theme(self._current_theme)
        self._save_settings()

    def toggle_theme(self) -> None:
        is_dark = (self._current_theme == LIGHT)
        self._on_theme_toggled(is_dark)
    # ──────────────────────────────────────────────────────────────────
    # Settings & State Persistence
    # ──────────────────────────────────────────────────────────────────
    def _load_saved_settings(self) -> None:
        last_input = str(self.settings.value("input", ""))
        last_output = str(self.settings.value("output", ""))
        saved_text = str(self.settings.value("text", DEFAULT_TEXT))
        saved_pos = str(self.settings.value("position", "top-left"))
        saved_op = int(self.settings.value("opacity", 90))
        same_folder = bool(self.settings.value("same_folder", False))
        invert_bg = bool(self.settings.value("invert_triangles", True))
        solid_col = str(self.settings.value("solid_color", "#FFFFFF"))
        text_col = str(self.settings.value("text_color", "#FFFFFF"))
        has_out = bool(self.settings.value("has_outline", True))
        out_col = str(self.settings.value("outline_color", "#000000"))
        out_thick = int(self.settings.value("outline_thickness", 2))
        f_scale = int(self.settings.value("font_scale", 100))
        saved_theme = str(self.settings.value("theme", LIGHT))

        self._current_theme = saved_theme
        self._apply_theme(saved_theme)

        if last_input:
            self.input_edit.setText(last_input)
        if last_output:
            self.output_edit.setText(last_output)

        self.text_edit.setText(saved_text)

        idx = self.position_combo.findData(saved_pos)
        if idx >= 0:
            self.position_combo.setCurrentIndex(idx)

        self.opacity_slider.setValue(max(10, min(100, saved_op)))
        self.op_val_lbl.setText(f"{self.opacity_slider.value()}%")

        tri_idx = self.triangle_combo.findData(invert_bg)
        if tri_idx >= 0:
            self.triangle_combo.setCurrentIndex(tri_idx)

        self.solid_color_btn.set_color(solid_col)
        self.text_color_btn.set_color(text_col)

        self.outline_chk.setChecked(has_out)
        self.outline_options_widget.setVisible(has_out)
        self.outline_color_btn.set_color(out_col)

        self.thick_slider.setValue(max(1, min(5, out_thick)))
        self.on_thickness_changed(self.thick_slider.value())

        self.scale_slider.setValue(max(50, min(180, f_scale)))
        self.scale_val_lbl.setText(f"{self.scale_slider.value()}%")

        saved_yaw = int(self.settings.value("yaw", 45))
        saved_pitch = int(self.settings.value("pitch", 30))
        self.yaw_slider.setValue(max(0, min(360, saved_yaw)))
        self.yaw_val_lbl.setText(f"{self.yaw_slider.value()}°")
        self.pitch_slider.setValue(max(-85, min(85, saved_pitch)))
        self.pitch_val_lbl.setText(f"{self.pitch_slider.value()}°")

        # Logo & Freeform coordinates
        saved_logo = str(self.settings.value("logo_path", ""))
        if saved_logo and Path(saved_logo).is_file():
            self.set_logo(saved_logo)
        saved_logo_scale = int(self.settings.value("logo_scale", 100))
        saved_logo_op = int(self.settings.value("logo_opacity", 90))
        saved_logo_x = int(self.settings.value("logo_pos_x", 88))
        saved_logo_y = int(self.settings.value("logo_pos_y", 5))
        saved_text_x = int(self.settings.value("text_pos_x", 5))
        saved_text_y = int(self.settings.value("text_pos_y", 5))

        self.logo_scale_slider.setValue(max(20, min(250, saved_logo_scale)))
        self.logo_opacity_slider.setValue(max(10, min(100, saved_logo_op)))
        self.logo_x_slider.setValue(max(0, min(100, saved_logo_x)))
        self.logo_y_slider.setValue(max(0, min(100, saved_logo_y)))
        self.text_x_slider.setValue(max(0, min(100, saved_text_x)))
        self.text_y_slider.setValue(max(0, min(100, saved_text_y)))

        saved_font = str(self.settings.value("custom_font_path", ""))
        if saved_font and Path(saved_font).is_file():
            self.set_custom_font(saved_font)

        self.same_folder_chk.setChecked(same_folder)
        if same_folder and last_input:
            self.output_edit.setText(last_input)
            self.output_edit.setEnabled(False)
            self.output_browse_btn.setEnabled(False)

        if last_input and Path(last_input).is_dir():
            QTimer.singleShot(150, self.load_first_preview)

    def _save_settings(self) -> None:
        self.settings.setValue("input", self.input_edit.text().strip())
        self.settings.setValue("output", self.output_edit.text().strip())
        self.settings.setValue("text", self.text_edit.text())
        self.settings.setValue("opacity", self.opacity_slider.value())
        self.settings.setValue("same_folder", self.same_folder_chk.isChecked())
        self.settings.setValue("invert_triangles", self.triangle_combo.currentData())
        self.settings.setValue("solid_color", self.solid_color_btn.color().name())
        self.settings.setValue("text_color", self.text_color_btn.color().name())
        self.settings.setValue("has_outline", self.outline_chk.isChecked())
        self.settings.setValue("outline_color", self.outline_color_btn.color().name())
        self.settings.setValue("outline_thickness", self.thick_slider.value())
        self.settings.setValue("font_scale", self.scale_slider.value())
        self.settings.setValue("theme", self._current_theme)
        self.settings.setValue("yaw", self.yaw_slider.value())
        self.settings.setValue("pitch", self.pitch_slider.value())
        self.settings.setValue("logo_path", self.logo_path)
        self.settings.setValue("logo_scale", self.logo_scale_slider.value())
        self.settings.setValue("logo_opacity", self.logo_opacity_slider.value())
        self.settings.setValue("logo_pos_x", self.logo_x_slider.value())
        self.settings.setValue("logo_pos_y", self.logo_y_slider.value())
        self.settings.setValue("text_pos_x", self.text_x_slider.value())
        self.settings.setValue("text_pos_y", self.text_y_slider.value())
        self.settings.setValue("custom_font_path", self.custom_font_path)

    def get_current_config(self) -> PreviewConfig:
        return PreviewConfig(
            text=self.text_edit.text(),
            position="custom" if self.position_combo.currentData() == "custom" else str(self.position_combo.currentText()),
            opacity=self.opacity_slider.value() / 100.0,
            invert_triangles=bool(self.triangle_combo.currentData()),
            solid_color=self.solid_color_btn.rgb_tuple(),
            text_color=self.text_color_btn.rgb_tuple(),
            has_outline=self.outline_chk.isChecked(),
            outline_color=self.outline_color_btn.rgb_tuple(),
            outline_thickness=self.thick_slider.value(),
            font_scale=self.scale_slider.value() / 100.0,
            yaw=float(self.yaw_slider.value()),
            pitch=float(self.pitch_slider.value()),
            text_pos_x=self.text_x_slider.value() / 100.0,
            text_pos_y=self.text_y_slider.value() / 100.0,
            logo_path=self.logo_path,
            logo_scale=self.logo_scale_slider.value() / 100.0,
            logo_opacity=self.logo_opacity_slider.value() / 100.0,
            logo_pos_x=self.logo_x_slider.value() / 100.0,
            logo_pos_y=self.logo_y_slider.value() / 100.0,
            font_path=self.custom_font_path,
        )
    # ──────────────────────────────────────────────────────────────────
    # User Actions & Handlers
    def choose_logo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Brand Logo or Icon",
            str(Path.home()),
            "Logo Images (*.png *.webp *.svg *.ico *.jpg *.jpeg)",
        )
        if file_path:
            self.set_logo(file_path)
            self._save_settings()
            self.schedule_preview()

    def set_logo(self, path: str) -> None:
        self.logo_path = path
        p = Path(path)
        if p.is_file():
            self.logo_info_lbl.setText(f"✓ Logo: {p.name}")
            self.logo_info_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #10B981;")
            self.clear_logo_btn.setEnabled(True)
            self.logo_options_widget.setVisible(True)
        else:
            self.clear_logo()

    def clear_logo(self) -> None:
        self.logo_path = ""
        self.logo_info_lbl.setText("No logo uploaded")
        self.logo_info_lbl.setStyleSheet("font-size: 11px; color: #6B7280;")
        self.clear_logo_btn.setEnabled(False)
        self.logo_options_widget.setVisible(False)
        self._save_settings()
        self.schedule_preview()

    def on_logo_scale_changed(self, val: int) -> None:
        self.logo_scale_lbl.setText(f"{val}%")
        self.schedule_preview()

    def on_logo_opacity_changed(self, val: int) -> None:
        self.logo_op_lbl.setText(f"{val}%")
        self.schedule_preview()

    def on_logo_pos_combo_changed(self) -> None:
        data = self.logo_pos_combo.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            self.logo_x_slider.blockSignals(True)
            self.logo_y_slider.blockSignals(True)
            self.logo_x_slider.setValue(int(data[0] * 100))
            self.logo_y_slider.setValue(int(data[1] * 100))
            self.logo_x_lbl.setText(f"{self.logo_x_slider.value()}%")
            self.logo_y_lbl.setText(f"{self.logo_y_slider.value()}%")
            self.logo_x_slider.blockSignals(False)
            self.logo_y_slider.blockSignals(False)
            self.schedule_preview()

    def on_logo_coords_changed(self) -> None:
        self.logo_x_lbl.setText(f"{self.logo_x_slider.value()}%")
        self.logo_y_lbl.setText(f"{self.logo_y_slider.value()}%")
        idx = self.logo_pos_combo.findData("custom")
        if idx >= 0:
            self.logo_pos_combo.blockSignals(True)
            self.logo_pos_combo.setCurrentIndex(idx)
            self.logo_pos_combo.blockSignals(False)
        self.schedule_preview()

    def on_text_pos_combo_changed(self) -> None:
        data = self.position_combo.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            self.text_x_slider.blockSignals(True)
            self.text_y_slider.blockSignals(True)
            self.text_x_slider.setValue(int(data[0] * 100))
            self.text_y_slider.setValue(int(data[1] * 100))
            self.text_x_lbl.setText(f"{self.text_x_slider.value()}%")
            self.text_y_lbl.setText(f"{self.text_y_slider.value()}%")
            self.text_x_slider.blockSignals(False)
            self.text_y_slider.blockSignals(False)
            self.schedule_preview()

    def on_text_coords_changed(self) -> None:
        self.text_x_lbl.setText(f"{self.text_x_slider.value()}%")
        self.text_y_lbl.setText(f"{self.text_y_slider.value()}%")
        idx = self.position_combo.findData("custom")
        if idx >= 0:
            self.position_combo.blockSignals(True)
            self.position_combo.setCurrentIndex(idx)
            self.position_combo.blockSignals(False)
        self.schedule_preview()

    def choose_font(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Custom Font File",
            str(Path.home()),
            "Font Files (*.ttf *.otf *.woff *.woff2)",
        )
        if file_path:
            self.set_custom_font(file_path)
            self._save_settings()
            self.schedule_preview()

    def set_custom_font(self, path: str) -> None:
        self.custom_font_path = path
        p = Path(path)
        if p.is_file():
            self.font_info_lbl.setText(f"✓ Custom Font: {p.name}")
            self.font_info_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #0D7A53;")
            self.reset_font_btn.setEnabled(True)
        else:
            self.reset_font()

    def reset_font(self) -> None:
        self.custom_font_path = ""
        self.font_info_lbl.setText("Font: System Default Bold")
        self.font_info_lbl.setStyleSheet("font-size: 11px; color: #4D6775;")
        self.reset_font_btn.setEnabled(False)
        self._save_settings()
        self.schedule_preview()

    def _load_app_icon(self) -> None:
        candidates = [
            Path(__file__).resolve().parent / "app.ico",
            Path(sys.executable).resolve().parent / "app.ico",
            Path(getattr(sys, "_MEIPASS", "")) / "app.ico",
        ]
        for c in candidates:
            if c.exists():
                self.app_icon = QIcon(str(c))
                self.setWindowIcon(self.app_icon)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(self.app_icon)
                self.app_icon_path = str(c)
                break

    def _setup_system_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        if self.app_icon:
            self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip("PreviewGen - Batch Preview Studio")

        menu = QMenu()
        show_action = menu.addAction("Show PreviewGen")
        show_action.triggered.connect(self._restore_from_tray)
        theme_action = menu.addAction("Toggle Dark/Light Mode")
        theme_action.triggered.connect(self.toggle_theme)
        menu.addSeparator()
        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if sys.platform == "win32" and getattr(self, "app_icon_path", None):
            try:
                import ctypes
                hwnd = int(self.winId())
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x0010
                hIcon = ctypes.windll.user32.LoadImageW(
                    0, str(self.app_icon_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE
                )
                if hIcon:
                    WM_SETICON = 0x0080
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hIcon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hIcon)
            except Exception:
                pass
    def on_same_folder_toggled(self, checked: bool) -> None:
        if checked:
            in_dir = self.input_edit.text().strip()
            if in_dir:
                self.output_edit.setText(in_dir)
            self.output_edit.setEnabled(False)
            self.output_browse_btn.setEnabled(False)
        else:
            self.output_edit.setEnabled(True)
            self.output_browse_btn.setEnabled(True)
        self._save_settings()

    def on_opacity_changed(self, value: int) -> None:
        self.op_val_lbl.setText(f"{value}%")
        self.schedule_preview()

    def on_scale_changed(self, value: int) -> None:
        self.scale_val_lbl.setText(f"{value}%")
        self.schedule_preview()

    def on_thickness_changed(self, value: int) -> None:
        labels = {1: "Thin", 2: "Normal", 3: "Medium", 4: "Thick", 5: "Extra Bold"}
        self.thick_val_lbl.setText(labels.get(value, f"{value}x"))
        self.schedule_preview()

    def on_outline_toggled(self, checked: bool) -> None:
        self.outline_options_widget.setVisible(checked)
        self.schedule_preview()

    def choose_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Input PNG Folder", self.input_edit.text() or str(Path.home())
        )
        if folder:
            self.input_edit.setText(folder)
            if self.same_folder_chk.isChecked() or not self.output_edit.text().strip():
                self.output_edit.setText(folder)
            self._save_settings()
            self.load_first_preview()

    def choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Output JPG Folder", self.output_edit.text() or str(Path.home())
        )
        if folder:
            self.output_edit.setText(folder)
            self._save_settings()

    def open_output_folder(self) -> None:
        target = self.output_edit.text().strip() or self.input_edit.text().strip()
        if not target:
            return
        folder = Path(target)
        folder.mkdir(parents=True, exist_ok=True)
        import os
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(folder)])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(folder)])

    def toggle_view_mode(self) -> None:
        self._fit_to_view = self.fit_view_btn.isChecked()
        self.fit_view_btn.setText("Fit to View" if self._fit_to_view else "Original 100%")
        self._update_preview_display()

    # ──────────────────────────────────────────────────────────────────
    # Preview Logic
    # ──────────────────────────────────────────────────────────────────
    def schedule_preview(self) -> None:
        self._preview_timer.start()

    def load_first_preview(self) -> None:
        folder_str = self.input_edit.text().strip()
        if not folder_str:
            return
        folder = Path(folder_str)
        if not folder.is_dir():
            self.preview_label.setText("Input folder does not exist")
            self.file_info_lbl.setText("No file loaded")
            self.file_counter_lbl.setText("0 / 0")
            self.res_info_lbl.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        import zipfile
        import tempfile
        import shutil

        if self._session_zip_dir and self._session_zip_dir.exists():
            shutil.rmtree(self._session_zip_dir, ignore_errors=True)
            self._session_zip_dir = None

        direct_files = [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and p.suffix.lower() != ".zip"
        ]
        zip_files = [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() == ".zip"
        ]

        if zip_files:
            self._session_zip_dir = Path(tempfile.mkdtemp(prefix="previewgen_session_"))
            for z in zip_files:
                try:
                    with zipfile.ZipFile(z, "r") as zf:
                        for member in zf.infolist():
                            t = (self._session_zip_dir / f"{z.stem}_{member.filename}").resolve()
                            if not str(t).startswith(str(self._session_zip_dir.resolve())):
                                continue
                            if member.is_dir() or member.filename.startswith("__MACOSX") or Path(member.filename).name.startswith("."):
                                continue
                            t.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(member) as src, open(t, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                except Exception:
                    pass

            extracted_assets = [
                p for p in self._session_zip_dir.rglob("*.*")
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and p.suffix.lower() != ".zip"
            ]
            self.file_list = sorted(direct_files + extracted_assets)
        else:
            self.file_list = sorted(direct_files)
        if not self.file_list:
            self.preview_source = None
            self.current_file_idx = 0
            ext_str = ", ".join(ext.upper().lstrip(".") for ext in SUPPORTED_EXTENSIONS)
            self.preview_label.setText(f"No supported images found in:\n{folder.name}\n\nSupported: {ext_str}")
            self.file_info_lbl.setText("No supported images found")
            self.file_counter_lbl.setText("0 / 0")
            self.res_info_lbl.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.panel_3d.setVisible(False)
            self.preview_label.set_3d_mode(False)
            return

        self.current_file_idx = 0
        self._update_active_file()

    def go_prev_file(self) -> None:
        if self.file_list and self.current_file_idx > 0:
            self.current_file_idx -= 1
            self._update_active_file()

    def go_next_file(self) -> None:
        if self.file_list and self.current_file_idx < len(self.file_list) - 1:
            self.current_file_idx += 1
            self._update_active_file()

    def _update_active_file(self) -> None:
        if not self.file_list:
            return
        self.preview_source = self.file_list[self.current_file_idx]
        total = len(self.file_list)
        self.file_counter_lbl.setText(f"{self.current_file_idx + 1} / {total}")
        self.prev_btn.setEnabled(self.current_file_idx > 0)
        self.next_btn.setEnabled(self.current_file_idx < total - 1)

        is_3d = self.preview_source.suffix.lower() in SUPPORTED_3D_EXTENSIONS or self.preview_source.suffix.lower() in (".step", ".stp", ".iges", ".igs")
        self.panel_3d.setVisible(is_3d)
        self.preview_label.set_3d_mode(is_3d)

        self._do_refresh_preview()

    def on_yaw_changed(self, value: int) -> None:
        self.yaw_val_lbl.setText(f"{value}°")
        self.schedule_preview()

    def on_pitch_changed(self, value: int) -> None:
        self.pitch_val_lbl.setText(f"{value}°")
        self.schedule_preview()

    def set_3d_angle(self, yaw: float, pitch: float) -> None:
        self.yaw_slider.setValue(int(yaw))
        self.pitch_slider.setValue(int(pitch))
        self.schedule_preview()

    def on_orbit_drag(self, dyaw: float, dpitch: float) -> None:
        new_yaw = (self.yaw_slider.value() + int(round(dyaw))) % 360
        new_pitch = max(-85, min(85, self.pitch_slider.value() + int(round(dpitch))))
        self.yaw_slider.setValue(new_yaw)
        self.pitch_slider.setValue(new_pitch)
        self.schedule_preview()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Left:
            self.go_prev_file()
        elif event.key() == Qt.Key.Key_Right:
            self.go_next_file()
        else:
            super().keyPressEvent(event)

    def _do_refresh_preview(self) -> None:
        if not self.preview_source or not self.preview_source.is_file():
            return

        self._current_preview_task_id += 1
        task_id = self._current_preview_task_id
        config = self.get_current_config()

        worker = AsyncPreviewWorker(task_id, self.preview_source, config)
        worker.signals.ready.connect(self._on_preview_ready)
        worker.signals.error.connect(self._on_preview_error)
        self.preview_thread_pool.start(worker)

    def _on_preview_ready(self, task_id: int, pixmap: QPixmap, name: str, w: int, h: int) -> None:
        if task_id != self._current_preview_task_id:
            return

        self._raw_pixmap = pixmap
        ext_badge = self.preview_source.suffix.upper().lstrip(".") if self.preview_source else ""
        self.file_info_lbl.setText(f"Preview: {name}  [{ext_badge}]")
        self.res_info_lbl.setText(f"{w} × {h} px")
        self._update_preview_display()

    def _on_preview_error(self, task_id: int, err: str) -> None:
        if task_id != self._current_preview_task_id:
            return
        self.preview_label.setText(f"Preview error:\n{err}")
        self.file_info_lbl.setText("Error loading preview")

    def _ensure_desktop_shortcut(self) -> None:
        """Ensure an official desktop shortcut exists across Windows, macOS, and Linux."""
        try:
            if sys.platform == "win32":
                import subprocess
                exe = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve().parent / "dist" / "PreviewGen" / "PreviewGen.exe")
                if not Path(exe).is_file():
                    return
                ico = str(Path(exe).parent / "app.ico")
                if not Path(ico).is_file():
                    ico = str(Path(__file__).resolve().parent / "app.ico")
                ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
if ($desktop -and (Test-Path $desktop)) {{
    $lnk = Join-Path $desktop "PreviewGen.lnk"
    if (-not (Test-Path $lnk)) {{
        $s = $wsh.CreateShortcut($lnk)
        $s.TargetPath = '{exe}'
        $s.WorkingDirectory = '{Path(exe).parent}'
        if (Test-Path '{ico}') {{ $s.IconLocation = '{ico},0' }}
        $s.Description = 'PreviewGen - Transparent PNG to JPG Preview Generator'
        $s.Save()
    }}
}}
"""
                subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script], creationflags=0x08000000)
            elif sys.platform == "darwin":
                desktop = Path.home() / "Desktop" / "PreviewGen"
                app_path = Path("/Applications/PreviewGen.app")
                if desktop.parent.exists() and not desktop.exists() and app_path.exists():
                    desktop.symlink_to(app_path)
            elif sys.platform.startswith("linux"):
                desktop = Path.home() / "Desktop" / "PreviewGen.desktop"
                app_entry = Path.home() / ".local/share/applications/previewgen.desktop"
                if desktop.parent.exists() and not desktop.exists() and app_entry.exists():
                    import shutil
                    shutil.copyfile(app_entry, desktop)
                    desktop.chmod(0o755)
        except Exception:
            pass
    def _update_preview_display(self) -> None:
        if not self._raw_pixmap or self._raw_pixmap.isNull():
            return

        if self._fit_to_view:
            viewport_size = self.preview_scroll.viewport().size()
            target_w = max(100, viewport_size.width() - 20)
            target_h = max(100, viewport_size.height() - 20)
            scaled = self._raw_pixmap.scaled(
                target_w, target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)
            self.preview_label.adjustSize()
        else:
            self.preview_label.setPixmap(self._raw_pixmap)
            self.preview_label.adjustSize()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._fit_to_view:
            self._update_preview_display()

    # ──────────────────────────────────────────────────────────────────
    # Batch Processing
    # ──────────────────────────────────────────────────────────────────
    def start_processing(self) -> None:
        in_str = self.input_edit.text().strip()
        out_str = self.output_edit.text().strip()

        if not in_str:
            QMessageBox.warning(self, "Missing Input", "Please select an input folder.")
            return

        input_folder = Path(in_str)
        if not input_folder.is_dir():
            QMessageBox.warning(self, "Invalid Input", "The input folder does not exist.")
            return

        if not out_str:
            out_str = in_str
            self.output_edit.setText(out_str)

        output_folder = Path(out_str)
        self._save_settings()

        asset_files = [
            p for p in input_folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if not asset_files:
            ext_str = ", ".join(ext.upper().lstrip(".") for ext in SUPPORTED_EXTENSIONS)
            QMessageBox.warning(
                self,
                "No Supported Images",
                f"No supported images were found in the input folder.\n\nSupported formats: {ext_str}",
            )
            return

        total = len(asset_files)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.stats_widget.setVisible(True)
        self.chip_success.setText("0 Success")
        self.chip_failed.setText("0 Failed")
        self.chip_pending.setText(f"{total} Total")

        self.status_lbl.setText(f"Processing 1 of {total}…")
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.input_browse_btn.setEnabled(False)
        self.output_browse_btn.setEnabled(False)

        config = self.get_current_config()
        self.worker = BatchWorker(input_folder, output_folder, config)
        self.worker.signals.progress.connect(self.on_progress)
        self.worker.signals.finished.connect(self.on_finished)
        self.worker.signals.failed.connect(self.on_failed)
        self.thread_pool.start(self.worker)

    def cancel_processing(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status_lbl.setText("Cancelling… finishing current image.")

    def on_progress(self, current: int, total: int, message: str) -> None:
        pct = round(current * 100 / total)
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(f"{current}/{total} — {message}")
        self.chip_success.setText(f"{current} Success")
        self.chip_pending.setText(f"{max(0, total - current)} Remaining")

    def on_finished(self, success: int, failed: int, errors: list, cancelled: bool) -> None:
        self._set_idle()
        out_dir = Path(self.output_edit.text().strip()).resolve()
        heading = "Cancelled" if cancelled else "Completed"

        self.chip_success.setText(f"{success} Success")
        self.chip_failed.setText(f"{failed} Failed")
        self.chip_pending.setText("0 Remaining")
        self.status_lbl.setText(f"{heading}! {success} preview(s) saved in {out_dir.name}")

        summary = (
            f"<b>{heading}!</b><br><br>"
            f"<b>Destination:</b><br>{out_dir}<br><br>"
            f"<b>Successful:</b> {success} previews<br>"
            f"<b>Failed:</b> {failed}"
        )
        if errors:
            summary += "<br><br><b>Errors:</b><br>" + "<br>".join(errors[:8])
            if len(errors) > 8:
                summary += f"<br><i>…and {len(errors) - 8} more.</i>"

        t = THEME[self._current_theme]
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Previews {heading}")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(summary)
        msg_box.setIcon(QMessageBox.Icon.Information if not cancelled else QMessageBox.Icon.Warning)

        open_btn = msg_box.addButton("Open Output Folder", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        msg_box.setStyleSheet(f"""
            QMessageBox {{ background: {t["card_bg"]}; }}
            QLabel {{ color: {t["text"]}; font-size: 13px; }}
            QPushButton {{
                min-width: 100px; padding: 9px 18px; border-radius: 8px;
                background: {t["accent"]}; color: white; font-weight: 600;
            }}
            QPushButton:hover {{ background: {t["accent_hover"]}; }}
        """)
        msg_box.exec()
        if msg_box.clickedButton() == open_btn:
            self.open_output_folder()

    def on_failed(self, message: str) -> None:
        self._set_idle()
        self.status_lbl.setText("Processing failed")
        QMessageBox.critical(self, "Processing Failed", message)

    def _set_idle(self) -> None:
        self.worker = None
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.input_browse_btn.setEnabled(True)
        if not self.same_folder_chk.isChecked():
            self.output_browse_btn.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self.worker:
            self.worker.cancel()
        if self._session_zip_dir and self._session_zip_dir.exists():
            import shutil
            shutil.rmtree(self._session_zip_dir, ignore_errors=True)
        self._save_settings()
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────
# Application Entry Point
# ──────────────────────────────────────────────────────────────────────
def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "MustaqeemTools.PreviewGen.1.0"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("PreviewGen")
    app.setApplicationDisplayName("PreviewGen")
    app.setStyleSheet(build_stylesheet(THEME[LIGHT]))

    # Load multi-resolution icon
    icon_candidates = [
        Path(__file__).resolve().parent / "app.ico",
        Path(sys.executable).resolve().parent / "app.ico",
        Path(getattr(sys, "_MEIPASS", "")) / "app.ico",
    ]
    app_icon = None
    for cand in icon_candidates:
        if cand.exists():
            app_icon = QIcon(str(cand))
            app.setWindowIcon(app_icon)
            break

    window = MainWindow()
    if app_icon:
        window.setWindowIcon(app_icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
