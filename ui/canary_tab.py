import os
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QTextEdit, QScrollArea, QFrame
)
from PySide2.QtCore import Qt
from generators.canary_generator import (
    generate_url_canary, generate_dns_canary,
    get_canary_types
)


class CanaryTab(QWidget):
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

        title = QLabel("Canary Token 蜜标生成器")
        title.setObjectName("titleLabel")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "生成追踪蜜标文件。目标打开文件即触发回调通知，"
            "用于确认钓鱼邮件是否被打开。"
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # --- 蜜标类型 ---
        type_group = QGroupBox("蜜标类型")
        type_layout = QVBoxLayout()

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("类型:"))
        self.type_selector = QComboBox()
        self.type_selector.addItems(get_canary_types())
        self.type_selector.currentIndexChanged.connect(self.on_type_changed)
        type_row.addWidget(self.type_selector, 1)
        type_layout.addLayout(type_row)

        self.type_desc = QLabel("")
        self.type_desc.setObjectName("subtitleLabel")
        self.type_desc.setWordWrap(True)
        type_layout.addWidget(self.type_desc)

        type_group.setLayout(type_layout)
        content_layout.addWidget(type_group)

        # --- 配置区 ---
        config_group = QGroupBox("配置")
        config_layout = QVBoxLayout()

        # 回调URL
        self.url_row = QWidget()
        url_layout = QHBoxLayout(self.url_row)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.addWidget(QLabel("回调 URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("你的监听服务器地址，如 https://your-server.com/track")
        url_layout.addWidget(self.url_input, 1)
        config_layout.addWidget(self.url_row)

        # DNS域名（仅DNS模式）
        self.dns_row = QWidget()
        dns_layout = QHBoxLayout(self.dns_row)
        dns_layout.setContentsMargins(0, 0, 0, 0)
        dns_layout.addWidget(QLabel("DNS 域名:"))
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("你控制的域名，如 canary.yourdomain.com")
        dns_layout.addWidget(self.dns_input, 1)
        config_layout.addWidget(self.dns_row)

        # 标识符（DNS模式）
        self.id_row = QWidget()
        id_layout = QHBoxLayout(self.id_row)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.addWidget(QLabel("目标标识:"))
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("用于区分不同目标的标识符，如 target1")
        self.id_input.setText("target1")
        id_layout.addWidget(self.id_input, 1)
        config_layout.addWidget(self.id_row)

        # 输出文件名
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出文件名:"))
        self.output_input = QLineEdit()
        self.output_input.setText("canary_pixel.html")
        out_row.addWidget(self.output_input, 1)
        config_layout.addLayout(out_row)

        config_group.setLayout(config_layout)
        content_layout.addWidget(config_group)

        # --- 输出 ---
        output_group = QGroupBox("输出信息")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(250)
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

        self.generate_btn = QPushButton("🚀 生成蜜标")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(160)
        self.generate_btn.clicked.connect(self.generate)
        bottom_layout.addWidget(self.generate_btn)

        bottom_layout.addStretch()
        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)
        main_layout.addWidget(bottom_bar)

        self.on_type_changed(0)

    def on_type_changed(self, index):
        descs = [
            "生成 1x1 透明追踪像素。嵌入邮件 HTML 正文中，\n邮件被打开时自动加载图片触发回调。",
            "利用 DNS 查询追踪。即使 HTTP 被防火墙拦截，\nDNS 查询通常不受限制。",
        ]
        self.type_desc.setText(descs[index] if index < len(descs) else "")

        is_dns = (index == 1)
        self.dns_row.setVisible(is_dns)
        self.id_row.setVisible(is_dns)
        self.url_row.setVisible(True)

        default_names = ["canary_pixel.html", "canary_dns.html"]
        self.output_input.setText(default_names[index] if index < len(default_names) else "canary.txt")

    def generate(self):
        index = self.type_selector.currentIndex()
        output_fn = self.output_input.text().strip()

        if index == 0:
            url = self.url_input.text().strip()
            if not url:
                self._show_error("请输入回调 URL")
                return
            success, message = generate_url_canary(url, output_fn)
        elif index == 1:
            dns = self.dns_input.text().strip()
            identifier = self.id_input.text().strip() or "target1"
            if not dns:
                self._show_error("请输入 DNS 域名")
                return
            success, message = generate_dns_canary(dns, identifier, output_fn)
        else:
            success, message = False, "未知类型"

        if success:
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
            self.status_label.setText("✅ 生成成功")
            self.output_text.setText(message)
        else:
            self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.status_label.setText(f"❌ {message}")
            self.output_text.setText(message)

    def _show_error(self, msg):
        self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
        self.status_label.setText(f"❌ {msg}")
