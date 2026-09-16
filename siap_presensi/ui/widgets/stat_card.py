"""
Komponen Widget Kartu Statistik untuk Dashboard SIAP.
Menampilkan judul metrik, nilai utama (angka/rupiah), indikator warna,
dan keterangan tambahan dengan estetika flat modern.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from config.settings import THEME


class StatCard(QFrame):
    """Widget kartu ringkasan metrik statistik dashboard."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        accent_color: str = THEME["BLUE_PRIMARY"],
        parent=None,
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setObjectName("StatCard")
        self.setFrameShape(QFrame.NoFrame)
        self._init_ui(title, value, subtitle)

    def _init_ui(self, title: str, value: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        # Header: Title + Accent Bar
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")
        self.title_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {THEME['TEXT_MUTED']}; text-transform: uppercase; letter-spacing: 0.5px;"
        )
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        # Accent dot
        accent_dot = QFrame()
        accent_dot.setFixedSize(10, 10)
        accent_dot.setStyleSheet(
            f"background-color: {self.accent_color}; border-radius: 5px;"
        )
        top_layout.addWidget(accent_dot)
        layout.addLayout(top_layout)

        # Nilai Utama
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        self.value_label.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {THEME['NAVY_DARK']}; margin-top: 4px;"
        )
        layout.addWidget(self.value_label)

        # Subtitle / Keterangan
        self.sub_label = QLabel(subtitle if subtitle else "Data periode aktif")
        self.sub_label.setObjectName("statSubtitle")
        self.sub_label.setStyleSheet(
            f"font-size: 12px; color: {THEME['TEXT_MUTED']};"
        )
        layout.addWidget(self.sub_label)

        # Styling Card Container
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
            }}
            QFrame#StatCard:hover {{
                border: 1px solid {self.accent_color};
            }}
        """)

    def update_value(self, new_value: str, new_subtitle: str = ""):
        """Memperbarui nilai dan subteks kartu."""
        self.value_label.setText(str(new_value))
        if new_subtitle:
            self.sub_label.setText(new_subtitle)
