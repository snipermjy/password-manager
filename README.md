# Mima 密码管理器

一个安全、便捷的本地密码管理工具，支持桌面应用和浏览器扩展。

## ✨ 主要特性

### 桌面应用
- 🔐 本地SQLite数据库存储，数据不上传云端
- 🎯 支持密码分类管理（社交媒体、购物、工作、娱乐、金融等）
- 🔍 快速搜索和筛选
- 💾 支持导入/导出（Excel、CSV、JSON）
- 📧 支持邮件备份
- 🗑️ 回收站功能，误删可恢复
- 🎲 强密码生成器
- 🎨 自定义字段

### 浏览器扩展（Chrome/Edge）
- ✅ 智能识别登录表单
- 🔐 自动保存密码（智能判断：新账号、密码变更、已保存）
- ⚡ 自动填充密码（单账号直接填充，多账号选择列表）
- 🎯 账号归一化（自动忽略大小写和空格）
- 🔄 跨标签页同步
- 📦 页面加载即缓存，无需等待

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行桌面应用

```bash
python main.py
```

### 3. 打包成exe（可选）

双击运行 `一键打包.bat`，或手动执行：

```bash
pip install pyinstaller
pyinstaller build_exe.spec --clean
```

打包后的程序在 `dist\Mima密码管理器\` 文件夹。

## 🌐 浏览器扩展安装

### 步骤1：加载扩展

**Chrome:**
1. 访问 `chrome://extensions/`
2. 开启"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `browser_extension` 文件夹

**Edge:**
1. 访问 `edge://extensions/`
2. 开启"开发人员模式"
3. 点击"加载解压缩的扩展"
4. 选择 `browser_extension` 文件夹

### 步骤2：安装Native Messaging（扩展与桌面程序通信）

```bash
cd native_host
python install_native_host.py install --browser chrome
# 或
python install_native_host.py install --browser edge
```

### 步骤3：配置扩展ID

1. 在浏览器中复制扩展ID
2. 打开桌面应用 → 设置 → 浏览器扩展
3. 粘贴扩展ID并保存
4. 重启浏览器

## 📖 使用说明

### 桌面应用

- **添加密码**：点击"➕ 添加"按钮
- **搜索密码**：在搜索框输入关键词
- **分类筛选**：使用分类下拉框
- **批量导出**：勾选多个密码，点击"批量导出选中"
- **全选**：点击表头第一列的☑
- **导入/备份/回收站**：设置 → 数据管理

### 浏览器扩展

- **自动保存**：登录网站时自动弹窗提示保存密码
- **自动填充**：点击输入框旁边的Mima按钮
- **多账号**：自动显示选择列表
- **密码变更**：自动检测并提示更新

## 🛠️ 技术栈

- **桌面应用**: Python 3.8+, PyQt5, SQLite
- **浏览器扩展**: JavaScript (Chrome Extension Manifest V3)
- **打包工具**: PyInstaller

## 📁 项目结构

```
mima/
├── browser_extension/     # 浏览器扩展
├── core/                  # 核心业务逻辑
├── native_host/          # Native Messaging桥接
├── ui/                   # PyQt5界面
├── main.py              # 主程序入口
├── build_exe.spec       # PyInstaller配置
├── 一键打包.bat          # 一键打包脚本
└── 打包说明.txt          # 打包说明
```

## 🔒 安全说明

- 所有密码数据存储在本地SQLite数据库
- 不上传任何数据到云端
- 支持主密码保护（待实现）
- 建议定期备份数据库文件

## 📝 更新日志

### v1.0.0
- ✅ 桌面应用基础功能
- ✅ 浏览器扩展自动填充
- ✅ 智能保存密码
- ✅ 导入/导出功能
- ✅ 邮件备份
- ✅ 回收站功能

## ⚠️ 注意事项

1. 首次使用建议先备份数据
2. 浏览器扩展需要先运行桌面应用
3. 杀毒软件可能误报打包后的exe，添加白名单即可

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

Made with ❤️ by [Your Name]

