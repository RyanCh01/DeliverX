import os
import webbrowser
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QGroupBox, 
    QFormLayout, QCheckBox, QFileDialog, QMessageBox, QApplication, QScrollArea
)
from PySide2.QtCore import Qt
from generators.html_generator import HTMLGenerator
from utils.packaging import package_as_zip

class HTMLTab(QWidget):
    def __init__(self):
        super().__init__()
        self.generator = HTMLGenerator()
        self.generated_html_path = None
        self.generated_extra_files = []
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
        title_label = QLabel("HTML Smuggling Generator")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label) 
        subtitle_label = QLabel("Embed any file as Base64-encoded data in HTML to bypass network boundary detection")
        subtitle_label.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

        # --- Configuration Section ---
        config_group = QGroupBox("Attack Configuration")
        config_layout = QFormLayout()
        config_layout.setSpacing(12)
        
        # Mode Selector
        self.htmlsm_mode_selector = QComboBox()
        self.htmlsm_mode_selector.addItems([
            "Auto Download",
            "Click Anywhere to Download"
        ])
        config_layout.addRow(QLabel("Trigger Mode:"), self.htmlsm_mode_selector)
        
        # Encoding Selector
        self.htmlsm_encoding_selector = QComboBox()
        self.htmlsm_encoding_selector.addItems([
            "Standard Base64", 
            "Reverse + Base64", 
            "XOR + Base64", 
            "Chunked Shuffle + Base64"
        ])
        self.htmlsm_encoding_selector.currentIndexChanged.connect(self.on_encoding_changed)
        self.htmlsm_encoding_label = QLabel("Encoding:")
        config_layout.addRow(self.htmlsm_encoding_label, self.htmlsm_encoding_selector)

        # XOR Key Length
        self.htmlsm_key_length = QLineEdit()
        self.htmlsm_key_length.setText("16")
        self.htmlsm_key_length.setPlaceholderText("8-64")
        self.htmlsm_key_length_label = QLabel("Key Length:")
        config_layout.addRow(self.htmlsm_key_length_label, self.htmlsm_key_length)
        
        # Chunk Size
        self.htmlsm_chunk_size = QLineEdit()
        self.htmlsm_chunk_size.setText("4096")
        self.htmlsm_chunk_size.setPlaceholderText("Bytes (e.g. 4096)")
        self.htmlsm_chunk_size_label = QLabel("Chunk Size:")
        config_layout.addRow(self.htmlsm_chunk_size_label, self.htmlsm_chunk_size)

        # File Selection
        self.htmlsm_file_input = QLineEdit()
        self.htmlsm_file_input.setPlaceholderText("Click Browse to select a file...")
        self.htmlsm_browse_btn = QPushButton("📂 Browse")
        self.htmlsm_browse_btn.setFixedWidth(80)
        self.htmlsm_browse_btn.clicked.connect(self.select_file)
        
        file_layout = list_to_hbox([self.htmlsm_file_input, self.htmlsm_browse_btn])
        config_layout.addRow(QLabel("Payload File:"), file_layout)
        
        # Download Filename
        self.htmlsm_output_filename = QLineEdit()
        self.htmlsm_output_filename.setText("malicious.iso")
        self.htmlsm_output_filename.setPlaceholderText("e.g. update.iso")
        config_layout.addRow(QLabel("Save As:"), self.htmlsm_output_filename)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # --- Appearance Section ---
        appearance_group = QGroupBox("Decoy Settings")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(12)

        # Decoy Template Selector
        self.htmlsm_decoy_selector = QComboBox()
        self.htmlsm_decoy_selector.addItems([
            "None",
            "Microsoft 365 Document Preview",
            "Adobe PDF Online Viewer",
            "File Download",
            "Custom"
        ])
        self.htmlsm_decoy_selector.currentIndexChanged.connect(self.on_decoy_changed)
        appearance_layout.addRow(QLabel("Decoy Template:"), self.htmlsm_decoy_selector)

        # Custom Template Input
        self.htmlsm_custom_template_input = QLineEdit()
        self.htmlsm_custom_template_input.setPlaceholderText("Select custom HTML template file...")
        self.htmlsm_custom_template_browse_btn = QPushButton("📂 Browse")
        self.htmlsm_custom_template_browse_btn.setFixedWidth(80)
        self.htmlsm_custom_template_browse_btn.clicked.connect(self.select_custom_template)
        
        custom_layout = list_to_hbox([self.htmlsm_custom_template_input, self.htmlsm_custom_template_browse_btn])
        self.htmlsm_custom_template_label = QLabel("Template File:")
        appearance_layout.addRow(self.htmlsm_custom_template_label, custom_layout)
        
        # Image URL
        self.htmlsm_image_url = QLineEdit()
        self.htmlsm_image_url.setPlaceholderText("https://example.com/click_me.jpg (optional)")
        self.htmlsm_image_url_label = QLabel("Decoy Image URL:")
        appearance_layout.addRow(self.htmlsm_image_url_label, self.htmlsm_image_url)
        
        # Evasion Checkbox
        self.htmlsm_evasion_checkbox = QCheckBox("Enable Keyword Evasion")
        appearance_layout.addRow("", self.htmlsm_evasion_checkbox)

        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # --- Packaging Section ---
        packaging_group = QGroupBox("Output Packaging")
        packaging_layout = QFormLayout()
        packaging_layout.setSpacing(12)
        
        self.htmlsm_package_selector = QComboBox()
        self.htmlsm_package_selector.addItems(["None", "ZIP Archive", "Password-Protected ZIP"])
        self.htmlsm_package_selector.currentIndexChanged.connect(self.on_package_changed)
        packaging_layout.addRow(QLabel("Format:"), self.htmlsm_package_selector)
        
        self.htmlsm_zip_password = QLineEdit()
        self.htmlsm_zip_password.setEchoMode(QLineEdit.Password)
        self.htmlsm_zip_password.setPlaceholderText("Enter password...")
        self.htmlsm_zip_password_label = QLabel("Password:")
        packaging_layout.addRow(self.htmlsm_zip_password_label, self.htmlsm_zip_password)
        
        packaging_group.setLayout(packaging_layout)
        layout.addWidget(packaging_group)
        
        # --- Action Section ---
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        
        self.htmlsm_generate_btn = QPushButton("🚀 Generate HTML File")
        self.htmlsm_generate_btn.setObjectName("primaryButton")
        self.htmlsm_generate_btn.clicked.connect(self.generate_html)
        btn_layout.addWidget(self.htmlsm_generate_btn)
        
        self.htmlsm_open_btn = QPushButton("🔍 Preview in Browser")
        self.htmlsm_open_btn.setEnabled(False)
        self.htmlsm_open_btn.clicked.connect(self.open_in_browser)
        btn_layout.addWidget(self.htmlsm_open_btn)
        
        layout.addLayout(btn_layout)
        
        # --- Status Section ---
        self.htmlsm_status = QLabel("")
        layout.addWidget(self.htmlsm_status)
        
        # Initialize Visibility
        self.on_encoding_changed(0)
        self.on_decoy_changed(0)
        self.on_package_changed(0)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def on_encoding_changed(self, index):
        method = self.htmlsm_encoding_selector.currentText()
        show_key = "XOR" in method
        show_chunk = "Chunked" in method
        
        self.htmlsm_key_length_label.setVisible(show_key)
        self.htmlsm_key_length.setVisible(show_key)
        
        self.htmlsm_chunk_size_label.setVisible(show_chunk)
        self.htmlsm_chunk_size.setVisible(show_chunk)

    def on_decoy_changed(self, index):
        decoy = self.htmlsm_decoy_selector.currentText()
        is_custom = "Custom" in decoy
        
        self.htmlsm_custom_template_label.setVisible(is_custom)
        self.htmlsm_custom_template_input.setVisible(is_custom)
        self.htmlsm_custom_template_browse_btn.setVisible(is_custom)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Payload File", "", "All Files (*)")
        if path:
            self.htmlsm_file_input.setText(path)

    def select_custom_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select HTML Template File", "", "HTML Files (*.html *.htm);;All Files (*)")
        if path:
            self.htmlsm_custom_template_input.setText(path)

    def on_package_changed(self, index):
        mode = self.htmlsm_package_selector.currentText()
        is_password = "Password" in mode
        
        self.htmlsm_zip_password_label.setVisible(is_password)
        self.htmlsm_zip_password.setVisible(is_password)

    def generate_html(self):
        file_path = self.htmlsm_file_input.text().strip()
        image_url = self.htmlsm_image_url.text().strip()
        download_name = self.htmlsm_output_filename.text().strip()
        mode_text = self.htmlsm_mode_selector.currentText()
        encoding_method = self.htmlsm_encoding_selector.currentText()
        decoy_type = self.htmlsm_decoy_selector.currentText()
        custom_template_path = self.htmlsm_custom_template_input.text().strip()
        enable_evasion = self.htmlsm_evasion_checkbox.isChecked()
        
        package_mode = self.htmlsm_package_selector.currentText()
        zip_password = self.htmlsm_zip_password.text().strip()
        
        # Map GUI text to mode string for generator
        mode = "auto_download"
        if "Click Anywhere" in mode_text:
            mode = "click_anywhere"
        
        if not file_path:
            self.show_error("Please select a file to embed")
            return
        
        if not os.path.exists(file_path):
             self.show_error("File not found")
             return
        
        if not download_name:
             self.show_error("Please enter a filename")
             return

        # Parse encoding params
        try:
            key_len = int(self.htmlsm_key_length.text().strip()) if self.htmlsm_key_length.isVisible() else 16
            chunk_size = int(self.htmlsm_chunk_size.text().strip()) if self.htmlsm_chunk_size.isVisible() else 4096
        except ValueError:
            self.show_error("Key length and chunk size must be integers")
            return

        try:
            self.htmlsm_status.setText("Status: Processing...")
            QApplication.processEvents()

            result = self.generator.generate(
                file_path=file_path, 
                image_url=image_url, 
                download_name=download_name, 
                mode=mode,
                encoding_method=encoding_method,
                key_length=key_len,
                chunk_size=chunk_size,
                decoy_type=decoy_type,
                custom_template_path=custom_template_path,
                enable_evasion=enable_evasion
            )
            
            # Check results
            generated_files = []
            if isinstance(result, list):
                abs_path = result[0]
                generated_files = result
            else:
                abs_path = result
                generated_files = [result]
            
            self.generated_html_path = abs_path
            self.generated_extra_files = generated_files[1:]

            self.htmlsm_status.setObjectName("statusSuccess")
            final_msg = f"✅ HTML generated: {abs_path}"

            # Packaging Logic
            if "None" not in package_mode:
                if "Password" in package_mode and not zip_password:
                     raise ValueError("Packaging password is required.")
                
                html_name = os.path.basename(abs_path)
                zip_name = os.path.splitext(html_name)[0] + ".zip"
                
                zip_pwd = zip_password if "Password" in package_mode else None
                zip_path = package_as_zip(generated_files, zip_name, password=zip_pwd)
                
                final_msg += f"\n📦 Packed in ZIP: {zip_path}"
            
            if self.generated_extra_files:
                final_msg += f"\nExtra Files: {len(self.generated_extra_files)}"

            self.htmlsm_status.setText(final_msg)
            self.htmlsm_status.setStyleSheet("color: #00b894; font-weight: bold;")
            
            self.htmlsm_open_btn.setEnabled(True)
            
            if self.window():
                self.window().statusBar().showMessage(f"Generated: {abs_path}")
        
        except Exception as e:
            self.show_error(f"Generation/packaging failed: {str(e)}")

    def show_error(self, message):
        self.htmlsm_status.setObjectName("statusError")
        self.htmlsm_status.setText(f"❌ {message}")
        self.htmlsm_status.setStyleSheet("color: #e94560; font-weight: bold;")

    def open_in_browser(self):
        if self.generated_html_path and os.path.exists(self.generated_html_path):
            webbrowser.open_new_tab(f"file://{self.generated_html_path}")
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
