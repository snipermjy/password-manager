"""
界面样式 - 定义UI组件的样式
"""

# 主窗口样式
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3d8b40;
}

QPushButton#deleteButton {
    background-color: #f44336;
}

QPushButton#deleteButton:hover {
    background-color: #da190b;
}

QLineEdit, QTextEdit {
    padding: 6px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    font-size: 10pt;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #4CAF50;
}

QComboBox {
    padding: 6px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    font-size: 10pt;
}

QTableWidget {
    border: 1px solid #ddd;
    background-color: white;
    gridline-color: #e0e0e0;
    font-size: 10pt;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #e3f2fd;
    color: black;
}

QHeaderView::section {
    background-color: #f0f0f0;
    padding: 8px;
    border: none;
    border-right: 1px solid #ddd;
    border-bottom: 1px solid #ddd;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #ddd;
    background-color: white;
}

QTabBar::tab {
    background-color: #e0e0e0;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #4CAF50;
}

QGroupBox {
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QCheckBox {
    spacing: 8px;
    font-size: 10pt;
}

QLabel {
    font-size: 10pt;
}

QToolBar {
    background-color: white;
    border-bottom: 1px solid #ddd;
    spacing: 8px;
    padding: 4px;
}
"""

# 对话框样式
DIALOG_STYLE = """
QDialog {
    background-color: #f5f5f5;
}
"""

# 分类颜色映射（用于表格显示）
CATEGORY_COLORS = {
    '社交媒体': '#FF6B6B',
    '购物': '#4ECDC4',
    '工作': '#95E1D3',
    '娱乐': '#FFE66D',
    '金融': '#C06C84',
    '其他': '#999999'
}

