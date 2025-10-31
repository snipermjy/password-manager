"""
设置对话框 - 应用设置管理
"""
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QLabel, QCheckBox, QComboBox, QLineEdit, QFormLayout,
    QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QColorDialog, QSpinBox, QTextEdit, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from typing import Dict

from core.database import Database
from core.models import Category, CustomField
from core.backup import BackupManager
from .styles import DIALOG_STYLE


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.backup_manager = BackupManager()
        
        # 标记是否有修改分类或自定义字段
        self.categories_modified = False
        self.custom_fields_modified = False
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 通用设置
        self.tabs.addTab(self.create_general_tab(), "通用")
        
        # 显示设置
        self.tabs.addTab(self.create_display_tab(), "显示")
        
        # 数据管理（新增）
        self.tabs.addTab(self.create_data_management_tab(), "数据管理")
        
        # 备份设置
        self.tabs.addTab(self.create_backup_tab(), "备份")
        
        # 分类管理
        self.tabs.addTab(self.create_category_tab(), "分类管理")
        
        # 字段管理
        self.tabs.addTab(self.create_custom_field_tab(), "字段管理")
        
        # 浏览器扩展
        
        layout.addWidget(self.tabs)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self) -> QWidget:
        """创建通用设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 通用设置
        group = QGroupBox("通用设置")
        form = QFormLayout(group)
        
        # 主密码保护（暂未实现）
        self.master_pwd_check = QCheckBox("启用主密码保护")
        self.master_pwd_check.setEnabled(False)
        self.master_pwd_check.setToolTip("此功能暂未实现")
        form.addRow("", self.master_pwd_check)
        
        # 删除确认
        self.confirm_delete_check = QCheckBox("删除时二次确认")
        self.confirm_delete_check.setChecked(True)
        form.addRow("", self.confirm_delete_check)
        
        # 默认排序
        self.default_sort_combo = QComboBox()
        self.default_sort_combo.addItems([
            "创建时间降序",
            "创建时间升序",
            "修改时间降序",
            "修改时间升序",
            "网站名称升序",
            "网站名称降序"
        ])
        form.addRow("默认排序：", self.default_sort_combo)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def create_data_management_tab(self) -> QWidget:
        """创建数据管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 导入数据
        import_group = QGroupBox("📥 导入数据")
        import_layout = QVBoxLayout(import_group)
        import_layout.setSpacing(10)
        
        import_info = QLabel("从Excel、CSV或JSON文件导入密码数据")
        import_info.setStyleSheet("color: #666; font-size: 9pt;")
        import_layout.addWidget(import_info)
        
        import_btn = QPushButton("📥 导入密码数据")
        import_btn.setMinimumHeight(50)
        import_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                font-weight: bold;
                padding: 10px;
                background: #4CAF50;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        import_btn.clicked.connect(self.on_import_data)
        import_layout.addWidget(import_btn)
        
        layout.addWidget(import_group)
        
        # 备份数据
        backup_group = QGroupBox("💾 备份数据")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(10)
        
        backup_info = QLabel("将所有密码导出为Excel、CSV或JSON格式，或发送到邮箱")
        backup_info.setStyleSheet("color: #666; font-size: 9pt;")
        backup_layout.addWidget(backup_info)
        
        backup_buttons = QHBoxLayout()
        backup_buttons.setSpacing(10)
        
        local_backup_btn = QPushButton("💾 导出到本地")
        local_backup_btn.setMinimumHeight(50)
        local_backup_btn.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                font-weight: bold;
                padding: 10px;
                background: #2196F3;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #0b7dda;
            }
        """)
        local_backup_btn.clicked.connect(self.on_local_backup)
        backup_buttons.addWidget(local_backup_btn)
        
        email_backup_btn = QPushButton("📧 发送到邮箱")
        email_backup_btn.setMinimumHeight(50)
        email_backup_btn.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                font-weight: bold;
                padding: 10px;
                background: #FF9800;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #e68900;
            }
        """)
        email_backup_btn.clicked.connect(self.on_email_backup)
        backup_buttons.addWidget(email_backup_btn)
        
        backup_layout.addLayout(backup_buttons)
        layout.addWidget(backup_group)
        
        # 回收站
        recycle_group = QGroupBox("🗑 回收站")
        recycle_layout = QVBoxLayout(recycle_group)
        recycle_layout.setSpacing(10)
        
        recycle_info = QLabel("查看、恢复或永久删除回收站中的密码记录")
        recycle_info.setStyleSheet("color: #666; font-size: 9pt;")
        recycle_layout.addWidget(recycle_info)
        
        recycle_btn = QPushButton("🗑 打开回收站")
        recycle_btn.setMinimumHeight(50)
        recycle_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                font-weight: bold;
                padding: 10px;
                background: #f44336;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #da190b;
            }
        """)
        recycle_btn.clicked.connect(self.on_open_recycle_bin)
        recycle_layout.addWidget(recycle_btn)
        
        layout.addWidget(recycle_group)
        
        layout.addStretch()
        
        return widget
    
    def create_display_tab(self) -> QWidget:
        """创建显示设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("显示设置")
        form = QFormLayout(group)
        
        # 显示密码
        self.show_password_check = QCheckBox("主界面显示密码（明文）")
        self.show_password_check.setChecked(True)
        form.addRow("", self.show_password_check)
        
        # 显示列设置
        columns_label = QLabel("主界面显示列：")
        form.addRow(columns_label)
        
        self.show_site_name = QCheckBox("网站名称")
        self.show_site_name.setChecked(True)
        self.show_site_name.setEnabled(False)  # 必须显示
        form.addRow("", self.show_site_name)
        
        self.show_account = QCheckBox("登录账号")
        self.show_account.setChecked(True)
        form.addRow("", self.show_account)
        
        self.show_password = QCheckBox("密码")
        self.show_password.setChecked(True)
        form.addRow("", self.show_password)
        
        self.show_category = QCheckBox("分类")
        self.show_category.setChecked(True)
        form.addRow("", self.show_category)
        
        self.show_register_date = QCheckBox("注册时间")
        self.show_register_date.setChecked(True)
        form.addRow("", self.show_register_date)
        
        self.show_url = QCheckBox("网址")
        form.addRow("", self.show_url)
        
        self.show_phone = QCheckBox("手机号")
        form.addRow("", self.show_phone)
        
        self.show_email = QCheckBox("邮箱")
        form.addRow("", self.show_email)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def create_backup_tab(self) -> QWidget:
        """创建备份设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # SMTP设置
        smtp_group = QGroupBox("邮箱SMTP设置")
        smtp_form = QFormLayout(smtp_group)
        
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("例如：smtp.qq.com")
        smtp_form.addRow("SMTP服务器：", self.smtp_server_input)
        
        self.smtp_port_input = QSpinBox()
        self.smtp_port_input.setRange(1, 65535)
        self.smtp_port_input.setValue(465)
        smtp_form.addRow("SMTP端口：", self.smtp_port_input)
        
        self.smtp_email_input = QLineEdit()
        self.smtp_email_input.setPlaceholderText("your@email.com")
        smtp_form.addRow("发件邮箱：", self.smtp_email_input)
        
        pwd_layout = QHBoxLayout()
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        self.smtp_password_input.setPlaceholderText("邮箱授权码（不是登录密码）")
        pwd_layout.addWidget(self.smtp_password_input)
        
        show_pwd_btn = QPushButton("显示")
        show_pwd_btn.setCheckable(True)
        show_pwd_btn.setMaximumWidth(60)
        show_pwd_btn.toggled.connect(
            lambda checked: self.smtp_password_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        pwd_layout.addWidget(show_pwd_btn)
        smtp_form.addRow("授权码：", pwd_layout)
        
        self.backup_email_input = QLineEdit()
        self.backup_email_input.setPlaceholderText("接收备份的邮箱地址")
        smtp_form.addRow("收件邮箱：", self.backup_email_input)
        
        # 测试连接按钮
        test_btn = QPushButton("测试SMTP连接")
        test_btn.clicked.connect(self.on_test_smtp)
        smtp_form.addRow("", test_btn)
        
        layout.addWidget(smtp_group)
        
        # 备份历史
        history_group = QGroupBox("备份历史")
        history_layout = QVBoxLayout(history_group)
        
        self.backup_history_text = QTextEdit()
        self.backup_history_text.setReadOnly(True)
        self.backup_history_text.setMaximumHeight(150)
        history_layout.addWidget(self.backup_history_text)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        
        return widget
    
    def create_category_tab(self) -> QWidget:
        """创建分类管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info = QLabel("管理密码分类，可以添加、编辑或删除分类")
        info.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(info)
        
        # 分类表格
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels([
            "分类名称", "颜色", "使用次数", "操作"
        ])
        self.category_table.setColumnWidth(0, 180)
        self.category_table.setColumnWidth(1, 120)
        self.category_table.setColumnWidth(2, 100)
        self.category_table.setColumnWidth(3, 100)
        # 设置默认行高
        self.category_table.verticalHeader().setDefaultSectionSize(50)
        
        # 双击编辑分类名称
        self.category_table.cellDoubleClicked.connect(self.on_category_cell_double_clicked)
        
        layout.addWidget(self.category_table)
        
        # 添加按钮
        add_btn = QPushButton("➕ 添加新分类")
        add_btn.clicked.connect(self.on_add_category)
        layout.addWidget(add_btn)
        
        self.load_categories()
        
        return widget
    
    def create_custom_field_tab(self) -> QWidget:
        """创建自定义字段管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info = QLabel("管理自定义字段，所有密码条目将显示相同的自定义字段")
        info.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(info)
        
        # 字段表格
        self.field_table = QTableWidget()
        self.field_table.setColumnCount(4)
        self.field_table.setHorizontalHeaderLabels([
            "字段名称", "类型", "使用情况", "操作"
        ])
        self.field_table.setColumnWidth(0, 200)
        self.field_table.setColumnWidth(1, 100)
        self.field_table.setColumnWidth(2, 150)
        self.field_table.setColumnWidth(3, 100)
        # 设置默认行高
        self.field_table.verticalHeader().setDefaultSectionSize(50)
        
        layout.addWidget(self.field_table)
        
        # 添加按钮
        add_btn = QPushButton("➕ 添加自定义字段")
        add_btn.clicked.connect(self.on_add_custom_field)
        layout.addWidget(add_btn)
        
        # 提示
        note = QLabel("注：删除字段前会检查使用情况，有数据使用的字段无法删除")
        note.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
        layout.addWidget(note)
        
        self.load_custom_fields()
        
        return widget
    
    def load_settings(self):
        """加载设置"""
        # 加载通用设置
        confirm_delete = self.db.get_setting('confirm_delete', '1')
        self.confirm_delete_check.setChecked(confirm_delete == '1')
        
        default_sort = self.db.get_setting('default_sort', 'created_at_desc')
        sort_map = {
            'created_at_desc': 0,
            'created_at_asc': 1,
            'updated_at_desc': 2,
            'updated_at_asc': 3,
            'site_name_asc': 4,
            'site_name_desc': 5
        }
        self.default_sort_combo.setCurrentIndex(sort_map.get(default_sort, 0))
        
        # 加载显示设置
        show_password = self.db.get_setting('show_password', '1')
        self.show_password_check.setChecked(show_password == '1')
        
        # 加载显示列设置
        self.show_account.setChecked(self.db.get_setting('show_account', '1') == '1')
        self.show_password.setChecked(self.db.get_setting('show_password_column', '1') == '1')
        self.show_category.setChecked(self.db.get_setting('show_category', '1') == '1')
        self.show_register_date.setChecked(self.db.get_setting('show_register_date', '1') == '1')
        self.show_url.setChecked(self.db.get_setting('show_url', '0') == '1')
        self.show_phone.setChecked(self.db.get_setting('show_phone', '0') == '1')
        self.show_email.setChecked(self.db.get_setting('show_email', '0') == '1')
        
        # 加载SMTP设置
        self.smtp_server_input.setText(self.db.get_setting('smtp_server', ''))
        self.smtp_port_input.setValue(int(self.db.get_setting('smtp_port', '465')))
        self.smtp_email_input.setText(self.db.get_setting('smtp_email', ''))
        self.smtp_password_input.setText(self.db.get_setting('smtp_password', ''))
        self.backup_email_input.setText(self.db.get_setting('backup_email', ''))
        
        # 加载备份历史
        self.load_backup_history()
    
    def load_backup_history(self):
        """加载备份历史"""
        history = self.db.get_backup_history(10)
        text = ""
        for item in history:
            status_icon = "✅" if item.status == "success" else "❌"
            text += f"{status_icon} {item.backup_time} | {item.backup_type} | {item.status}\n"
            if item.message:
                text += f"   {item.message}\n"
            text += "\n"
        
        if not text:
            text = "暂无备份记录"
        
        self.backup_history_text.setPlainText(text)
    
    def load_categories(self):
        """加载分类列表"""
        categories = self.db.get_all_categories()
        self.category_table.setRowCount(0)
        
        for idx, cat in enumerate(categories):
            self.category_table.insertRow(idx)
            
            # 分类名称
            self.category_table.setItem(idx, 0, QTableWidgetItem(cat.name))
            
            # 颜色（显示为色块）
            color_widget = QWidget()
            color_layout = QHBoxLayout(color_widget)
            color_layout.setContentsMargins(10, 5, 10, 5)
            
            color_btn = QPushButton("")
            color_btn.setStyleSheet(f"background-color: {cat.color}; border: 1px solid #ccc;")
            color_btn.setFixedHeight(30)
            color_btn.setToolTip(f"点击修改颜色\n当前颜色: {cat.color}")
            color_btn.clicked.connect(lambda checked, c=cat: self.on_change_category_color(c))
            
            color_layout.addWidget(color_btn)
            self.category_table.setCellWidget(idx, 1, color_widget)
            
            # 使用次数
            count = self.db.get_category_usage_count(cat.name)
            self.category_table.setItem(idx, 2, QTableWidgetItem(f"{count} 条"))
            
            # 操作按钮
            self.create_category_action_buttons(idx, cat, count)
    
    def create_category_action_buttons(self, row: int, category: Category, usage_count: int):
        """创建分类操作按钮"""
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(10, 5, 10, 5)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedWidth(60)
        delete_btn.setFixedHeight(30)
        delete_btn.setObjectName("deleteButton")
        
        if category.is_default or usage_count > 0:
            delete_btn.setEnabled(False)
            if category.is_default:
                delete_btn.setToolTip("默认分类不能删除")
            else:
                delete_btn.setToolTip(f"有{usage_count}条密码使用此分类，无法删除")
        else:
            delete_btn.clicked.connect(lambda: self.on_delete_category(category.id))
        
        btn_layout.addWidget(delete_btn)
        
        self.category_table.setCellWidget(row, 3, btn_widget)
    
    def load_custom_fields(self):
        """加载自定义字段列表"""
        fields = self.db.get_all_custom_fields()
        self.field_table.setRowCount(0)
        
        for idx, field in enumerate(fields):
            self.field_table.insertRow(idx)
            
            # 字段名称
            self.field_table.setItem(idx, 0, QTableWidgetItem(field.field_name))
            
            # 类型
            self.field_table.setItem(idx, 1, QTableWidgetItem(field.field_type))
            
            # 使用情况
            count = self.db.get_custom_field_usage_count(field.id)
            usage_text = f"已使用({count}条)" if count > 0 else "未使用"
            self.field_table.setItem(idx, 2, QTableWidgetItem(usage_text))
            
            # 操作按钮
            self.create_field_action_buttons(idx, field, count)
    
    def create_field_action_buttons(self, row: int, field: CustomField, usage_count: int):
        """创建字段操作按钮"""
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(10, 5, 10, 5)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedWidth(60)
        delete_btn.setFixedHeight(30)
        delete_btn.setObjectName("deleteButton")
        
        if usage_count > 0:
            delete_btn.setEnabled(False)
            delete_btn.setToolTip(f"有{usage_count}条密码使用此字段，无法删除")
        else:
            delete_btn.clicked.connect(lambda: self.on_delete_custom_field(field.id))
        
        btn_layout.addWidget(delete_btn)
        
        self.field_table.setCellWidget(row, 3, btn_widget)
    
    def on_add_category(self):
        """添加分类"""
        # 简单对话框
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称：")
        if ok and name:
            try:
                # 选择颜色
                color = QColorDialog.getColor()
                if color.isValid():
                    category = Category(
                        name=name,
                        color=color.name(),
                        sort_order=100
                    )
                    self.db.add_category(category)
                    self.categories_modified = True  # 标记已修改
                    QMessageBox.information(self, "成功", "分类已添加")
                    self.load_categories()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")
    
    def on_category_cell_double_clicked(self, row: int, col: int):
        """双击分类单元格"""
        # 只有第一列（分类名称）可以编辑
        if col != 0:
            return
        
        # 获取当前分类
        categories = self.db.get_all_categories()
        if row >= len(categories):
            return
        
        category = categories[row]
        old_name = category.name
        
        # 使用输入框编辑
        from PyQt5.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self,
            "编辑分类名称",
            "请输入新的分类名称：",
            text=old_name
        )
        
        if not ok or not new_name or new_name == old_name:
            return
        
        # 弹出确认对话框
        usage_count = self.db.get_category_usage_count(old_name)
        
        if usage_count > 0:
            reply = QMessageBox.question(
                self,
                "确认保存",
                f"分类名称将从 '{old_name}' 修改为 '{new_name}'\n\n"
                f"有 {usage_count} 条密码使用此分类，将同步更新。\n\n"
                f"确定要保存吗？",
                QMessageBox.Save | QMessageBox.Cancel
            )
        else:
            reply = QMessageBox.question(
                self,
                "确认保存",
                f"分类名称将从 '{old_name}' 修改为 '{new_name}'\n\n"
                f"确定要保存吗？",
                QMessageBox.Save | QMessageBox.Cancel
            )
        
        if reply == QMessageBox.Save:
            try:
                # 更新所有使用该分类的密码
                if usage_count > 0:
                    passwords = self.db.filter_by_category(old_name)
                    for pwd in passwords:
                        pwd.category = new_name
                        self.db.update_password(pwd, None)
                
                # 更新分类名称
                category.name = new_name
                self.db.update_category(category)
                self.categories_modified = True
                
                QMessageBox.information(self, "成功", "分类已更新")
                self.load_categories()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
    
    def on_change_category_color(self, category: Category):
        """更改分类颜色"""
        color = QColorDialog.getColor(QColor(category.color))
        if color.isValid():
            try:
                category.color = color.name()
                self.db.update_category(category)
                self.categories_modified = True  # 标记已修改
                self.load_categories()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
    
    def on_delete_category(self, category_id: int):
        """删除分类"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个分类吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db.delete_category(category_id)
                if success:
                    self.categories_modified = True  # 标记已修改
                    QMessageBox.information(self, "成功", "分类已删除")
                    self.load_categories()
                else:
                    QMessageBox.warning(self, "失败", "该分类正在使用中，无法删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def on_add_custom_field(self):
        """添加自定义字段"""
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "添加自定义字段", "字段名称：")
        if ok and name:
            try:
                # 获取当前字段数量作为排序
                fields = self.db.get_all_custom_fields()
                sort_order = len(fields) + 1
                
                field = CustomField(
                    field_name=name,
                    field_type='text',
                    sort_order=sort_order
                )
                self.db.add_custom_field(field)
                self.custom_fields_modified = True  # 标记已修改
                QMessageBox.information(self, "成功", "自定义字段已添加")
                self.load_custom_fields()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")
    
    def on_delete_custom_field(self, field_id: int):
        """删除自定义字段"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个自定义字段吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db.delete_custom_field(field_id)
                if success:
                    self.custom_fields_modified = True  # 标记已修改
                    QMessageBox.information(self, "成功", "字段已删除")
                    self.load_custom_fields()
                else:
                    QMessageBox.warning(self, "失败", "该字段正在使用中，无法删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def on_test_smtp(self):
        """测试SMTP连接"""
        server = self.smtp_server_input.text().strip()
        port = self.smtp_port_input.value()
        email = self.smtp_email_input.text().strip()
        password = self.smtp_password_input.text().strip()
        
        if not all([server, email, password]):
            QMessageBox.warning(self, "提示", "请填写完整的SMTP信息")
            return
        
        # 测试连接
        success, message = self.backup_manager.test_smtp_connection(
            server, port, email, password
        )
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "失败", message)
    
    def on_import_data(self):
        """导入数据"""
        if self.parent():
            self.parent().on_import_data()
        else:
            QMessageBox.warning(self, "提示", "无法调用导入功能")
    
    def on_local_backup(self):
        """本地备份"""
        if self.parent():
            self.parent().on_backup()
        else:
            QMessageBox.warning(self, "提示", "无法调用备份功能")
    
    def on_email_backup(self):
        """邮箱备份"""
        from PyQt5.QtWidgets import QFileDialog
        
        # 获取SMTP设置
        smtp_server = self.db.get_setting('smtp_server', '')
        smtp_port = int(self.db.get_setting('smtp_port', '465'))
        smtp_email = self.db.get_setting('smtp_email', '')
        smtp_password = self.db.get_setting('smtp_password', '')
        backup_email = self.db.get_setting('backup_email', '')
        
        if not all([smtp_server, smtp_email, smtp_password, backup_email]):
            QMessageBox.warning(
                self,
                "提示",
                "请先在\"备份\"标签页中配置SMTP设置"
            )
            # 切换到备份标签页
            self.tabs.setCurrentIndex(3)  # 备份标签页的索引
            return
        
        # 确认发送
        reply = QMessageBox.question(
            self,
            "确认备份",
            f"将通过邮件发送备份到：\n{backup_email}\n\n确定继续吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 获取所有密码
            passwords = self.db.get_all_passwords()
            
            if not passwords:
                QMessageBox.warning(self, "提示", "没有密码数据可以备份")
                return
            
            # 发送邮件备份
            success, message = self.backup_manager.backup_to_email(
                passwords,
                smtp_server,
                smtp_port,
                smtp_email,
                smtp_password,
                backup_email
            )
            
            if success:
                QMessageBox.information(self, "成功", "备份已发送到邮箱")
                # 刷新备份历史
                self.load_backup_history()
            else:
                QMessageBox.critical(self, "失败", f"备份失败：\n{message}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份过程中发生错误：\n{str(e)}")
    
    def on_open_recycle_bin(self):
        """打开回收站"""
        if self.parent():
            self.parent().on_open_recycle_bin()
        else:
            QMessageBox.warning(self, "提示", "无法调用回收站功能")
    
    def on_save(self):
        """保存设置"""
        try:
            # 保存通用设置
            self.db.set_setting('confirm_delete', '1' if self.confirm_delete_check.isChecked() else '0')
            
            sort_map = [
                'created_at_desc', 'created_at_asc', 'updated_at_desc',
                'updated_at_asc', 'site_name_asc', 'site_name_desc'
            ]
            self.db.set_setting('default_sort', sort_map[self.default_sort_combo.currentIndex()])
            
            # 保存显示设置
            self.db.set_setting('show_password', '1' if self.show_password_check.isChecked() else '0')
            
            # 保存显示列设置
            self.db.set_setting('show_account', '1' if self.show_account.isChecked() else '0')
            self.db.set_setting('show_password_column', '1' if self.show_password.isChecked() else '0')
            self.db.set_setting('show_category', '1' if self.show_category.isChecked() else '0')
            self.db.set_setting('show_register_date', '1' if self.show_register_date.isChecked() else '0')
            self.db.set_setting('show_url', '1' if self.show_url.isChecked() else '0')
            self.db.set_setting('show_phone', '1' if self.show_phone.isChecked() else '0')
            self.db.set_setting('show_email', '1' if self.show_email.isChecked() else '0')
            
            # 保存SMTP设置
            self.db.set_setting('smtp_server', self.smtp_server_input.text().strip())
            self.db.set_setting('smtp_port', str(self.smtp_port_input.value()))
            self.db.set_setting('smtp_email', self.smtp_email_input.text().strip())
            self.db.set_setting('smtp_password', self.smtp_password_input.text().strip())
            self.db.set_setting('backup_email', self.backup_email_input.text().strip())
            
            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

