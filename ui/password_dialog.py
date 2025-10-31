"""
密码对话框 - 添加和编辑密码
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QDateEdit, QLabel,
    QGroupBox, QCheckBox, QSpinBox, QMessageBox, QFrame, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional

from core.database import Database
from core.models import Password
from core.password_gen import PasswordGenerator
from .styles import DIALOG_STYLE


class PasswordDialog(QDialog):
    """密码添加/编辑对话框"""
    
    def __init__(self, parent=None, password: Optional[Password] = None):
        super().__init__(parent)
        self.db = Database()
        self.password_gen = PasswordGenerator()
        
        self.password = password  # 如果为None，则是添加模式；否则是编辑模式
        self.old_password = None  # 用于记录修改历史
        
        # 自定义字段
        self.custom_field_widgets = {}
        
        self.init_ui()
        
        # 如果是编辑模式，加载数据
        if self.password:
            self.load_password_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(700)  # 对话框宽度
        self.setMinimumHeight(750)  # 对话框高度
        
        if self.password:
            self.setWindowTitle("编辑密码")
        else:
            self.setWindowTitle("添加密码")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 创建滚动区域的内容容器
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 网站名称（必填）
        self.site_name_input = QLineEdit()
        self.site_name_input.setPlaceholderText("例如：淘宝、GitHub")
        self.site_name_input.setMinimumHeight(32)
        form_layout.addRow("* 网站名称：", self.site_name_input)
        
        # 网址
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("例如：https://www.taobao.com")
        self.url_input.setMinimumHeight(32)
        form_layout.addRow("网址：", self.url_input)
        
        # 登录账号
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("用户名/手机号/邮箱")
        self.account_input.setMinimumHeight(32)
        form_layout.addRow("登录账号：", self.account_input)
        
        scroll_layout.addLayout(form_layout)
        
        # 密码输入区域（包含生成器）
        password_section = self.create_password_section()
        scroll_layout.addWidget(password_section)
        
        # 其他字段
        form_layout2 = QFormLayout()
        form_layout2.setSpacing(10)
        
        # 手机号
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("绑定的手机号")
        self.phone_input.setMinimumHeight(32)
        form_layout2.addRow("手机号：", self.phone_input)
        
        # 邮箱
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("注册使用的邮箱")
        self.email_input.setMinimumHeight(32)
        form_layout2.addRow("邮箱：", self.email_input)
        
        # 分类
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(32)
        self.load_categories()
        form_layout2.addRow("分类：", self.category_combo)
        
        # 注册时间
        self.register_date = QDateEdit()
        self.register_date.setCalendarPopup(True)
        self.register_date.setDate(QDate.currentDate())
        self.register_date.setDisplayFormat("yyyy-MM-dd")
        self.register_date.setMinimumHeight(32)
        form_layout2.addRow("注册时间：", self.register_date)
        
        # 备注
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("其他补充信息")
        self.notes_input.setMaximumHeight(80)
        form_layout2.addRow("备注：", self.notes_input)
        
        scroll_layout.addLayout(form_layout2)
        
        # 自定义字段区域
        self.custom_fields_layout = QVBoxLayout()
        self.load_custom_fields()
        scroll_layout.addLayout(self.custom_fields_layout)
        
        # 修改历史按钮（仅编辑模式显示）
        if self.password:
            history_btn = QPushButton("📝 查看修改历史")
            history_btn.clicked.connect(self.show_modification_history)
            scroll_layout.addWidget(history_btn)
        
        # 添加一个弹性空间，让内容靠上显示
        scroll_layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # 按钮区域（固定在底部，不滚动）
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.on_save)
        save_btn.setMinimumWidth(100)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_password_section(self) -> QGroupBox:
        """创建密码输入区域（包含生成器）"""
        group = QGroupBox("* 密码")
        layout = QVBoxLayout(group)
        
        # 密码输入框
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Normal)  # 默认显示明文
        self.password_input.setPlaceholderText("输入密码或使用生成器")
        self.password_input.setMinimumHeight(32)
        password_layout.addWidget(self.password_input)
        
        # 显示/隐藏按钮
        self.show_pwd_btn = QPushButton("隐藏")
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.setChecked(True)  # 默认为显示状态
        self.show_pwd_btn.clicked.connect(self.toggle_password_visibility)
        self.show_pwd_btn.setFixedWidth(60)
        self.show_pwd_btn.setMinimumHeight(32)
        password_layout.addWidget(self.show_pwd_btn)
        
        layout.addLayout(password_layout)
        
        # 密码生成器
        gen_group = self.create_password_generator()
        layout.addWidget(gen_group)
        
        return group
    
    def create_password_generator(self) -> QFrame:
        """创建密码生成器"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; }")
        frame.setMinimumHeight(240)  # 设置最小高度确保内容显示
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)  # 增加垂直间距
        
        # 标题
        title = QLabel("🔑 快速生成密码")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        title.setMinimumHeight(25)
        layout.addWidget(title)
        
        # 生成选项
        options_widget = QWidget()
        options_widget.setMinimumHeight(45)  # 确保有足够高度
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 8, 0, 8)
        options_layout.setSpacing(12)
        
        # 长度
        length_label = QLabel("长度：")
        length_label.setMinimumWidth(40)
        length_label.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(length_label)
        
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 32)
        self.length_spin.setValue(12)
        self.length_spin.setFixedWidth(70)
        self.length_spin.setMinimumHeight(28)
        options_layout.addWidget(self.length_spin)
        
        options_layout.addSpacing(15)
        
        # 字符类型选项
        self.upper_check = QCheckBox("大写")
        self.upper_check.setChecked(True)
        self.upper_check.setMinimumWidth(60)
        self.upper_check.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(self.upper_check)
        
        self.lower_check = QCheckBox("小写")
        self.lower_check.setChecked(True)
        self.lower_check.setMinimumWidth(60)
        self.lower_check.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(self.lower_check)
        
        self.digit_check = QCheckBox("数字")
        self.digit_check.setChecked(True)
        self.digit_check.setMinimumWidth(60)
        self.digit_check.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(self.digit_check)
        
        self.symbol_check = QCheckBox("符号")
        self.symbol_check.setChecked(True)
        self.symbol_check.setMinimumWidth(60)
        self.symbol_check.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(self.symbol_check)
        
        options_layout.addStretch()
        layout.addWidget(options_widget)
        
        # 生成结果
        result_widget = QWidget()
        result_widget.setMinimumHeight(45)  # 确保有足够高度
        result_layout = QHBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 8, 0, 8)
        result_layout.setSpacing(10)
        
        result_label = QLabel("生成结果：")
        result_label.setMinimumWidth(70)
        result_label.setStyleSheet("font-size: 10pt;")
        result_layout.addWidget(result_label)
        
        self.generated_pwd = QLineEdit()
        self.generated_pwd.setReadOnly(True)
        self.generated_pwd.setMinimumHeight(34)
        self.generated_pwd.setStyleSheet("padding: 6px; font-size: 10pt;")
        result_layout.addWidget(self.generated_pwd, stretch=1)
        
        generate_btn = QPushButton("重新生成")
        generate_btn.clicked.connect(self.generate_password)
        generate_btn.setFixedWidth(100)
        generate_btn.setFixedHeight(34)
        generate_btn.setStyleSheet("font-size: 10pt;")
        result_layout.addWidget(generate_btn, stretch=0)
        
        layout.addWidget(result_widget)
        
        # 使用按钮
        use_btn = QPushButton("使用此密码")
        use_btn.clicked.connect(self.use_generated_password)
        use_btn.setMinimumHeight(40)
        use_btn.setStyleSheet("font-size: 10.5pt; font-weight: bold; padding: 8px;")
        layout.addWidget(use_btn)
        
        # 初始生成一个密码
        self.generate_password()
        
        return frame
    
    def toggle_password_visibility(self):
        """切换密码可见性"""
        if self.show_pwd_btn.isChecked():
            # 显示明文
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_pwd_btn.setText("隐藏")
        else:
            # 隐藏密码
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_pwd_btn.setText("显示")
    
    def generate_password(self):
        """生成密码"""
        length = self.length_spin.value()
        use_upper = self.upper_check.isChecked()
        use_lower = self.lower_check.isChecked()
        use_digit = self.digit_check.isChecked()
        use_symbol = self.symbol_check.isChecked()
        
        password = self.password_gen.generate(
            length=length,
            use_uppercase=use_upper,
            use_lowercase=use_lower,
            use_digits=use_digit,
            use_symbols=use_symbol
        )
        
        self.generated_pwd.setText(password)
    
    def use_generated_password(self):
        """使用生成的密码"""
        password = self.generated_pwd.text()
        if password:
            self.password_input.setText(password)
            QMessageBox.information(self, "成功", "密码已填入")
    
    def load_categories(self):
        """加载分类列表"""
        categories = self.db.get_all_categories()
        self.category_combo.clear()
        for cat in categories:
            self.category_combo.addItem(cat.name)
    
    def load_custom_fields(self):
        """加载自定义字段"""
        # 清空现有布局
        while self.custom_fields_layout.count():
            child = self.custom_fields_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 获取自定义字段定义
        custom_fields = self.db.get_all_custom_fields()
        
        if custom_fields:
            # 添加分隔线和标题
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            self.custom_fields_layout.addWidget(separator)
            
            label = QLabel("--- 自定义字段 ---")
            label.setStyleSheet("font-weight: bold; color: #666;")
            label.setAlignment(Qt.AlignCenter)
            self.custom_fields_layout.addWidget(label)
            
            # 添加自定义字段输入框
            form_layout = QFormLayout()
            for field in custom_fields:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText(f"输入{field.field_name}")
                input_widget.setMinimumHeight(32)
                form_layout.addRow(f"{field.field_name}：", input_widget)
                self.custom_field_widgets[field.field_name] = input_widget
            
            self.custom_fields_layout.addLayout(form_layout)
    
    def load_password_data(self):
        """加载密码数据（编辑模式）"""
        if not self.password:
            return
        
        # 保存旧密码用于记录修改
        self.old_password = Password.from_dict(self.password.to_dict())
        
        # 填充基本字段
        self.site_name_input.setText(self.password.site_name)
        self.url_input.setText(self.password.url or "")
        self.account_input.setText(self.password.login_account or "")
        self.password_input.setText(self.password.password)
        self.phone_input.setText(self.password.phone or "")
        self.email_input.setText(self.password.email or "")
        self.notes_input.setPlainText(self.password.notes or "")
        
        # 分类
        if self.password.category:
            index = self.category_combo.findText(self.password.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        # 注册时间
        if self.password.register_date:
            try:
                date = QDate.fromString(self.password.register_date, "yyyy-MM-dd")
                self.register_date.setDate(date)
            except:
                pass
        
        # 填充自定义字段
        for field_name, value in self.password.custom_fields.items():
            if field_name in self.custom_field_widgets:
                self.custom_field_widgets[field_name].setText(value)
    
    def on_save(self):
        """保存密码"""
        # 验证必填字段
        site_name = self.site_name_input.text().strip()
        password = self.password_input.text().strip()
        
        if not site_name:
            QMessageBox.warning(self, "提示", "请输入网站名称")
            self.site_name_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            self.password_input.setFocus()
            return
        
        # 收集自定义字段值
        custom_fields = {}
        for field_name, widget in self.custom_field_widgets.items():
            value = widget.text().strip()
            if value:  # 只保存非空值
                custom_fields[field_name] = value
        
        try:
            if self.password:
                # 编辑模式
                self.password.site_name = site_name
                self.password.url = self.url_input.text().strip()
                self.password.login_account = self.account_input.text().strip()
                self.password.password = password
                self.password.phone = self.phone_input.text().strip()
                self.password.email = self.email_input.text().strip()
                self.password.category = self.category_combo.currentText()
                self.password.notes = self.notes_input.toPlainText().strip()
                self.password.register_date = self.register_date.date().toString("yyyy-MM-dd")
                self.password.custom_fields = custom_fields
                
                # 更新到数据库
                self.db.update_password(self.password, self.old_password)
                QMessageBox.information(self, "成功", "密码已更新")
            else:
                # 添加模式
                new_password = Password(
                    site_name=site_name,
                    url=self.url_input.text().strip(),
                    login_account=self.account_input.text().strip(),
                    password=password,
                    phone=self.phone_input.text().strip(),
                    email=self.email_input.text().strip(),
                    category=self.category_combo.currentText(),
                    notes=self.notes_input.toPlainText().strip(),
                    register_date=self.register_date.date().toString("yyyy-MM-dd")
                )
                new_password.custom_fields = custom_fields
                
                # 添加到数据库
                self.db.add_password(new_password)
                QMessageBox.information(self, "成功", "密码已添加")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def show_modification_history(self):
        """显示修改历史"""
        if not self.password:
            return
        
        history = self.db.get_modification_history(self.password.id)
        
        if not history:
            QMessageBox.information(self, "修改历史", "暂无修改记录")
            return
        
        # 构建历史信息
        history_text = "修改历史记录：\n\n"
        for item in history:
            history_text += f"【{item.modified_at}】\n"
            history_text += f"{item.field_name}：{item.old_value} → {item.new_value}\n\n"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("修改历史")
        msg.setText(history_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

