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
        full_html = f'<!DOCTYPE html>\n<html>\n<head><title>Canary Token Test</title></head>\n<body>\n<p>This is a normal email body.</p>\n{pixel_html}\n</body>\n</html>'
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        return True, (
            f"URL tracking canary generated: {output_path}\n\nToken ID: {token_id}\nTracking URL: {tracking_url}\n\n"
            f"HTML pixel code (paste into email body):\n{pixel_html}\n\n"
            f"Usage:\n1. Paste the <img> tag into the HTML body of your phishing email\n"
            f"2. When the target opens the email, the email client loads the image\n"
            f"3. Your server receives the request -> confirms target opened the email\n4. Use Token ID to distinguish different targets"
        )
    except Exception as e:
        return False, f"Failed to generate URL canary: {str(e)}"


def generate_dns_canary(dns_domain, identifier="target1", output_filename="canary_dns.html"):
    try:
        token_id = _generate_token_id()
        subdomain = f"{identifier}.{token_id}.{dns_domain}"
        dns_html = (
            f'<!DOCTYPE html>\n<html>\n<head>\n<title>Document</title>\n'
            f'<style>\nbody {{ background-image: url(\'http://{subdomain}/bg.png\'); }}\n</style>\n'
            f'</head>\n<body>\n<p>Document content</p>\n'
            f'<img src="http://{subdomain}/pixel.png" width="1" height="1" style="display:none">\n'
            f'<link rel="stylesheet" href="http://{subdomain}/style.css">\n</body>\n</html>'
        )
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dns_html)
        return True, (
            f"DNS canary generated: {output_path}\n\nToken ID: {token_id}\nTrigger domain: {subdomain}\n\n"
            f"Usage:\n1. Ensure you control the DNS server for {dns_domain}\n"
            f"2. Monitor DNS query logs for *.{dns_domain}\n"
            f"3. When the target opens this HTML, it triggers a DNS lookup for {subdomain}\n"
            f"4. You see the query in DNS logs -> confirms target opened the file\n\n"
            f"Advantage: Even if HTTP is blocked by a firewall, DNS queries are usually unrestricted"
        )
    except Exception as e:
        return False, f"Failed to generate DNS canary: {str(e)}"


def get_canary_types():
    return [
        "URL Tracking Pixel (email open detection)",
        "DNS Canary (bypass HTTP blocking)",
    ]
