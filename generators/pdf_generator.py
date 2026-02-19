import os
import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_pdf(url, template_mode="custom", custom_title="", custom_body="",
                 output_filename="phishing.pdf"):
    try:
        if not url:
            return False, "请输入目标 URL"
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 获取模板内容
        if template_mode == "template1":
            title, body_lines = _get_template1()
        elif template_mode == "template2":
            title, body_lines = _get_template2()
        else:
            title = custom_title or "通知"
            body_text = custom_body or "请点击查看文档。"
            body_lines = body_text.split('\n')
        
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 尝试使用 reportlab（支持中文）
        try:
            return _generate_pdf_reportlab(url, title, body_lines, output_path)
        except ImportError:
            pass
        
        # 回退：手工 PDF（仅支持英文）
        return _generate_pdf_manual(url, title, body_lines, output_path)
        
    except Exception as e:
        return False, f"生成 PDF 失败: {str(e)}"


def _generate_pdf_reportlab(url, title, body_lines, output_path):
    """使用 reportlab 生成支持中文的 PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import platform
    
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # 注册中文字体
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
    
    # 绘制标题
    c.setFont(font_name_bold if font_name_bold != font_name else font_name, 18)
    c.setFillColor(HexColor('#003380'))
    c.drawString(72, height - 72, title)
    
    # 分隔线
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(1)
    c.line(72, height - 82, width - 72, height - 82)
    
    # 正文
    c.setFont(font_name, 11)
    c.setFillColor(HexColor('#333333'))
    
    y = height - 110
    for line in body_lines:
        if y < 160:
            break
        c.drawString(72, y, line.strip())
        y -= 18
    
    # 点击提示
    c.setFont(font_name, 13)
    c.setFillColor(HexColor('#0055cc'))
    click_text = ">>> 点击此处查看文档 <<<"
    c.drawString(72, 120, click_text)
    
    # 下划线
    c.setStrokeColor(HexColor('#0055cc'))
    c.setLineWidth(0.5)
    tw = c.stringWidth(click_text, font_name, 13)
    c.line(72, 116, 72 + tw, 116)
    
    # 日期
    c.setFont(font_name, 9)
    c.setFillColor(HexColor('#999999'))
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    c.drawString(72, 80, f"生成日期: {date_str}")
    
    # 全页透明链接 - 使用 reportlab 的 linkURL 方法
    c.linkURL(url, (0, 0, width, height), relative=0,
              Border='[0 0 0]')
    
    c.save()
    
    return True, f"PDF 已生成: {output_path}"


def _generate_pdf_manual(url, title, body_lines, output_path):
    """手工构建 PDF（不支持中文，作为回退方案）"""
    
    content_lines = []
    content_lines.append('BT')
    
    # 标题
    content_lines.append('/F2 18 Tf')
    content_lines.append('0 0 0.8 rg')
    content_lines.append('72 750 Td')
    content_lines.append(f'({_pdf_escape(title)}) Tj')
    content_lines.append('ET')
    
    # 分隔线
    content_lines.append('0.8 0.8 0.8 RG')
    content_lines.append('1 w')
    content_lines.append('72 738 m 523 738 l S')
    
    # 正文
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
    
    # 点击提示
    content_lines.append('BT')
    content_lines.append('/F2 13 Tf')
    content_lines.append('0 0 0.9 rg')
    content_lines.append('72 120 Td')
    content_lines.append('(>>> Click Here to View Document <<<) Tj')
    content_lines.append('ET')
    
    # 下划线
    content_lines.append('0 0 0.9 RG')
    content_lines.append('0.5 w')
    content_lines.append('72 116 m 340 116 l S')
    
    # 日期
    content_lines.append('BT')
    content_lines.append('/F1 9 Tf')
    content_lines.append('0.5 0.5 0.5 rg')
    content_lines.append('72 80 Td')
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    content_lines.append(f'(Generated: {date_str}) Tj')
    content_lines.append('ET')
    
    content_stream = '\n'.join(content_lines)
    
    # PDF 对象结构
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
    
    return True, f"PDF 已生成（英文回退模式）: {output_path}"


def _pdf_escape(text):
    text = text.replace('\\', '\\\\')
    text = text.replace('(', '\\(')
    text = text.replace(')', '\\)')
    return text


def _get_template1():
    """模板1：安全验证通知"""
    title = "账户安全验证通知"
    body_lines = [
        "",
        "尊敬的用户：",
        "",
        "我们的安全系统检测到您的账户存在异常登录行为，",
        "需要您立即进行身份验证。",
        "",
        "根据最新的安全策略更新，所有员工须在 24 小时",
        "内完成身份验证操作。",
        "",
        "未完成验证可能导致账户被临时冻结，届时将无法",
        "访问企业内部系统和邮箱。",
        "",
        "",
        "请点击本页面任意位置进行安全验证。",
        "",
        "",
        "如非本人操作，请立即联系 IT 安全部门。",
        "",
        "此致",
        "IT 安全管理部",
    ]
    return title, body_lines


def _get_template2():
    """模板2：文件预览失败"""
    title = "文档预览失败"
    body_lines = [
        "",
        "您正在查看的文档无法在当前 PDF 阅读器中显示。",
        "",
        "可能的原因：",
        "",
        "  1. 文档已启用加密保护",
        "  2. 当前 PDF 阅读器版本不兼容",
        "  3. 文件格式受限",
        "",
        "",
        "如需查看完整文档内容，请点击本页面任意位置，",
        "通过在线文档查看器打开。",
        "",
        "",
        "注意：您可能需要使用组织账户登录后才能",
        "访问此文档。",
        "",
        "如问题持续存在，请联系文档所有者或 IT 支持。",
        "",
        "此通知由系统自动生成。",
    ]
    return title, body_lines


def get_template_list():
    return [
        "安全验证通知（诱导用户进行身份验证）",
        "文件预览失败（诱导用户点击在线查看）",
        "自定义内容",
    ]
