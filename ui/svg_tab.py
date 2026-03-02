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
        
        subtitle_label = QLabel("Embed payload or redirect logic into SVG images, leveraging browser parsing to trigger actions")
        subtitle_label.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # --- Configuration Section ---
        config_group = QGroupBox("Attack Configuration")
        config_layout = QFormLayout()
        config_layout.setSpacing(12)
        
        # Mode Selector
        self.svg_mode_selector = QComboBox()
        self.svg_mode_selector.addItems([
            "Click Download Mode", 
            "URL Redirect Mode",
            "Auto Redirect Mode",
            "JS Smuggling Mode"
        ])
        self.svg_mode_selector.currentIndexChanged.connect(self.on_mode_changed)
        config_layout.addRow(QLabel("Delivery Mode:"), self.svg_mode_selector)
        
        # Payload File
        self.svg_payload_input = QLineEdit()
        self.svg_payload_input.setPlaceholderText("Click Browse to select the payload file...")
        self.svg_payload_browse_btn = QPushButton("📂 Browse")
        self.svg_payload_browse_btn.setFixedWidth(80)
        self.svg_payload_browse_btn.clicked.connect(self.select_payload_file)
        
        payload_layout = list_to_hbox([self.svg_payload_input, self.svg_payload_browse_btn])
        self.svg_payload_label = QLabel("Payload:")
        config_layout.addRow(self.svg_payload_label, payload_layout)
        
        # Download Filename
        self.svg_download_filename = QLineEdit()
        self.svg_download_filename.setPlaceholderText("e.g. malicious_update.zip")
        self.svg_download_filename_label = QLabel("Save As:")
        config_layout.addRow(self.svg_download_filename_label, self.svg_download_filename)
        
        # Target URL
        self.svg_target_url = QLineEdit()
        self.svg_target_url.setPlaceholderText("e.g. https://attacker.com/login")
        self.svg_target_url_label = QLabel("Target URL:")
        config_layout.addRow(self.svg_target_url_label, self.svg_target_url)

        # Encoding Selector
        self.svg_encoding_selector = QComboBox()
        self.svg_encoding_selector.addItems([
            "Standard Base64", 
            "Reverse + Base64", 
            "XOR + Base64", 
            "Chunked Shuffle + Base64"
        ])
        self.svg_encoding_label = QLabel("Encoding:")
        config_layout.addRow(self.svg_encoding_label, self.svg_encoding_selector)

        # Evasion Checkbox
        self.svg_evasion_checkbox = QCheckBox("Enable Keyword Evasion")
        self.svg_evasion_checkbox.setToolTip("Obfuscate sensitive JavaScript keywords to evade static detection")
        self.svg_evasion_label = QLabel("Evasion:")
        config_layout.addRow("", self.svg_evasion_checkbox)

        # Decoy Template Selector (JS Smuggling only)
        self.svg_decoy_selector = QComboBox()
        self.svg_decoy_selector.addItems([
            "Document Viewer",
            "Secure Transfer"
        ])
        self.svg_decoy_label = QLabel("Decoy Template:")
        config_layout.addRow(self.svg_decoy_label, self.svg_decoy_selector)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # --- Appearance Section ---
        appearance_group = QGroupBox("Decoy Settings")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(12)
        
        # Bait Image
        self.svg_image_input = QLineEdit()
        self.svg_image_input.setPlaceholderText("Leave empty for default gray placeholder...")
        self.svg_image_browse_btn = QPushButton("📂 Browse")
        self.svg_image_browse_btn.setFixedWidth(80)
        self.svg_image_browse_btn.clicked.connect(self.select_image_file)
        
        image_layout = list_to_hbox([self.svg_image_input, self.svg_image_browse_btn])
        self.svg_image_label = QLabel("Bait Image:")
        appearance_layout.addRow(self.svg_image_label, image_layout)
        
        # Click Text
        self.svg_click_text = QLineEdit()
        self.svg_click_text.setText("Scan complete. Click to download")
        self.svg_click_text_label = QLabel("Click Text:")
        appearance_layout.addRow(self.svg_click_text_label, self.svg_click_text)
        
        appearance_group.setLayout(appearance_layout)
        self.appearance_group = appearance_group 
        layout.addWidget(appearance_group)

        # --- Packaging Section ---
        packaging_group = QGroupBox("Output Packaging")
        packaging_layout = QFormLayout()
        packaging_layout.setSpacing(12)
        
        self.svg_package_selector = QComboBox()
        self.svg_package_selector.addItems(["None", "ZIP Archive", "Password-Protected ZIP"])
        self.svg_package_selector.currentIndexChanged.connect(self.on_package_changed)
        packaging_layout.addRow(QLabel("Format:"), self.svg_package_selector)
        
        self.svg_zip_password = QLineEdit()
        self.svg_zip_password.setEchoMode(QLineEdit.Password)
        self.svg_zip_password.setPlaceholderText("Enter password...")
        self.svg_zip_password_label = QLabel("Password:")
        packaging_layout.addRow(self.svg_zip_password_label, self.svg_zip_password)
        
        packaging_group.setLayout(packaging_layout)
        layout.addWidget(packaging_group)
        
        # --- Action Section ---
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        
        self.svg_generate_btn = QPushButton("🚀 Generate SVG File")
        self.svg_generate_btn.setObjectName("primaryButton")
        self.svg_generate_btn.clicked.connect(self.generate_svg)
        btn_layout.addWidget(self.svg_generate_btn)
        
        self.svg_open_btn = QPushButton("🔍 Preview in Browser")
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
        show_appearance = (is_download or index == 1)
        show_advanced = (is_smuggling)
        
        self.svg_payload_label.setVisible(show_payload)
        self.svg_payload_input.setVisible(show_payload)
        self.svg_payload_browse_btn.setVisible(show_payload)
        self.svg_download_filename_label.setVisible(show_payload)
        self.svg_download_filename.setVisible(show_payload)
        
        self.svg_target_url_label.setVisible(show_url)
        self.svg_target_url.setVisible(show_url)
        
        self.svg_encoding_label.setVisible(show_advanced)
        self.svg_encoding_selector.setVisible(show_advanced)
        self.svg_evasion_checkbox.setVisible(show_advanced)
        self.svg_decoy_label.setVisible(show_advanced)
        self.svg_decoy_selector.setVisible(show_advanced)
        
        self.appearance_group.setVisible(show_appearance)
    
    def on_package_changed(self, index):
        mode = self.svg_package_selector.currentText()
        is_password = "Password" in mode
        
        self.svg_zip_password_label.setVisible(is_password)
        self.svg_zip_password.setVisible(is_password)

    def select_payload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Payload File", "", "All Files (*)")
        if path:
            self.svg_payload_input.setText(path)

    def select_image_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Bait Image", "", "Images (*.jpg *.jpeg *.png *.gif *.bmp);;All Files (*)")
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
        
        if "Click Download" in mode:
            params['payload_path'] = self.svg_payload_input.text().strip()
            params['download_filename'] = self.svg_download_filename.text().strip()
            if not params['payload_path']:
                self.show_error("Please select a payload file")
                return
        
        elif "URL Redirect" in mode or "Auto Redirect" in mode:
             params['target_url'] = self.svg_target_url.text().strip()
             if not params['target_url']:
                self.show_error("Please enter a target URL")
                return

        elif "JS" in mode or "Smuggling" in mode:
             params['payload_path'] = self.svg_payload_input.text().strip()
             params['download_filename'] = self.svg_download_filename.text().strip()
             params['encoding_method'] = self.svg_encoding_selector.currentText()
             params['enable_evasion'] = self.svg_evasion_checkbox.isChecked()
             decoy_idx = self.svg_decoy_selector.currentIndex()
             params['decoy_mode'] = 'template2' if decoy_idx == 1 else 'template1'
             
             if not params['payload_path']:
                self.show_error("Please select a payload file")
                return

        try:
            self.svg_status.setText("Status: Generating...")
            self.svg_status.setStyleSheet("color: #a0a0a0;")
            QApplication.processEvents()

            default_filename = os.path.join("outputs", "svg_smuggling.svg")
            save_path, _ = QFileDialog.getSaveFileName(self, "Save SVG File", default_filename, "SVG Files (*.svg);;All Files (*)")
            
            if not save_path:
                self.svg_status.setText("Status: Cancelled")
                return

            abs_path = self.generator.generate(mode, params, save_path)
            final_msg = f"✅ SVG generated: {abs_path}"

            # Packaging Logic
            if "None" not in package_mode:
                if "Password" in package_mode and not zip_password:
                     raise ValueError("Packaging password is required.")
                
                svg_name = os.path.basename(abs_path)
                zip_name = os.path.splitext(svg_name)[0] + ".zip"
                
                zip_pwd = zip_password if "Password" in package_mode else None
                zip_path = package_as_zip([abs_path], zip_name, password=zip_pwd)
                
                final_msg += f"\n📦 Packed in ZIP: {zip_path}"
                
            self.svg_status.setObjectName("statusSuccess")
            self.svg_status.setText(final_msg)
            self.svg_status.setStyleSheet("color: #00b894; font-weight: bold;")
            
            self.svg_open_btn.setEnabled(True)
            self.generated_svg_path = abs_path
            
            if self.window():
                self.window().statusBar().showMessage(f"Generated: {abs_path}")

        except Exception as e:
             self.show_error(f"Generation/packaging failed: {str(e)}")

    def show_error(self, message):
        self.svg_status.setObjectName("statusError")
        self.svg_status.setText(f"❌ {message}")
        self.svg_status.setStyleSheet("color: #e94560; font-weight: bold;")

    def open_in_browser(self):
        if self.generated_svg_path and os.path.exists(self.generated_svg_path):
            try:
                webbrowser.open_new_tab(f"file://{self.generated_svg_path}")
            except Exception as e:
                self.show_error(f"Failed to open preview: {str(e)}")
        else:
            self.show_error("File not found")

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
