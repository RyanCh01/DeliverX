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

        # Title
        title = QLabel("PDF Phishing Generator")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Generate PDF files with a full-page transparent link overlay. "
            "Clicking anywhere on the PDF redirects the target to a specified URL. "
            "Supports preset decoy templates and custom content."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- Basic Configuration ---
        basic_group = QGroupBox("Basic Configuration")
        basic_layout = QVBoxLayout()

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Target URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Redirect URL after click, e.g. https://attacker.com/login")
        url_row.addWidget(self.url_input, 1)
        basic_layout.addLayout(url_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output Filename:"))
        self.output_input = QLineEdit()
        self.output_input.setText("phishing.pdf")
        output_row.addWidget(self.output_input, 1)
        basic_layout.addLayout(output_row)

        basic_group.setLayout(basic_layout)
        content_layout.addWidget(basic_group)

        # --- Content Template ---
        template_group = QGroupBox("PDF Content Template")
        template_layout = QVBoxLayout()

        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Template:"))
        self.template_selector = QComboBox()
        self.template_selector.addItems(get_template_list())
        self.template_selector.currentIndexChanged.connect(self.on_template_changed)
        template_row.addWidget(self.template_selector, 1)
        template_layout.addLayout(template_row)

        # Template preview/description
        self.template_desc = QLabel("")
        self.template_desc.setObjectName("subtitleLabel")
        self.template_desc.setWordWrap(True)
        template_layout.addWidget(self.template_desc)

        # Custom title (shown only in custom mode)
        self.custom_title_row = QWidget()
        ct_layout = QHBoxLayout(self.custom_title_row)
        ct_layout.setContentsMargins(0, 0, 0, 0)
        ct_layout.addWidget(QLabel("Custom Title:"))
        self.custom_title_input = QLineEdit()
        self.custom_title_input.setPlaceholderText("Title displayed in the PDF document")
        ct_layout.addWidget(self.custom_title_input, 1)
        template_layout.addWidget(self.custom_title_row)

        # Custom body (shown only in custom mode)
        self.custom_body_row = QWidget()
        cb_layout = QVBoxLayout(self.custom_body_row)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addWidget(QLabel("Custom Body (one paragraph per line):"))
        self.custom_body_input = QPlainTextEdit()
        self.custom_body_input.setMaximumHeight(150)
        self.custom_body_input.setPlaceholderText(
            "Enter the text content to display in the PDF...\n"
            "Each line will be rendered as a separate line in the PDF\n"
            "Multiple lines supported"
        )
        cb_layout.addWidget(self.custom_body_input)
        template_layout.addWidget(self.custom_body_row)

        template_group.setLayout(template_layout)
        content_layout.addWidget(template_group)

        content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # --- Bottom Bar ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        self.generate_btn = QPushButton("🚀 Generate PDF")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(160)
        self.generate_btn.clicked.connect(self.generate)
        bottom_layout.addWidget(self.generate_btn)

        self.preview_btn = QPushButton("🌐 Open PDF")
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.clicked.connect(self.open_pdf)
        bottom_layout.addWidget(self.preview_btn)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)

        main_layout.addWidget(bottom_bar)

        # Initialize
        self.on_template_changed(0)

    def on_template_changed(self, index):
        descs = [
            "Disguised as a corporate security verification notice, prompting the user\nto verify their account by clicking the link.",
            "Disguised as a failed file preview, telling the user the PDF cannot display\nand luring them to click to open an \"online viewer\".",
            "Custom PDF title and body content.",
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
            self.status_label.setText("❌ Please enter a target URL")
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
            self.status_label.setText("❌ Please generate a PDF first")
