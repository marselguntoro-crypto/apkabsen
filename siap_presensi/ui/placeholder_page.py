"""
Widget Halaman Placeholder untuk Menu yang Akan Dikembangkan pada Tahap Berikutnya.
Menampilkan pesan informatif dan transparan sesuai panduan Tahap 1.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from config.settings import THEME


class PlaceholderPage(QWidget):
    """Halaman penampung transparan untuk modul yang dialokasikan pada tahap berikutnya."""

    def __init__(self, module_title: str, module_description: str = "", parent=None):
        super().__init__(parent)
        self.module_title = module_title
        self.module_description = module_description
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setFixedWidth(540)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 12px;
                padding: 32px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(12)

        icon_lbl = QLabel("🚧")
        icon_lbl.setStyleSheet("font-size: 48px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_lbl)

        title_lbl = QLabel(self.module_title)
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        title_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_lbl)

        status_badge = QLabel("TAHAP PENGEMBANGAN")
        status_badge.setStyleSheet(f"""
            background-color: #fef3c7;
            color: #b45309;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #fde68a;
        """)
        status_badge.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(status_badge)

        msg_lbl = QLabel("Modul akan tersedia pada tahap berikutnya.")
        msg_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {THEME['BLUE_PRIMARY']};")
        msg_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(msg_lbl)

        if self.module_description:
            desc_lbl = QLabel(self.module_description)
            desc_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']}; line-height: 1.5;")
            desc_lbl.setAlignment(Qt.AlignCenter)
            desc_lbl.setWordWrap(True)
            card_layout.addWidget(desc_lbl)

        layout.addWidget(card)
