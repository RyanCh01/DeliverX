import os
import datetime
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QFileDialog, QTextEdit, QScrollArea, QFrame,
    QDateTimeEdit, QCheckBox, QTabWidget
)
from PySide2.QtCore import Qt, QDateTime
from generators.file_spoofer import (
    modify_timestamps, clone_timestamps, get_file_timestamps,
    modify_pe_info, get_pe_info,
    get_preset_names, get_preset_info
)


class FileSpoofTab(QWidget):
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

        # 标题
        title = QLabel("文件属性伪造工具")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "修改文件的时间戳和 EXE 版本信息属性，让恶意文件在取证分析中看起来像正常的系统文件或常用软件。"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # 使用内部 Tab 分两个功能区
        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2d2d4e; border-radius: 6px; background-color: transparent; }
            QTabBar::tab { padding: 8px 20px; }
        """)

        # ===== Tab1：时间戳修改 =====
        timestamp_widget = QWidget()
        ts_layout = QVBoxLayout(timestamp_widget)
        ts_layout.setContentsMargins(12, 12, 12, 12)
        ts_layout.setSpacing(10)

        # 目标文件
        ts_file_group = QGroupBox("目标文件")
        ts_file_layout = QVBoxLayout()

        ts_file_row = QHBoxLayout()
        ts_file_row.addWidget(QLabel("文件路径:"))
        self.ts_file_input = QLineEdit()
        self.ts_file_input.setPlaceholderText("选择要修改时间戳的文件")
        ts_file_row.addWidget(self.ts_file_input, 1)
        self.ts_file_btn = QPushButton("浏览")
        self.ts_file_btn.clicked.connect(self.select_ts_file)
        ts_file_row.addWidget(self.ts_file_btn)
        ts_file_layout.addLayout(ts_file_row)

        # 读取当前时间按钮
        self.ts_read_btn = QPushButton("📖 读取当前文件时间戳")
        self.ts_read_btn.clicked.connect(self.read_timestamps)
        ts_file_layout.addWidget(self.ts_read_btn)

        # 当前时间戳显示
        self.ts_current_label = QLabel("")
        self.ts_current_label.setObjectName("subtitleLabel")
        self.ts_current_label.setWordWrap(True)
        ts_file_layout.addWidget(self.ts_current_label)

        ts_file_group.setLayout(ts_file_layout)
        ts_layout.addWidget(ts_file_group)

        # 修改模式
        ts_mode_group = QGroupBox("修改方式")
        ts_mode_layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("模式:"))
        self.ts_mode_selector = QComboBox()
        self.ts_mode_selector.addItems([
            "手动指定时间",
            "从其他文件克隆时间戳",
            "随机生成合理时间",
        ])
        self.ts_mode_selector.currentIndexChanged.connect(self.on_ts_mode_changed)
        mode_row.addWidget(self.ts_mode_selector, 1)
        ts_mode_layout.addLayout(mode_row)

        # 手动时间设置区
        self.ts_manual_widget = QWidget()
        manual_layout = QVBoxLayout(self.ts_manual_widget)
        manual_layout.setContentsMargins(0, 8, 0, 0)

        # 创建时间
        self.ts_created_check = QCheckBox("修改创建时间（仅Windows）")
        self.ts_created_check.setChecked(True)
        manual_layout.addWidget(self.ts_created_check)

        created_row = QHBoxLayout()
        created_row.addWidget(QLabel("  创建时间:"))
        self.ts_created_input = QDateTimeEdit()
        self.ts_created_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_created_input.setDateTime(QDateTime(2023, 6, 15, 9, 30, 0))
        self.ts_created_input.setCalendarPopup(True)
        created_row.addWidget(self.ts_created_input, 1)
        manual_layout.addLayout(created_row)

        # 修改时间
        self.ts_modified_check = QCheckBox("修改修改时间")
        self.ts_modified_check.setChecked(True)
        manual_layout.addWidget(self.ts_modified_check)

        modified_row = QHBoxLayout()
        modified_row.addWidget(QLabel("  修改时间:"))
        self.ts_modified_input = QDateTimeEdit()
        self.ts_modified_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_modified_input.setDateTime(QDateTime(2023, 6, 15, 14, 22, 0))
        self.ts_modified_input.setCalendarPopup(True)
        modified_row.addWidget(self.ts_modified_input, 1)
        manual_layout.addLayout(modified_row)

        # 访问时间
        self.ts_accessed_check = QCheckBox("修改访问时间")
        self.ts_accessed_check.setChecked(True)
        manual_layout.addWidget(self.ts_accessed_check)

        accessed_row = QHBoxLayout()
        accessed_row.addWidget(QLabel("  访问时间:"))
        self.ts_accessed_input = QDateTimeEdit()
        self.ts_accessed_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_accessed_input.setDateTime(QDateTime(2023, 12, 20, 10, 5, 0))
        self.ts_accessed_input.setCalendarPopup(True)
        accessed_row.addWidget(self.ts_accessed_input, 1)
        manual_layout.addLayout(accessed_row)

        ts_mode_layout.addWidget(self.ts_manual_widget)

        # 克隆源文件
        self.ts_clone_widget = QWidget()
        clone_layout = QHBoxLayout(self.ts_clone_widget)
        clone_layout.setContentsMargins(0, 8, 0, 0)
        clone_layout.addWidget(QLabel("源文件:"))
        self.ts_clone_input = QLineEdit()
        self.ts_clone_input.setPlaceholderText("选择要克隆时间戳的源文件")
        clone_layout.addWidget(self.ts_clone_input, 1)
        self.ts_clone_btn = QPushButton("浏览")
        self.ts_clone_btn.clicked.connect(self.select_clone_source)
        clone_layout.addWidget(self.ts_clone_btn)
        ts_mode_layout.addWidget(self.ts_clone_widget)

        # 随机时间范围
        self.ts_random_widget = QWidget()
        random_layout = QVBoxLayout(self.ts_random_widget)
        random_layout.setContentsMargins(0, 8, 0, 0)

        range_start_row = QHBoxLayout()
        range_start_row.addWidget(QLabel("起始日期:"))
        self.ts_range_start = QDateTimeEdit()
        self.ts_range_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_range_start.setDateTime(QDateTime(2022, 1, 1, 8, 0, 0))
        self.ts_range_start.setCalendarPopup(True)
        range_start_row.addWidget(self.ts_range_start, 1)
        random_layout.addLayout(range_start_row)

        range_end_row = QHBoxLayout()
        range_end_row.addWidget(QLabel("结束日期:"))
        self.ts_range_end = QDateTimeEdit()
        self.ts_range_end.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_range_end.setDateTime(QDateTime(2023, 12, 31, 18, 0, 0))
        self.ts_range_end.setCalendarPopup(True)
        range_end_row.addWidget(self.ts_range_end, 1)
        random_layout.addLayout(range_end_row)

        random_hint = QLabel("将在指定范围内随机生成合理的创建/修改/访问时间（创建<修改<访问）")
        random_hint.setObjectName("subtitleLabel")
        random_hint.setWordWrap(True)
        random_layout.addWidget(random_hint)

        ts_mode_layout.addWidget(self.ts_random_widget)

        ts_mode_group.setLayout(ts_mode_layout)
        ts_layout.addWidget(ts_mode_group)

        # 时间戳执行按钮
        self.ts_execute_btn = QPushButton("🕐 修改时间戳")
        self.ts_execute_btn.setObjectName("primaryButton")
        self.ts_execute_btn.setMinimumHeight(38)
        self.ts_execute_btn.clicked.connect(self.execute_timestamp)
        ts_layout.addWidget(self.ts_execute_btn)

        ts_layout.addStretch()
        inner_tabs.addTab(timestamp_widget, "🕐 时间戳修改")

        # ===== Tab2：PE属性修改 =====
        pe_widget = QWidget()
        pe_layout = QVBoxLayout(pe_widget)
        pe_layout.setContentsMargins(12, 12, 12, 12)
        pe_layout.setSpacing(10)

        # PE文件选择
        pe_file_group = QGroupBox("EXE/DLL 文件")
        pe_file_layout = QVBoxLayout()

        pe_file_row = QHBoxLayout()
        pe_file_row.addWidget(QLabel("文件路径:"))
        self.pe_file_input = QLineEdit()
        self.pe_file_input.setPlaceholderText("选择要修改属性的 EXE 或 DLL 文件")
        pe_file_row.addWidget(self.pe_file_input, 1)
        self.pe_file_btn = QPushButton("浏览")
        self.pe_file_btn.clicked.connect(self.select_pe_file)
        pe_file_row.addWidget(self.pe_file_btn)
        pe_file_layout.addLayout(pe_file_row)

        self.pe_read_btn = QPushButton("📖 读取当前文件属性")
        self.pe_read_btn.clicked.connect(self.read_pe_info)
        pe_file_layout.addWidget(self.pe_read_btn)

        self.pe_current_label = QLabel("")
        self.pe_current_label.setObjectName("subtitleLabel")
        self.pe_current_label.setWordWrap(True)
        pe_file_layout.addWidget(self.pe_current_label)

        pe_file_group.setLayout(pe_file_layout)
        pe_layout.addWidget(pe_file_group)

        # 预置方案
        preset_group = QGroupBox("伪装方案")
        preset_layout = QVBoxLayout()

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预置方案:"))
        self.preset_selector = QComboBox()
        self.preset_selector.addItem("-- 自定义 --")
        self.preset_selector.addItems(get_preset_names())
        self.preset_selector.currentIndexChanged.connect(self.on_preset_changed)
        preset_row.addWidget(self.preset_selector, 1)
        preset_layout.addLayout(preset_row)

        preset_group.setLayout(preset_layout)
        pe_layout.addWidget(preset_group)

        # 属性输入
        attr_group = QGroupBox("文件属性")
        attr_layout = QVBoxLayout()

        fields = [
            ("产品名称:", "pe_product_input", "如：Microsoft Office Word"),
            ("公司名称:", "pe_company_input", "如：Microsoft Corporation"),
            ("文件描述:", "pe_desc_input", "如：Microsoft Word"),
            ("文件版本:", "pe_version_input", "如：16.0.14326.20404"),
            ("原始文件名:", "pe_origname_input", "如：WINWORD.EXE"),
            ("内部名称:", "pe_internal_input", "如：WinWord"),
            ("版权信息:", "pe_copyright_input", "如：© Microsoft Corporation."),
        ]

        for label_text, attr_name, placeholder in fields:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            setattr(self, attr_name, line_edit)
            row.addWidget(line_edit, 1)
            attr_layout.addLayout(row)

        attr_group.setLayout(attr_layout)
        pe_layout.addWidget(attr_group)

        # 输出设置
        pe_out_group = QGroupBox("输出设置")
        pe_out_layout = QVBoxLayout()

        self.pe_overwrite_check = QCheckBox("覆盖原文件（不勾选则输出到 outputs/ 目录）")
        self.pe_overwrite_check.setChecked(False)
        pe_out_layout.addWidget(self.pe_overwrite_check)

        pe_outname_row = QHBoxLayout()
        pe_outname_row.addWidget(QLabel("输出文件名:"))
        self.pe_outname_input = QLineEdit()
        self.pe_outname_input.setPlaceholderText("修改后的 EXE 文件名")
        self.pe_outname_input.setText("spoofed.exe")
        pe_outname_row.addWidget(self.pe_outname_input, 1)
        pe_out_layout.addLayout(pe_outname_row)

        pe_out_group.setLayout(pe_out_layout)
        pe_layout.addWidget(pe_out_group)

        # PE执行按钮
        self.pe_execute_btn = QPushButton("🔧 修改文件属性")
        self.pe_execute_btn.setObjectName("primaryButton")
        self.pe_execute_btn.setMinimumHeight(38)
        self.pe_execute_btn.clicked.connect(self.execute_pe_modify)
        pe_layout.addWidget(self.pe_execute_btn)

        pe_layout.addStretch()
        inner_tabs.addTab(pe_widget, "🔧 PE属性伪造")

        content_layout.addWidget(inner_tabs)

        # 输出信息
        output_group = QGroupBox("输出信息")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(180)
        self.output_text.setStyleSheet(
            "font-family: 'Consolas','JetBrains Mono',monospace; font-size: 12px;"
        )
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        content_layout.addWidget(output_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 底部状态栏
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)
        bottom_layout.addStretch()
        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)
        main_layout.addWidget(bottom_bar)

        # 初始化显隐
        self.on_ts_mode_changed(0)

    # ============ 时间戳功能 ============

    def select_ts_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*.*)")
        if path:
            self.ts_file_input.setText(path)
            self.read_timestamps()

    def select_clone_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择源文件", "", "所有文件 (*.*)")
        if path:
            self.ts_clone_input.setText(path)

    def on_ts_mode_changed(self, index):
        self.ts_manual_widget.setVisible(index == 0)
        self.ts_clone_widget.setVisible(index == 1)
        self.ts_random_widget.setVisible(index == 2)

    def read_timestamps(self):
        path = self.ts_file_input.text().strip()
        if not path:
            return
        success, info = get_file_timestamps(path)
        if success:
            text = (
                f"文件: {info['name']}  ({info['size']/1024:.1f} KB)\n"
                f"创建时间: {info['created'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"修改时间: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"访问时间: {info['accessed'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.ts_current_label.setText(text)
        else:
            self.ts_current_label.setText(f"读取失败: {info}")

    def execute_timestamp(self):
        path = self.ts_file_input.text().strip()
        if not path:
            self._set_status("❌ 请选择目标文件", False)
            return

        mode = self.ts_mode_selector.currentIndex()

        if mode == 0:
            # 手动指定
            created = self.ts_created_input.dateTime().toPython() if self.ts_created_check.isChecked() else None
            modified = self.ts_modified_input.dateTime().toPython() if self.ts_modified_check.isChecked() else None
            accessed = self.ts_accessed_input.dateTime().toPython() if self.ts_accessed_check.isChecked() else None

            if not any([created, modified, accessed]):
                self._set_status("❌ 请至少勾选一项要修改的时间", False)
                return

            success, message = modify_timestamps(path, created, modified, accessed)

        elif mode == 1:
            # 克隆
            source = self.ts_clone_input.text().strip()
            if not source:
                self._set_status("❌ 请选择源文件", False)
                return
            success, message = clone_timestamps(source, path)

        elif mode == 2:
            # 随机
            import random
            start_dt = self.ts_range_start.dateTime().toPython()
            end_dt = self.ts_range_end.dateTime().toPython()

            if start_dt >= end_dt:
                self._set_status("❌ 起始日期必须早于结束日期", False)
                return

            total_seconds = int((end_dt - start_dt).total_seconds())
            rand1 = random.randint(0, total_seconds // 3)
            rand2 = random.randint(total_seconds // 3, total_seconds * 2 // 3)
            rand3 = random.randint(total_seconds * 2 // 3, total_seconds)

            created = start_dt + datetime.timedelta(seconds=rand1)
            modified = start_dt + datetime.timedelta(seconds=rand2)
            accessed = start_dt + datetime.timedelta(seconds=rand3)

            success, message = modify_timestamps(path, created, modified, accessed)
        else:
            return

        self.output_text.setText(message)
        self._set_status("✅ 时间戳修改完成" if success else "❌ 修改失败", success)

        if success:
            self.read_timestamps()

    # ============ PE属性功能 ============

    def select_pe_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 EXE/DLL 文件", "",
            "可执行文件 (*.exe *.dll);;所有文件 (*.*)"
        )
        if path:
            self.pe_file_input.setText(path)

    def read_pe_info(self):
        path = self.pe_file_input.text().strip()
        if not path:
            return
        success, info = get_pe_info(path)
        if success:
            lines = [f"{k}: {v}" for k, v in info.items()]
            self.pe_current_label.setText('\n'.join(lines))
        else:
            self.pe_current_label.setText(str(info))

    def on_preset_changed(self, index):
        if index == 0:
            # 自定义，清空
            return
        preset_name = self.preset_selector.currentText()
        info = get_preset_info(preset_name)
        if info:
            self.pe_product_input.setText(info.get("product_name", ""))
            self.pe_company_input.setText(info.get("company_name", ""))
            self.pe_desc_input.setText(info.get("file_description", ""))
            self.pe_version_input.setText(info.get("file_version", ""))
            self.pe_origname_input.setText(info.get("original_filename", ""))
            self.pe_internal_input.setText(info.get("internal_name", ""))
            self.pe_copyright_input.setText(info.get("copyright_info", ""))

    def execute_pe_modify(self):
        path = self.pe_file_input.text().strip()
        if not path:
            self._set_status("❌ 请选择 EXE/DLL 文件", False)
            return

        overwrite = self.pe_overwrite_check.isChecked()
        if overwrite:
            output_path = None
        else:
            outname = self.pe_outname_input.text().strip() or "spoofed.exe"
            from generators.file_spoofer import OUTPUT_DIR
            output_path = os.path.join(OUTPUT_DIR, outname)

        success, message = modify_pe_info(
            file_path=path,
            output_path=output_path,
            product_name=self.pe_product_input.text().strip() or None,
            company_name=self.pe_company_input.text().strip() or None,
            file_description=self.pe_desc_input.text().strip() or None,
            file_version=self.pe_version_input.text().strip() or None,
            original_filename=self.pe_origname_input.text().strip() or None,
            internal_name=self.pe_internal_input.text().strip() or None,
            copyright_info=self.pe_copyright_input.text().strip() or None,
        )

        self.output_text.setText(message)
        self._set_status("✅ 属性修改完成" if success else "❌ 修改失败", success)

    # ============ 通用 ============

    def _set_status(self, text, success):
        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
        self.status_label.setText(text)
