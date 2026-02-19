# DeliverX

Phishing & Social Engineering Toolkit | 钓鱼与社会工程学工具集

**Author:** [@RyanCh01](https://github.com/RyanCh01)

基于 Python + PySide2 开发的 GUI 桌面应用，用于红队攻防演练中的钓鱼文件生成、载荷投递与社会工程学攻击。

## 功能模块

| 模块 | 说明 |
|------|------|
| 📄 PDF 生成 | 生成含全屏透明链接的钓鱼 PDF，支持预置模板和自定义内容 |
| 🌐 HTML 走私 | 将任意文件编码嵌入 HTML，浏览器打开后自动下载，支持多种编码和诱饵模板 |
| 🎨 SVG 生成 | SVG 文件走私/跳转，支持 JS 走私模式自动下载 payload |
| 🔗 LNK 生成 | 伪装快捷方式，支持 Explorer/Rundll32/Pcalua 等多种执行方式 |
| 💿 ISO 打包 | 将文件打包为 ISO 镜像，挂载后文件不携带 MOTW 标记 |
| 📦 文件捆绑 | 将 payload 与诱饵文档捆绑，执行后静默运行 payload 并打开正常文档 |
| 🔔 蜜标生成 | 生成 URL 追踪像素和 DNS 蜜标，监测目标是否打开文件 |
| 🕐 文件伪造 | 修改文件时间戳和 EXE 版本信息，伪装为正常系统文件 |

## 安装

```bash
# 克隆项目
git clone https://github.com/RyanCh01/DeliverX.git
cd DeliverX

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

## 依赖

- Python 3.8+
- PySide2（GUI 框架）
- reportlab（PDF 生成）
- pycdlib（ISO 镜像生成）
- pefile（PE 文件属性修改）
- pywin32（LNK 文件生成，仅 Windows）

## 使用说明

### HTML 走私

1. 选择要嵌入的文件（如 exe）
2. 选择下载模式：自动下载 / 点击任意位置下载
3. 选择编码方式：标准 Base64 / 反转+Base64 / XOR+Base64 / 分块乱序
4. 可选：选择诱饵模板、启用关键词规避
5. 点击生成，输出 HTML 文件

### LNK 生成

1. 选择执行方式（Explorer 打开 / Pcalua 代理执行 / Rundll32 加载 DLL 等）
2. 填写 payload 相对路径（如 `data\payload.exe`）
3. 选择伪装图标（PDF/Word/Excel）
4. 点击生成，按预览中的目录结构组织文件后打包发送

### ISO 打包

1. 添加要打包的文件（支持从 outputs/ 直接添加已生成的 LNK）
2. 设置卷标名称
3. 点击生成 ISO 镜像

### 文件捆绑

1. 选择 payload EXE 和诱饵文档
2. 选择生成模式：编译为 EXE（需 PyInstaller）或仅生成 Stub 脚本
3. 点击生成

### 文件伪造

- 时间戳修改：手动指定 / 从其他文件克隆 / 随机生成
- PE 属性修改：预置伪装方案（Word/Chrome/微信/钉钉等）或自定义

## 输出目录

所有生成的文件保存在 `outputs/` 目录中。

## 免责声明

本工具仅供合法的安全研究和授权的红队演练使用。使用者须遵守相关法律法规，因非法使用造成的一切后果由使用者自行承担。
