"""
Halaman Utama Master Data Karyawan SIAP Desktop (Tahap 2).
Menyediakan antarmuka manajemen data pegawai lengkap:
- Kartu ringkasan metrik statistik (Total, Aktif, Nonaktif, Tanpa NIK)
- Filter unit, jabatan, status, dan pencarian kata kunci
- Tabel data pegawai dengan badge status kepegawaian
- Operasi Tambah, Edit, Soft Delete (Nonaktifkan), Hapus Permanen terproteksi relasi
- Import data dari file Excel / CSV dengan pratinjau & opsi duplikasi
- Export data ke format Excel / CSV
- Paginasi data dengan kontrol jumlah per halaman
- Kontrol hak akses berbasis peran (Admin & Operator)
"""
from typing import Optional, Dict, Any, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QFileDialog,
)
from config.settings import THEME
from database.models import User, UserRole
from services.employee_service import EmployeeService
from services.employee_import_service import EmployeeImportService
from ui.widgets.employee_form_dialog import EmployeeFormDialog
from ui.widgets.employee_import_dialog import EmployeeImportDialog


class MetricCard(QFrame):
    """Kartu metrik statistik ringkas."""

    def __init__(self, title: str, value: str, icon: str, color_accent: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Icon box
        icon_box = QLabel(icon)
        icon_box.setFixedSize(40, 40)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet(f"""
            background-color: {color_accent}15;
            color: {color_accent};
            font-size: 18px;
            font-weight: 700;
            border-radius: 8px;
        """)
        layout.addWidget(icon_box)

        # Text layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a;")
        text_layout.addWidget(self.lbl_val)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 500; color: #64748b;")
        text_layout.addWidget(lbl_title)

        layout.addLayout(text_layout)
        layout.addStretch()

    def update_value(self, val: str):
        self.lbl_val.setText(str(val))


class EmployeesPage(QWidget):
    """Halaman Pengelolaan Master Data Karyawan."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.is_admin = (user.role == UserRole.ADMIN) if user else True

        # State Paginasi & Filter
        self.current_page = 1
        self.per_page = 15
        self.total_records = 0
        self.total_pages = 1

        self._init_ui()
        self.load_data()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        # 1. Header Toolbar (Judul + Tombol Aksi)
        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        title_lbl = QLabel("Master Data Karyawan")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_PRIMARY']};")
        header_text.addWidget(title_lbl)

        desc_lbl = QLabel("Pengelolaan identitas pegawai, nomor mesin absensi (PIN/Barcode), unit kerja, dan status.")
        desc_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        header_text.addWidget(desc_lbl)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        # Tombol Aksi Kanan
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_refresh = QPushButton("🔄  Segarkan")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet(self._btn_secondary_style())
        self.btn_refresh.clicked.connect(self.load_data)
        btn_layout.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("📤  Export Excel")
        self.btn_export.setFixedHeight(36)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet(self._btn_secondary_style())
        self.btn_export.clicked.connect(self._on_export_clicked)
        btn_layout.addWidget(self.btn_export)

        self.btn_import = QPushButton("📥  Import Excel")
        self.btn_import.setFixedHeight(36)
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.setStyleSheet(self._btn_secondary_style())
        self.btn_import.clicked.connect(self._on_import_clicked)
        btn_layout.addWidget(self.btn_import)

        self.btn_add = QPushButton("➕  Tambah Karyawan")
        self.btn_add.setFixedHeight(36)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.btn_add.clicked.connect(self._on_add_clicked)
        btn_layout.addWidget(self.btn_add)

        header_layout.addLayout(btn_layout)
        root_layout.addLayout(header_layout)

        # 2. Metric Cards Grid (4 Kartu Ringkasan)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_total = MetricCard("Total Karyawan", "0", "👥", "#2563eb")
        self.card_aktif = MetricCard("Karyawan Aktif", "0", "✓", "#16a34a")
        self.card_nonaktif = MetricCard("Nonaktif / Resign", "0", "✕", "#64748b")
        self.card_no_nik = MetricCard("Belum Memiliki NIK", "0", "⚠", "#d97706")

        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_aktif)
        cards_layout.addWidget(self.card_nonaktif)
        cards_layout.addWidget(self.card_no_nik)
        root_layout.addLayout(cards_layout)

        # 3. Filter and Search Toolbar Bar
        filter_bar = QFrame()
        filter_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(10, 6, 10, 6)
        filter_layout.setSpacing(10)

        # Search Input
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍  Cari nama, No. ID, NIP, atau NIK...")
        self.txt_search.setFixedHeight(34)
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 1.5px solid #2563eb;
                background-color: #ffffff;
            }
        """)
        self.txt_search.returnPressed.connect(self._on_search_triggered)
        filter_layout.addWidget(self.txt_search, 2)

        # Filter Unit Dropdown
        self.cmb_filter_unit = QComboBox()
        self.cmb_filter_unit.setFixedHeight(34)
        self.cmb_filter_unit.addItem("Semua Unit")
        self.cmb_filter_unit.setStyleSheet(self._combo_style())
        self.cmb_filter_unit.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.cmb_filter_unit, 1)

        # Filter Jabatan Dropdown
        self.cmb_filter_jabatan = QComboBox()
        self.cmb_filter_jabatan.setFixedHeight(34)
        self.cmb_filter_jabatan.addItem("Semua Jabatan")
        self.cmb_filter_jabatan.setStyleSheet(self._combo_style())
        self.cmb_filter_jabatan.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.cmb_filter_jabatan, 1)

        # Filter Status Dropdown
        self.cmb_filter_status = QComboBox()
        self.cmb_filter_status.setFixedHeight(34)
        self.cmb_filter_status.addItems(["Semua Status", "AKTIF", "NONAKTIF"])
        self.cmb_filter_status.setStyleSheet(self._combo_style())
        self.cmb_filter_status.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.cmb_filter_status, 1)

        # Tombol Reset Filter
        btn_reset = QPushButton("Reset")
        btn_reset.setFixedHeight(34)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet(self._btn_secondary_style())
        btn_reset.clicked.connect(self._on_reset_filters)
        filter_layout.addWidget(btn_reset)

        root_layout.addWidget(filter_bar)

        # 4. Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "No",
            "No. ID / PIN",
            "No. Pegawai",
            "NIK",
            "Nama Lengkap",
            "Unit / Departemen",
            "Jabatan",
            "Status",
            "Aksi",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Nama Karyawan
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 12px;
                color: #1e293b;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #475569;
                font-weight: 700;
                font-size: 11px;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item:selected {
                background-color: #eff6ff;
                color: #1e3a8a;
            }
        """)
        root_layout.addWidget(self.table, 1)

        # 5. Pagination Bar
        page_bar = QHBoxLayout()
        page_bar.setContentsMargins(4, 0, 4, 0)

        # Per page dropdown
        lbl_per_page = QLabel("Tampilkan:")
        lbl_per_page.setStyleSheet("font-size: 11px; color: #64748b;")
        page_bar.addWidget(lbl_per_page)

        self.cmb_per_page = QComboBox()
        self.cmb_per_page.setFixedHeight(28)
        self.cmb_per_page.addItems(["15", "25", "50", "100"])
        self.cmb_per_page.setStyleSheet(self._combo_style())
        self.cmb_per_page.currentTextChanged.connect(self._on_per_page_changed)
        page_bar.addWidget(self.cmb_per_page)

        page_bar.addSpacing(16)

        self.lbl_page_info = QLabel("Menampilkan 0 dari 0 data")
        self.lbl_page_info.setStyleSheet("font-size: 12px; color: #64748b;")
        page_bar.addWidget(self.lbl_page_info)

        page_bar.addStretch()

        # Prev/Next Buttons
        self.btn_prev = QPushButton("◀ Sebelumnya")
        self.btn_prev.setFixedHeight(30)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(self._btn_secondary_style())
        self.btn_prev.clicked.connect(self._on_prev_page)
        page_bar.addWidget(self.btn_prev)

        self.lbl_current_page = QLabel("Halaman 1 / 1")
        self.lbl_current_page.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155; margin: 0 8px;")
        page_bar.addWidget(self.lbl_current_page)

        self.btn_next = QPushButton("Berikutnya ▶")
        self.btn_next.setFixedHeight(30)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(self._btn_secondary_style())
        self.btn_next.clicked.connect(self._on_next_page)
        page_bar.addWidget(self.btn_next)

        root_layout.addLayout(page_bar)

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                color: #0f172a;
            }
            QComboBox:focus {
                border: 1.5px solid #2563eb;
            }
        """

    def _btn_secondary_style(self) -> str:
        return """
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
            }
        """

    def load_data(self):
        """Memuat ulang data statistik, unit suggestions, dan daftar karyawan."""
        # 1. Update Statistik Ringkas
        stats = EmployeeService.get_statistics()
        self.card_total.update_value(str(stats.get("total_karyawan", 0)))
        self.card_aktif.update_value(str(stats.get("aktif", 0)))
        self.card_nonaktif.update_value(str(stats.get("nonaktif", 0)))
        self.card_no_nik.update_value(str(stats.get("tanpa_nik", 0)))

        # 2. Update Options Unit & Jabatan jika baru
        current_unit = self.cmb_filter_unit.currentText()
        distinct_units = EmployeeService.get_distinct_units()
        self.cmb_filter_unit.blockSignals(True)
        self.cmb_filter_unit.clear()
        self.cmb_filter_unit.addItem("Semua Unit")
        for u in distinct_units:
            self.cmb_filter_unit.addItem(u)
        if current_unit in distinct_units:
            self.cmb_filter_unit.setCurrentText(current_unit)
        self.cmb_filter_unit.blockSignals(False)

        current_jab = self.cmb_filter_jabatan.currentText()
        distinct_jabs = EmployeeService.get_distinct_jabatans()
        self.cmb_filter_jabatan.blockSignals(True)
        self.cmb_filter_jabatan.clear()
        self.cmb_filter_jabatan.addItem("Semua Jabatan")
        for j in distinct_jabs:
            self.cmb_filter_jabatan.addItem(j)
        if current_jab in distinct_jabs:
            self.cmb_filter_jabatan.setCurrentText(current_jab)
        self.cmb_filter_jabatan.blockSignals(False)

        # 3. Query Karyawan dengan Filter
        search_kw = self.txt_search.text().strip()
        unit_kw = self.cmb_filter_unit.currentText()
        jab_kw = self.cmb_filter_jabatan.currentText()
        status_kw = self.cmb_filter_status.currentText()

        result = EmployeeService.get_employees(
            search=search_kw,
            unit=unit_kw,
            jabatan=jab_kw,
            status=status_kw,
            page=self.current_page,
            per_page=self.per_page,
        )

        items = result.get("items", [])
        self.total_records = result.get("total", 0)
        self.total_pages = result.get("total_pages", 1)

        # Update Tabel
        self.table.setRowCount(len(items))
        offset = (self.current_page - 1) * self.per_page

        for row_idx, emp in enumerate(items):
            # Col 0: No
            no_item = QTableWidgetItem(str(offset + row_idx + 1))
            no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, no_item)

            # Col 1: No ID / PIN
            id_item = QTableWidgetItem(emp.get("no_id") or "-")
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, id_item)

            # Col 2: No Pegawai
            emp_num_item = QTableWidgetItem(emp.get("emp_num") or "-")
            emp_num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, emp_num_item)

            # Col 3: NIK
            nik_val = emp.get("nik") or "-"
            nik_item = QTableWidgetItem(nik_val)
            nik_item.setTextAlignment(Qt.AlignCenter)
            if nik_val == "-":
                nik_item.setForeground(Qt.darkGray)
            self.table.setItem(row_idx, 3, nik_item)

            # Col 4: Nama
            nama_item = QTableWidgetItem(emp.get("nama"))
            nama_item.setFont(self.font())
            self.table.setItem(row_idx, 4, nama_item)

            # Col 5: Unit
            self.table.setItem(row_idx, 5, QTableWidgetItem(emp.get("unit") or "-"))

            # Col 6: Jabatan
            self.table.setItem(row_idx, 6, QTableWidgetItem(emp.get("jabatan") or "-"))

            # Col 7: Status Badge
            status_str = emp.get("status")
            status_item = QTableWidgetItem(f" {status_str} ")
            status_item.setTextAlignment(Qt.AlignCenter)
            if status_str == "AKTIF":
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.darkGray)
            self.table.setItem(row_idx, 7, status_item)

            # Col 8: Action Buttons (Edit, Nonaktifkan/Aktifkan, Hapus)
            action_widget = self._create_row_actions(emp)
            self.table.setCellWidget(row_idx, 8, action_widget)

        # Set Table Row Heights
        for r in range(len(items)):
            self.table.setRowHeight(r, 40)

        # Update Paginasi Info
        start_idx = offset + 1 if self.total_records > 0 else 0
        end_idx = min(offset + self.per_page, self.total_records)
        self.lbl_page_info.setText(f"Menampilkan {start_idx} - {end_idx} dari {self.total_records} data")
        self.lbl_current_page.setText(f"Halaman {self.current_page} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

    def _create_row_actions(self, emp: Dict[str, Any]) -> QWidget:
        """Membuat widget tombol aksi di setiap baris tabel data karyawan."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        emp_id = emp["id"]
        is_active = emp["status"] == "AKTIF"

        # 1. Tombol Edit
        btn_edit = QPushButton("✏️ Edit")
        btn_edit.setToolTip("Perbarui data profil karyawan")
        btn_edit.setFixedHeight(26)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                padding: 0 6px;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)
        btn_edit.clicked.connect(lambda _, eid=emp_id: self._on_edit_clicked(eid))
        layout.addWidget(btn_edit)

        # 2. Tombol Toggle Status (Soft Delete)
        toggle_label = "Nonaktifkan" if is_active else "Aktifkan"
        btn_toggle = QPushButton(toggle_label)
        btn_toggle.setToolTip("Ubah status kepegawaian (soft delete/pulihkan)")
        btn_toggle.setFixedHeight(26)
        btn_toggle.setCursor(Qt.PointingHandCursor)
        if is_active:
            btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #fffbeb;
                    color: #b45309;
                    border: 1px solid #fde68a;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 0 6px;
                }
                QPushButton:hover {
                    background-color: #fef3c7;
                }
            """)
        else:
            btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #f0fdf4;
                    color: #15803d;
                    border: 1px solid #bbf7d0;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 0 6px;
                }
                QPushButton:hover {
                    background-color: #dcfce7;
                }
            """)
        btn_toggle.clicked.connect(lambda _, eid=emp_id: self._on_toggle_status_clicked(eid))
        layout.addWidget(btn_toggle)

        # 3. Tombol Hapus Permanen (Khusus Admin)
        btn_delete = QPushButton("🗑️")
        btn_delete.setToolTip("Hapus permanen (Hanya untuk Admin jika belum ada transaksi)")
        btn_delete.setFixedHeight(26)
        btn_delete.setFixedWidth(28)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
        """)
        btn_delete.clicked.connect(lambda _, eid=emp_id: self._on_delete_clicked(eid))
        layout.addWidget(btn_delete)

        return widget

    def _on_search_triggered(self):
        self.current_page = 1
        self.load_data()

    def _on_filter_changed(self):
        self.current_page = 1
        self.load_data()

    def _on_reset_filters(self):
        self.txt_search.clear()
        self.cmb_filter_unit.setCurrentIndex(0)
        self.cmb_filter_jabatan.setCurrentIndex(0)
        self.cmb_filter_status.setCurrentIndex(0)
        self.current_page = 1
        self.load_data()

    def _on_per_page_changed(self, text: str):
        if text.isdigit():
            self.per_page = int(text)
            self.current_page = 1
            self.load_data()

    def _on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def _on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def _on_add_clicked(self):
        """Membuka dialog tambah karyawan."""
        units = EmployeeService.get_distinct_units()
        dlg = EmployeeFormDialog(self, employee_data=None, unit_suggestions=units)
        if dlg.exec() == EmployeeFormDialog.Accepted:
            data = dlg.get_form_data()
            user_id = self.user.id if self.user else None
            success, emp, err = EmployeeService.create_employee(data, user_id=user_id)
            if success:
                QMessageBox.information(self, "Berhasil", f"Karyawan '{data['nama']}' berhasil ditambahkan ke sistem.")
                self.load_data()
            else:
                QMessageBox.warning(self, "Gagal Menambahkan Karyawan", err or "Terjadi kesalahan menyimpan data.")

    def _on_edit_clicked(self, emp_id: int):
        """Membuka dialog edit profil karyawan."""
        emp = EmployeeService.get_employee_by_id(emp_id)
        if not emp:
            QMessageBox.warning(self, "Tidak Ditemukan", f"Karyawan dengan ID {emp_id} tidak ditemukan.")
            return

        units = EmployeeService.get_distinct_units()
        dlg = EmployeeFormDialog(self, employee_data=emp, unit_suggestions=units)
        if dlg.exec() == EmployeeFormDialog.Accepted:
            data = dlg.get_form_data()
            user_id = self.user.id if self.user else None
            success, updated_emp, err = EmployeeService.update_employee(emp_id, data, user_id=user_id)
            if success:
                QMessageBox.information(self, "Berhasil", f"Data karyawan '{data['nama']}' berhasil diperbarui.")
                self.load_data()
            else:
                QMessageBox.warning(self, "Gagal Memperbarui", err or "Terjadi kesalahan menyimpan perubahan.")

    def _on_toggle_status_clicked(self, emp_id: int):
        """Mengubah status aktif / nonaktif (soft delete)."""
        emp = EmployeeService.get_employee_by_id(emp_id)
        if not emp:
            return

        current_status = emp.get("status")
        target_status = "NONAKTIF" if current_status == "AKTIF" else "AKTIF"

        confirm = QMessageBox.question(
            self,
            "Konfirmasi Ubah Status",
            (
                f"Apakah Anda yakin ingin mengubah status karyawan:\n'{emp['nama']}'\n\n"
                f"Status akan diubah dari {current_status} menjadi {target_status}."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            user_id = self.user.id if self.user else None
            success, new_status, err = EmployeeService.toggle_status(emp_id, user_id=user_id)
            if success:
                self.load_data()
            else:
                QMessageBox.warning(self, "Gagal Mengubah Status", err or "Terjadi kesalahan sistem.")

    def _on_delete_clicked(self, emp_id: int):
        """Menghapus data karyawan secara permanen jika diizinkan."""
        # Proteksi hak akses role
        if not self.is_admin:
            QMessageBox.warning(
                self,
                "Akses Ditolak",
                "Penghapusan data karyawan permanen hanya dapat dilakukan oleh Administrator.\n"
                "Untuk Operator, silakan gunakan fitur 'Nonaktifkan Karyawan'.",
            )
            return

        emp = EmployeeService.get_employee_by_id(emp_id)
        if not emp:
            return

        confirm = QMessageBox.warning(
            self,
            "Peringatan Hapus Permanen",
            (
                f"Tindakan ini akan menghapus data karyawan secara permanen:\n'{emp['nama']}' (ID: {emp_id}).\n\n"
                f"PERHATIAN: Jika karyawan sudah memiliki catatan absensi, sistem akan menolak penghapusan "
                f"untuk menjaga integritas pembukuan.\n\n"
                f"Apakah Anda tetap ingin melanjutkan?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            user_id = self.user.id if self.user else None
            success, err = EmployeeService.delete_employee(emp_id, user_id=user_id)
            if success:
                QMessageBox.information(self, "Berhasil Dihapus", f"Karyawan '{emp['nama']}' berhasil dihapus.")
                self.load_data()
            else:
                QMessageBox.critical(self, "Penghapusan Ditolak", err or "Gagal menghapus data karyawan.")

    def _on_import_clicked(self):
        """Membuka dialog import karyawan dari Excel."""
        user_id = self.user.id if self.user else None
        dlg = EmployeeImportDialog(self, user_id=user_id)
        if dlg.exec() == EmployeeImportDialog.Accepted:
            self.load_data()

    def _on_export_clicked(self):
        """Mengekspor data karyawan saat ini ke Excel atau CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Berkas Data Karyawan",
            "Data_Karyawan_SIAP.xlsx",
            "Excel Workbook (*.xlsx);;CSV (Titik Koma) (*.csv)",
        )
        if not file_path:
            return

        search_kw = self.txt_search.text().strip()
        unit_kw = self.cmb_filter_unit.currentText()
        status_kw = self.cmb_filter_status.currentText()
        user_id = self.user.id if self.user else None

        success, err = EmployeeImportService.export_employees(
            target_file_path=file_path,
            unit=unit_kw if unit_kw != "Semua Unit" else None,
            status=status_kw if status_kw != "Semua Status" else None,
            search=search_kw if search_kw else None,
            user_id=user_id,
        )

        if success:
            QMessageBox.information(
                self,
                "Export Berhasil",
                f"Data master karyawan berhasil diekspor ke berkas:\n{file_path}",
            )
        else:
            QMessageBox.critical(self, "Export Gagal", err or "Terjadi kesalahan saat mengekspor data.")
