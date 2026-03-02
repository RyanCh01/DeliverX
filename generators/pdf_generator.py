import os
import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_pdf(url, template_mode="custom", custom_title="", custom_body="",
                 output_filename="phishing.pdf"):
    try:
        if not url:
            return False, "Please enter a target URL"
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Get template content
        if template_mode == "template1":
            title, body_lines = _get_template1()
        elif template_mode == "template2":
            title, body_lines = _get_template2()
        else:
            title = custom_title or "Notice"
            body_text = custom_body or "Please click to view the document."
            body_lines = body_text.split('\n')
        
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Try reportlab first (supports CJK fonts)
        try:
            return _generate_pdf_reportlab(url, title, body_lines, output_path)
        except ImportError:
            pass
        
        # Fallback: manual PDF construction (ASCII only)
        return _generate_pdf_manual(url, title, body_lines, output_path)
        
    except Exception as e:
        return False, f"Failed to generate PDF: {str(e)}"


def _generate_pdf_reportlab(url, title, body_lines, output_path):
    """Generate PDF using reportlab with font auto-detection"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import platform
    
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Register system font
    font_name = 'Helvetica'
    font_name_bold = 'Helvetica-Bold'
    
    font_paths = []
    if platform.system() == 'Windows':
        win_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        font_paths = [
            (os.path.join(win_fonts, 'msyh.ttc'), 'MSYH'),
            (os.path.join(win_fonts, 'simhei.ttf'), 'SimHei'),
            (os.path.join(win_fonts, 'simsun.ttc'), 'SimSun'),
        ]
    elif platform.system() == 'Darwin':
        font_paths = [
            ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
        ]
    else:
        font_paths = [
            ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WQY'),
        ]
    
    for fpath, fname in font_paths:
        if os.path.exists(fpath):
            try:
                pdfmetrics.registerFont(TTFont(fname, fpath, subfontIndex=0))
                font_name = fname
                font_name_bold = fname
                break
            except Exception:
                continue
    
    # Draw title
    c.setFont(font_name_bold if font_name_bold != font_name else font_name, 18)
    c.setFillColor(HexColor('#003380'))
    c.drawString(72, height - 72, title)
    
    # Separator line
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(1)
    c.line(72, height - 82, width - 72, height - 82)
    
    # Body text
    c.setFont(font_name, 11)
    c.setFillColor(HexColor('#333333'))
    
    y = height - 110
    for line in body_lines:
        if y < 160:
            break
        c.drawString(72, y, line.strip())
        y -= 18
    
    # Click prompt
    c.setFont(font_name, 13)
    c.setFillColor(HexColor('#0055cc'))
    click_text = ">>> Click here to view the document <<<"
    c.drawString(72, 120, click_text)
    
    # Underline
    c.setStrokeColor(HexColor('#0055cc'))
    c.setLineWidth(0.5)
    tw = c.stringWidth(click_text, font_name, 13)
    c.line(72, 116, 72 + tw, 116)
    
    # Date
    c.setFont(font_name, 9)
    c.setFillColor(HexColor('#999999'))
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    c.drawString(72, 80, f"Generated: {date_str}")
    
    # Full-page transparent link using reportlab's linkURL
    c.linkURL(url, (0, 0, width, height), relative=0,
              Border='[0 0 0]')
    
    c.save()
    
    return True, f"PDF generated: {output_path}"


def _generate_pdf_manual(url, title, body_lines, output_path):
    """Manual PDF construction (ASCII only, fallback)"""
    
    content_lines = []
    content_lines.append('BT')
    
    # Title
    content_lines.append('/F2 18 Tf')
    content_lines.append('0 0 0.8 rg')
    content_lines.append('72 750 Td')
    content_lines.append(f'({_pdf_escape(title)}) Tj')
    content_lines.append('ET')
    
    # Separator line
    content_lines.append('0.8 0.8 0.8 RG')
    content_lines.append('1 w')
    content_lines.append('72 738 m 523 738 l S')
    
    # Body text
    content_lines.append('BT')
    content_lines.append('/F1 11 Tf')
    content_lines.append('0.2 0.2 0.2 rg')
    
    y_pos = 710
    first_line = True
    for line in body_lines:
        if y_pos < 160:
            break
        if first_line:
            content_lines.append(f'72 {y_pos} Td')
            first_line = False
        else:
            content_lines.append('0 -16 Td')
        content_lines.append(f'({_pdf_escape(line.strip())}) Tj')
        y_pos -= 16
    
    content_lines.append('ET')
    
    # Click prompt
    content_lines.append('BT')
    content_lines.append('/F2 13 Tf')
    content_lines.append('0 0 0.9 rg')
    content_lines.append('72 120 Td')
    content_lines.append('(>>> Click Here to View Document <<<) Tj')
    content_lines.append('ET')
    
    # Underline
    content_lines.append('0 0 0.9 RG')
    content_lines.append('0.5 w')
    content_lines.append('72 116 m 340 116 l S')
    
    # Date
    content_lines.append('BT')
    content_lines.append('/F1 9 Tf')
    content_lines.append('0.5 0.5 0.5 rg')
    content_lines.append('72 80 Td')
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    content_lines.append(f'(Generated: {date_str}) Tj')
    content_lines.append('ET')
    
    content_stream = '\n'.join(content_lines)
    
    # PDF object structure
    pdf_objects = []
    
    pdf_objects.append(
        '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj'
    )
    pdf_objects.append(
        '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj'
    )
    pdf_objects.append(
        '3 0 obj\n'
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842]\n'
        '   /Contents 4 0 R\n'
        '   /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >>\n'
        '   /Annots [7 0 R]\n>>\nendobj'
    )
    pdf_objects.append(
        f'4 0 obj\n<< /Length {len(content_stream)} >>\n'
        f'stream\n{content_stream}\nendstream\nendobj'
    )
    pdf_objects.append(
        '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj'
    )
    pdf_objects.append(
        '6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj'
    )
    pdf_objects.append(
        '7 0 obj\n'
        '<< /Type /Annot /Subtype /Link /Rect [0 0 595 842]\n'
        '   /Border [0 0 0]\n'
        f'   /A << /Type /Action /S /URI /URI ({url}) >>\n>>\nendobj'
    )
    
    pdf_data = '%PDF-1.4\n'
    offsets = []
    for obj in pdf_objects:
        offsets.append(len(pdf_data))
        pdf_data += obj + '\n\n'
    
    xref_offset = len(pdf_data)
    pdf_data += f'xref\n0 {len(pdf_objects) + 1}\n'
    pdf_data += '0000000000 65535 f \n'
    for offset in offsets:
        pdf_data += f'{offset:010d} 00000 n \n'
    
    pdf_data += f'\ntrailer\n<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\n'
    pdf_data += f'startxref\n{xref_offset}\n%%EOF\n'
    
    with open(output_path, 'w', encoding='latin-1') as f:
        f.write(pdf_data)
    
    return True, f"PDF generated (ASCII fallback): {output_path}"


def _pdf_escape(text):
    text = text.replace('\\', '\\\\')
    text = text.replace('(', '\\(')
    text = text.replace(')', '\\)')
    return text


def _get_template1():
    """Template 1: Account Security Verification Notice"""
    title = "Account Security Verification Notice"
    body_lines = [
        "",
        "Dear User,",
        "",
        "Our security system has detected unusual login activity",
        "on your account. Immediate identity verification is required.",
        "",
        "Per the latest security policy update, all employees must",
        "complete identity verification within 24 hours.",
        "",
        "Failure to verify may result in temporary account suspension,",
        "preventing access to internal systems and email.",
        "",
        "",
        "Please click anywhere on this page to proceed with verification.",
        "",
        "",
        "If this was not initiated by you, contact IT Security immediately.",
        "",
        "Regards,",
        "IT Security Department",
    ]
    return title, body_lines


def _get_template2():
    """Template 2: File Preview Failed"""
    title = "Document Preview Failed"
    body_lines = [
        "",
        "The document you are trying to view cannot be displayed",
        "in the current PDF reader.",
        "",
        "Possible reasons:",
        "",
        "  1. The document has encryption protection enabled",
        "  2. The current PDF reader version is incompatible",
        "  3. The file format is restricted",
        "",
        "",
        "To view the full document, please click anywhere on this page",
        "to open it in the online document viewer.",
        "",
        "",
        "Note: You may need to sign in with your organization account",
        "to access this document.",
        "",
        "If the issue persists, contact the document owner or IT support.",
        "",
        "This notice was automatically generated by the system.",
    ]
    return title, body_lines


def get_template_list():
    return [
        "Security Verification Notice (lure user to verify identity)",
        "File Preview Failed (lure user to click online viewer)",
        "Custom Content",
    ]
