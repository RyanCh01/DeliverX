import os
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QTextEdit,
    QScrollArea, QFrame, QListWidget
)
from PySide2.QtCore import Qt
from generators.iso_generator import generate_iso


class ISOTab(QWidget):
    def __init__(self):
        super().__init__()
        self.files_to_pack = []  # [{"source_path": ..., "name_in_iso": ...}]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)

        # Title
        title = QLabel("ISO/IMG Packager")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Package payload and decoy files into an ISO image. "
            "When the target double-clicks the ISO, Windows auto-mounts it. "
            "Files inside the mounted ISO do not carry the MOTW flag, "
            "bypassing SmartScreen and Office macro disable policies."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- File List ---
        files_group = QGroupBox("Files to Pack")
        files_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        self.file_list.setStyleSheet(
            "QListWidget { background-color: #12122a; border: 1px solid #2d2d4e; border-radius: 6px; }"
            "QListWidget::item { padding: 6px; color: #e0e0e0; }"
            "QListWidget::item:selected { background-color: #e94560; }"
        )
        files_layout.addWidget(self.file_list)

        # Button row
        btn_row = QHBoxLayout()

        self.add_file_btn = QPushButton("➕ Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        btn_row.addWidget(self.add_file_btn)

        self.add_lnk_btn = QPushButton("🔗 Add LNK (from outputs/)")
        self.add_lnk_btn.clicked.connect(self.add_lnk_from_outputs)
        btn_row.addWidget(self.add_lnk_btn)

        self.remove_file_btn = QPushButton("❌ Remove Selected")
        self.remove_file_btn.clicked.connect(self.remove_file)
        btn_row.addWidget(self.remove_file_btn)

        self.clear_files_btn = QPushButton("🗑 Clear List")
        self.clear_files_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.clear_files_btn)

        files_layout.addLayout(btn_row)

        # Rename in ISO
        rename_row = QHBoxLayout()
        rename_row.addWidget(QLabel("Name in ISO:"))
        self.rename_input = QLineEdit()
        self.rename_input.setPlaceholderText("Select a file above, then change its display name in the ISO")
        rename_row.addWidget(self.rename_input, 1)
        self.rename_btn = QPushButton("✏️ Rename")
        self.rename_btn.clicked.connect(self.rename_selected)
        rename_row.addWidget(self.rename_btn)
        files_layout.addLayout(rename_row)

        files_group.setLayout(files_layout)
        content_layout.addWidget(files_group)

        # --- ISO Settings ---
        settings_group = QGroupBox("ISO Settings")
        settings_layout = QVBoxLayout()

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volume Label:"))
        self.volume_input = QLineEdit()
        self.volume_input.setPlaceholderText("Disk name shown after mounting")
        self.volume_input.setText("DOCUMENTS")
        vol_row.addWidget(self.volume_input, 1)
        settings_layout.addLayout(vol_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output Filename:"))
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("ISO output filename")
        self.output_input.setText("demo.iso")
        out_row.addWidget(self.output_input, 1)
        settings_layout.addLayout(out_row)

        settings_group.setLayout(settings_layout)
        content_layout.addWidget(settings_group)

        # --- Attack Chain Guide ---
        guide_group = QGroupBox("Attack Chain Guide")
        guide_layout = QVBoxLayout()
        guide_text = QLabel(
            "Recommended attack chain:\n"
            "1. Use the LNK module to generate a disguised shortcut\n"
            "2. Add LNK + Payload + decoy document to the file list\n"
            "3. Generate the ISO image\n"
            "4. Send the ISO to the target via email or file sharing\n"
            "5. Target double-clicks ISO -> auto-mount -> sees LNK (disguised as document) -> double-clicks to execute\n\n"
            "⚠️ Files inside ISO do not carry MOTW, bypassing:\n"
            "   • Windows SmartScreen\n"
            "   • Office macro auto-disable policies\n"
            "   • Some EDR file-origin detection"
        )
        guide_text.setObjectName("subtitleLabel")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        guide_group.setLayout(guide_layout)
        content_layout.addWidget(guide_group)

        # --- Output Preview ---
        preview_group = QGroupBox("Output")
        preview_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(150)
        self.output_text.setPlaceholderText("Generated output info will appear here...")
        self.output_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        preview_layout.addWidget(self.output_text)
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # --- Bottom Bar ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 Generate ISO Image")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(160)
        self.generate_btn.clicked.connect(self.generate)
        bottom_layout.addWidget(self.generate_btn)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)

        main_layout.addWidget(bottom_bar)

    def add_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select files to pack", "", "All Files (*.*)"
        )
        for path in file_paths:
            name = os.path.basename(path)
            self.files_to_pack.append({
                "source_path": path,
                "name_in_iso": name
            })
            self.file_list.addItem(f"{name}  ←  {path}")

    def add_lnk_from_outputs(self):
        outputs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"
        )
        if not os.path.exists(outputs_dir):
            QMessageBox.warning(self, "Notice", "outputs directory does not exist")
            return

        lnk_files = [f for f in os.listdir(outputs_dir) if f.endswith('.lnk')]
        if not lnk_files:
            QMessageBox.warning(self, "Notice", "No LNK files found in outputs directory")
            return

        for lnk in lnk_files:
            full_path = os.path.join(outputs_dir, lnk)
            self.files_to_pack.append({
                "source_path": full_path,
                "name_in_iso": lnk
            })
            self.file_list.addItem(f"{lnk}  ←  {full_path}")

    def remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            self.file_list.takeItem(row)
            self.files_to_pack.pop(row)

    def clear_files(self):
        self.file_list.clear()
        self.files_to_pack.clear()

    def rename_selected(self):
        row = self.file_list.currentRow()
        new_name = self.rename_input.text().strip()
        if row >= 0 and new_name:
            self.files_to_pack[row]["name_in_iso"] = new_name
            source = self.files_to_pack[row]["source_path"]
            self.file_list.item(row).setText(f"{new_name}  ←  {source}")
            self.rename_input.clear()

    def generate(self):
        if not self.files_to_pack:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ Please add files to pack first")
            return

        volume = self.volume_input.text().strip() or "DOCUMENTS"
        output_fn = self.output_input.text().strip() or "demo.iso"
        if not output_fn.endswith(('.iso', '.img')):
            output_fn += ".iso"

        success, message = generate_iso(self.files_to_pack, volume, output_fn)

        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText("✅ ISO generated successfully")
            self.output_text.setText(message)
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText(f"❌ {message}")
            self.output_text.setText(message)
