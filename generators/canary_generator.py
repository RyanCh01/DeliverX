import os
import uuid
import html
from config import OUTPUT_DIR


def _generate_token_id():
    return str(uuid.uuid4()).replace('-', '')[:16]


def generate_url_canary(callback_url, output_filename="canary_pixel.html"):
    try:
        token_id = _generate_token_id()
        sep = "&" if '?' in callback_url else "?"
        tracking_url = f"{callback_url}{sep}t={token_id}"
        pixel_html = f'<img src="{html.escape(tracking_url)}" width="1" height="1" style="display:none" alt="">'
        full_html = f'<!DOCTYPE html>\n<html>\n<head><title>Canary Token Test</title></head>\n<body>\n<p>这是一封正常的邮件内容。</p>\n{pixel_html}\n</body>\n</html>'
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        return True, (
            f"URL 追踪蜜标已生成: {output_path}\n\nToken ID: {token_id}\n追踪 URL: {tracking_url}\n\n"
            f"HTML 像素代码（复制到邮件正文中）:\n{pixel_html}\n\n"
            f"使用方式:\n1. 将 <img> 标签粘贴到钓鱼邮件的 HTML 正文中\n"
            f"2. 目标打开邮件时，邮件客户端自动加载图片\n"
            f"3. 你的服务器收到请求 → 确认目标已打开邮件\n4. 通过 Token ID 区分不同目标"
        )
    except Exception as e:
        return False, f"生成 URL 蜜标失败: {str(e)}"


def generate_dns_canary(dns_domain, identifier="target1", output_filename="canary_dns.html"):
    try:
        token_id = _generate_token_id()
        subdomain = f"{identifier}.{token_id}.{dns_domain}"
        dns_html = (
            f'<!DOCTYPE html>\n<html>\n<head>\n<title>Document</title>\n'
            f'<style>\nbody {{ background-image: url(\'http://{subdomain}/bg.png\'); }}\n</style>\n'
            f'</head>\n<body>\n<p>文档内容</p>\n'
            f'<img src="http://{subdomain}/pixel.png" width="1" height="1" style="display:none">\n'
            f'<link rel="stylesheet" href="http://{subdomain}/style.css">\n</body>\n</html>'
        )
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dns_html)
        return True, (
            f"DNS 蜜标已生成: {output_path}\n\nToken ID: {token_id}\n触发域名: {subdomain}\n\n"
            f"使用方式:\n1. 确保你控制 {dns_domain} 的 DNS 服务器\n"
            f"2. 监控 *.{dns_domain} 的 DNS 查询记录\n"
            f"3. 目标打开此 HTML 时触发对 {subdomain} 的 DNS 解析\n"
            f"4. 你在 DNS 日志中看到查询 → 确认目标已打开文件\n\n"
            f"优势: 即使 HTTP 被防火墙拦截，DNS 查询通常不受限"
        )
    except Exception as e:
        return False, f"生成 DNS 蜜标失败: {str(e)}"


def get_canary_types():
    return [
        "URL 追踪像素（邮件打开检测）",
        "DNS 蜜标（绕过 HTTP 拦截）",
    ]
