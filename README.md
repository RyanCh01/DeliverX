# DeliverX

Phishing & Social Engineering Toolkit

**Author:** [@RyanCh01](https://github.com/RyanCh01)

A GUI desktop application built with Python + PySide2 for generating phishing files, payload delivery, and social engineering attacks in red team engagements.

## Modules

| Module | Description |
|--------|-------------|
| 📄 PDF Generator | Generate phishing PDFs with full-page transparent link overlays. Supports preset templates and custom content |
| 🌐 HTML Smuggling | Encode and embed any file into HTML for automatic download via browser. Supports multiple encoding methods and decoy templates |
| 🎨 SVG Generator | SVG file smuggling/redirect. JS smuggling mode auto-downloads payloads |
| 🔗 LNK Generator | Craft disguised shortcuts with multiple execution modes (Explorer/Rundll32/Pcalua/etc.) |
| 💿 ISO Packager | Package files into ISO images. Mounted files bypass MOTW (Mark of the Web) |
| 📦 File Binder | Bundle payload with a decoy document. Executes payload silently while opening the legitimate document |
| 🔔 Canary Token | Generate URL tracking pixels and DNS canary tokens to detect if a target opens a file |
| 🕐 File Spoofer | Modify file timestamps and EXE version info to impersonate legitimate system files |

## Installation

```bash
# Clone the repository
git clone https://github.com/RyanCh01/DeliverX.git
cd DeliverX

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

## Dependencies

- Python 3.8+
- PySide2 (GUI framework)
- reportlab (PDF generation)
- pycdlib (ISO image creation)
- pefile (PE file attribute modification)
- pywin32 (LNK file generation, Windows only)

## Usage

### HTML Smuggling

1. Select the file to embed (e.g. an EXE)
2. Choose trigger mode: Auto Download / Click Anywhere to Download
3. Choose encoding: Standard Base64 / Reverse+Base64 / XOR+Base64 / Chunked Shuffle
4. Optional: Select a decoy template, enable keyword evasion
5. Click Generate to output the HTML file

### LNK Generator

1. Select execution mode (Explorer Open / Pcalua Proxy / Rundll32 Load DLL, etc.)
2. Enter the payload relative path (e.g. `data\payload.exe`)
3. Choose a disguise icon (PDF/Word/Excel)
4. Click Generate, then organize files per the directory structure preview

### ISO Packager

1. Add files to pack (supports adding generated LNK files from outputs/)
2. Set the volume label
3. Click Generate ISO Image

### File Binder

1. Select a payload EXE and a decoy document
2. Choose build mode: Compile to EXE (requires PyInstaller) or Generate Stub Script only
3. Click Generate

### File Spoofer

- Timestamp Modification: Specify manually / Clone from another file / Generate random
- PE Attribute Modification: Use preset disguises (Word/Chrome/WeChat/DingTalk) or customize

## Output Directory

All generated files are saved in the `outputs/` directory.

## Disclaimer

This tool is intended solely for authorized security research and legitimate red team engagements. Users must comply with all applicable laws and regulations. The author assumes no liability for any misuse or damages resulting from unauthorized use.
