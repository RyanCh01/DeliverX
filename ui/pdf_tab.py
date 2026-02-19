import os
import webbrowser
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QTextEdit, QScrollArea, QFrame, QPlainTextEdit
)
from PySide2.QtCore import Qt
from generators.pdf_generator import generate_pdf, get_template_list


class PDFTab(QWidget):
    def __init__(self):
        super().__init__()
        self.generated_pdf_path = None
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
        title = QLabel("PDF 钓鱼文件生成器")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "生成包含全屏透明链接的 PDF 文件。用户打开 PDF 后点击任意位置跳转至目标 URL。"
            "支持预置诱导模板和自定义内容。"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- 基本配置 ---
        basic_group = QGroupBox("基本配置")
        basic_layout = QVBoxLayout()

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("目标 URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("用户点击后跳转的地址，如 https://attacker.com/login")
        url_row.addWidget(self.url_input, 1)
        basic_layout.addLayout(url_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("输出文件名:"))
        self.output_input = QLineEdit()
        self.output_input.setText("phishing.pdf")
        output_row.addWidget(self.output_input, 1)
        basic_layout.addLayout(output_row)

        basic_group.setLayout(basic_layout)
        content_layout.addWidget(basic_group)

        # --- 内容模板 ---
        template_group = QGroupBox("PDF 内容模板")
        template_layout = QVBoxLayout()

        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("模板选择:"))
        self.template_selector = QComboBox()
        self.template_selector.addItems(get_template_list())
        self.template_selector.currentIndexChanged.connect(self.on_template_changed)
        template_row.addWidget(self.template_selector, 1)
        template_layout.addLayout(template_row)

        # 模板预览/说明
        self.template_desc = QLabel("")
        self.template_desc.setObjectName("subtitleLabel")
        self.template_desc.setWordWrap(True)
        template_layout.addWidget(self.template_desc)

        # 自定义标题（仅自定义模式显示）
        self.custom_title_row = QWidget()
        ct_layout = QHBoxLayout(self.custom_title_row)
        ct_layout.setContentsMargins(0, 0, 0, 0)
        ct_layout.addWidget(QLabel("自定义标题:"))
        self.custom_title_input = QLineEdit()
        self.custom_title_input.setPlaceholderText("PDF 文档内显示的标题")
        ct_layout.addWidget(self.custom_title_input, 1)
        template_layout.addWidget(self.custom_title_row)

        # 自定义正文（仅自定义模式显示）
        self.custom_body_row = QWidget()
        cb_layout = QVBoxLayout(self.custom_body_row)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addWidget(QLabel("自定义正文内容（每行一段）:"))
        self.custom_body_input = QPlainTextEdit()
        self.custom_body_input.setMaximumHeight(150)
        self.custom_body_input.setPlaceholderText(
            "在这里输入 PDF 中显示的文字内容...\n"
            "每行将作为 PDF 中的一行文字显示\n"
            "可以写多行"
        )
        cb_layout.addWidget(self.custom_body_input)
        template_layout.addWidget(self.custom_body_row)

        template_group.setLayout(template_layout)
        content_layout.addWidget(template_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # --- 底部 ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 生成 PDF")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(160)
        self.generate_btn.clicked.connect(self.generate)
        bottom_layout.addWidget(self.generate_btn)

        self.preview_btn = QPushButton("🌐 打开 PDF")
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.clicked.connect(self.open_pdf)
        bottom_layout.addWidget(self.preview_btn)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)

        main_layout.addWidget(bottom_bar)

        # 初始化
        self.on_template_changed(0)

    def on_template_changed(self, index):
        descs = [
            "伪装为企业安全验证通知，提示用户账户需要身份验证，\n诱导用户点击链接进行「验证」。",
            "伪装为文件预览失败提示，告知用户 PDF 无法显示，\n诱导用户点击链接在「在线查看器」中查看。",
            "自定义 PDF 标题和正文内容。",
        ]
        self.template_desc.setText(descs[index] if index < len(descs) else "")

        is_custom = (index == 2)
        self.custom_title_row.setVisible(is_custom)
        self.custom_body_row.setVisible(is_custom)

    def generate(self):
        url = self.url_input.text().strip()
        output_fn = self.output_input.text().strip() or "phishing.pdf"
        template_index = self.template_selector.currentIndex()

        if not url:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ 请输入目标 URL")
            return

        if template_index == 0:
            template_mode = "template1"
        elif template_index == 1:
            template_mode = "template2"
        else:
            template_mode = "custom"

        custom_title = self.custom_title_input.text().strip()
        custom_body = self.custom_body_input.toPlainText().strip()

        success, message = generate_pdf(
            url=url,
            template_mode=template_mode,
            custom_title=custom_title,
            custom_body=custom_body,
            output_filename=output_fn
        )

        if success:
            self.generated_pdf_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "outputs", output_fn
            )
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText(f"✅ {message}")
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText(f"❌ {message}")

    def open_pdf(self):
        if self.generated_pdf_path and os.path.exists(self.generated_pdf_path):
            webbrowser.open_new_tab(f'file:///{self.generated_pdf_path}')
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText("❌ 请先生成 PDF 文件")
