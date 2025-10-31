"""
主窗口 - 应用程序主界面
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QLabel,
    QHeaderView, QMessageBox, QCheckBox, QFileDialog, QApplication, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Optional
import sys

from core.database import Database
from core.models import Password
from core.backup import BackupManager
from core.data_handler import DataHandler
from core.search_engine import SearchEngine
from .styles import MAIN_WINDOW_STYLE, CATEGORY_COLORS
from .password_dialog import PasswordDialog
from .recycle_bin_dialog import RecycleBinDialog
from .settings_dialog import SettingsDialog
from .table_manager import TableManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.backup_manager = BackupManager()
        self.data_handler = DataHandler()
        self.search_engine = SearchEngine()  # 新增：搜索引擎
        
        self.passwords: List[Password] = []
        self.filtered_passwords: List[Password] = []
        self.show_password = True
        
        # 表格管理器（初始化时创建）
        self.table_manager: Optional[TableManager] = None
        
        # 排序状态变量
        self.all_selected = False
        self.current_sort_column = -1
        self.sort_ascending = True
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("密码管理工具 (Mima)")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 工具栏
        toolbar_layout = self.create_toolbar()
        main_layout.addLayout(toolbar_layout)
        
        # 密码表格
        self.table = QTableWidget()
        self.table_manager = TableManager(self.table, self.db)
        self.table_manager.set_callbacks(
            on_edit=self.on_edit_password_by_id,
            on_delete=self.on_delete_password_by_id
        )
        self.table_manager.setup_table()
        
        # 双击单元格事件（用于双击网址打开）
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        main_layout.addWidget(self.table)
        
        # 底部状态栏
        bottom_layout = self.create_bottom_bar()
        main_layout.addLayout(bottom_layout)
    
    def create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索网站、账号、邮箱...")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self.on_search)
        toolbar.addWidget(self.search_input)
        
        # 分类筛选
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类")
        self.load_categories()
        self.category_combo.currentTextChanged.connect(self.on_category_filter)
        toolbar.addWidget(self.category_combo)
        
        toolbar.addStretch()
        
        # 添加按钮（移到刷新前面）
        add_btn = QPushButton("➕ 添加")
        add_btn.clicked.connect(self.on_add_password)
        toolbar.addWidget(add_btn)
        
        # 回收站按钮
        recycle_btn = QPushButton("🗑️ 回收站")
        recycle_btn.clicked.connect(self.on_open_recycle_bin)
        recycle_btn.setToolTip("查看已删除的密码")
        toolbar.addWidget(recycle_btn)
        
        # 刷新按钮（只保留图标）
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.on_refresh_data)
        refresh_btn.setToolTip("重新加载密码列表和分类")
        toolbar.addWidget(refresh_btn)
        
        # 设置按钮
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.clicked.connect(self.on_open_settings)
        toolbar.addWidget(settings_btn)
        
        return toolbar
    
    
    def create_bottom_bar(self) -> QHBoxLayout:
        """创建底部栏"""
        bottom_layout = QHBoxLayout()
        
        # 统计信息
        self.status_label = QLabel("共 0 条记录")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 批量导出按钮
        export_btn = QPushButton("📤 批量导出选中")
        export_btn.clicked.connect(self.on_batch_export)
        bottom_layout.addWidget(export_btn)
        
        return bottom_layout
    
    def load_categories(self):
        """加载分类列表"""
        categories = self.db.get_all_categories()
        self.category_combo.clear()
        self.category_combo.addItem("全部分类")
        for cat in categories:
            self.category_combo.addItem(cat.name)
    
    def load_data(self):
        """加载密码数据"""
        self.passwords = self.db.get_all_passwords()
        self.filtered_passwords = self.passwords.copy()
        
        # 应用默认排序设置
        self.apply_default_sort()
        
        self.refresh_table()
    
    def apply_default_sort(self):
        """应用默认排序设置"""
        default_sort = self.db.get_setting('default_sort', 'created_at_desc')
        
        # 解析排序设置
        sort_map = {
            'created_at_desc': ('created_at', False),
            'created_at_asc': ('created_at', True),
            'updated_at_desc': ('updated_at', False),
            'updated_at_asc': ('updated_at', True),
            'site_name_asc': ('site_name', True),
            'site_name_desc': ('site_name', False)
        }
        
        if default_sort in sort_map:
            field, ascending = sort_map[default_sort]
            self.sort_passwords(field, ascending)
    
    def sort_passwords(self, field: str, ascending: bool = True):
        """
        对密码列表排序
        
        Args:
            field: 排序字段 (site_name, created_at, updated_at等)
            ascending: 是否升序
        """
        def get_sort_key(pwd: Password):
            value = getattr(pwd, field, '')
            # 处理None值
            if value is None:
                return '' if ascending else 'zzzzz'  # None值排在最后
            return value
        
        self.filtered_passwords.sort(key=get_sort_key, reverse=not ascending)
    
    def refresh_table(self):
        """刷新表格显示（使用TableManager）"""
        self.table_manager.set_password_visibility(self.show_password)
        self.table_manager.refresh_table(self.filtered_passwords)
        
        # 更新状态栏
        self.update_status_bar()
    
    def update_status_bar(self):
        """更新状态栏"""
        self.status_label.setText(f"共 {len(self.filtered_passwords)} 条记录")
    
    
    
    def on_search(self, keyword: str):
        """搜索（使用智能搜索引擎）"""
        current_category = self.category_combo.currentText()
        category = None if current_category == "全部分类" else current_category
        
        # 使用搜索引擎进行智能搜索
        self.filtered_passwords = self.search_engine.filter_by_multiple_criteria(
            self.passwords,
            keyword=keyword if keyword else None,
            category=category
        )
        
        self.refresh_table()
    
    def on_category_filter(self, category: str):
        """分类筛选"""
        try:
            # ⚡ 安全检查：确保表格管理器和表格对象都存在
            if not self.table_manager or not self.table:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("表格对象未初始化或已失效，跳过筛选")
                return
            
            if category == "全部分类":
                self.filtered_passwords = self.passwords.copy()
            else:
                self.filtered_passwords = self.db.filter_by_category(category)
            
            # 如果有搜索关键词，同时应用
            keyword = self.search_input.text()
            if keyword:
                self.filtered_passwords = [
                    pwd for pwd in self.filtered_passwords
                    if keyword.lower() in pwd.site_name.lower() or
                       keyword.lower() in (pwd.login_account or "").lower()
                ]
            
            self.refresh_table()
        except RuntimeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"分类筛选失败（对象已被删除）: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"分类筛选失败: {e}", exc_info=True)
    
    def on_refresh_data(self):
        """刷新数据"""
        try:
            # 重新加载分类
            self.load_categories()
            # 重新加载密码数据
            self.load_data()
            # 显示成功提示
            QMessageBox.information(self, "刷新成功", "数据已刷新！")
        except Exception as e:
            QMessageBox.critical(self, "刷新失败", f"刷新数据时出错：{str(e)}")
    
    def on_add_password(self):
        """添加密码"""
        dialog = PasswordDialog(self)
        if dialog.exec_() == PasswordDialog.Accepted:
            self.load_data()
    
    def on_edit_password_by_id(self, password_id: int):
        """根据ID编辑密码"""
        password = self.db.get_password(password_id)
        if password:
            dialog = PasswordDialog(self, password)
            if dialog.exec_() == PasswordDialog.Accepted:
                self.load_data()
    
    def on_copy_password(self, password_id: int):
        """复制密码到剪贴板"""
        password = self.db.get_password(password_id)
        if password:
            clipboard = QApplication.clipboard()
            clipboard.setText(password.password)
            QMessageBox.information(self, "成功", "密码已复制到剪贴板")
    
    def on_batch_export(self):
        """批量导出选中项"""
        # 获取选中的行
        selected_passwords = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    if row < len(self.filtered_passwords):
                        selected_passwords.append(self.filtered_passwords[row])
        
        if not selected_passwords:
            QMessageBox.warning(self, "提示", "请先选择要导出的密码记录")
            return
        
        # 选择导出格式和路径
        file_filter = "Excel文件 (*.xlsx);;CSV文件 (*.csv);;JSON文件 (*.json)"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出密码",
            "",
            file_filter
        )
        
        if file_path:
            try:
                if "xlsx" in selected_filter:
                    self.data_handler.export_to_excel(selected_passwords, file_path)
                elif "csv" in selected_filter:
                    self.data_handler.export_to_csv(selected_passwords, file_path)
                elif "json" in selected_filter:
                    self.data_handler.export_to_json(selected_passwords, file_path)
                
                QMessageBox.information(
                    self,
                    "成功",
                    f"已导出 {len(selected_passwords)} 条记录"
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def on_open_recycle_bin(self):
        """打开回收站"""
        dialog = RecycleBinDialog(self)
        dialog.exec_()
    
    def on_open_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self)
        result = dialog.exec_()
        
        # 如果保存了设置，重新加载并重建表格
        if result == SettingsDialog.Accepted:
            # 重新加载设置
            show_password = self.db.get_setting('show_password', '1')
            self.show_password = (show_password == '1')
            self.load_categories()
            
            # 重新创建表格以反映新的列配置
            old_table = self.table
            self.create_password_table()
            
            # 替换中心部件中的表格
            layout = self.centralWidget().layout()
            layout.replaceWidget(old_table, self.table)
            old_table.deleteLater()
            
            # 刷新表格数据
            self.refresh_table()
        elif dialog.categories_modified or dialog.custom_fields_modified:
            # 如果只修改了分类或字段，只需刷新
            self.load_categories()
            self.refresh_table()
    
    def on_backup(self):
        """备份"""
        # 选择备份方式
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择备份方式")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请选择备份方式：")
        layout.addWidget(label)
        
        email_btn = QPushButton("📧 邮件备份")
        email_btn.clicked.connect(lambda: self.do_email_backup(dialog))
        layout.addWidget(email_btn)
        
        local_btn = QPushButton("💾 本地备份")
        local_btn.clicked.connect(lambda: self.do_local_backup(dialog))
        layout.addWidget(local_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.exec_()
    
    def do_email_backup(self, dialog):
        """执行邮件备份"""
        dialog.accept()
        
        # 获取SMTP设置
        smtp_server = self.db.get_setting('smtp_server', '')
        smtp_port = int(self.db.get_setting('smtp_port', '465'))
        smtp_email = self.db.get_setting('smtp_email', '')
        smtp_password = self.db.get_setting('smtp_password', '')
        backup_email = self.db.get_setting('backup_email', '')
        
        if not all([smtp_server, smtp_email, smtp_password, backup_email]):
            QMessageBox.warning(
                self,
                "配置不完整",
                "请先在设置中配置SMTP邮箱信息"
            )
            return
        
        # 获取所有密码
        passwords = self.db.get_all_passwords()
        
        if not passwords:
            QMessageBox.information(self, "提示", "没有可备份的数据")
            return
        
        # 显示进度提示
        QMessageBox.information(
            self,
            "备份中",
            "正在发送邮件备份，请稍候..."
        )
        
        # 执行备份
        success, message = self.backup_manager.backup_to_email(
            passwords,
            smtp_server,
            smtp_port,
            smtp_email,
            smtp_password,
            backup_email
        )
        
        # 记录备份历史
        from core.models import BackupHistory
        from datetime import datetime
        
        history = BackupHistory(
            backup_type='email',
            file_path=backup_email,
            status='success' if success else 'failed',
            message=message
        )
        self.db.add_backup_history(history)
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "失败", message)
    
    def do_local_backup(self, dialog):
        """执行本地备份"""
        dialog.accept()
        
        # 选择保存目录
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择备份保存目录",
            ""
        )
        
        if not directory:
            return
        
        # 获取所有密码
        passwords = self.db.get_all_passwords()
        
        if not passwords:
            QMessageBox.information(self, "提示", "没有可备份的数据")
            return
        
        try:
            # 执行备份（Excel格式）
            file_path = self.backup_manager.backup_to_local(
                passwords,
                directory,
                'excel'
            )
            
            # 记录备份历史
            from core.models import BackupHistory
            
            history = BackupHistory(
                backup_type='local',
                file_path=file_path,
                status='success',
                message=f'已保存到 {file_path}'
            )
            self.db.add_backup_history(history)
            
            QMessageBox.information(
                self,
                "成功",
                f"备份成功！\n文件已保存到：\n{file_path}"
            )
        except Exception as e:
            # 记录失败
            from core.models import BackupHistory
            
            history = BackupHistory(
                backup_type='local',
                file_path=directory,
                status='failed',
                message=str(e)
            )
            self.db.add_backup_history(history)
            
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")
    
    def on_import_data(self):
        """导入数据"""
        # 选择文件
        file_filter = "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;JSON文件 (*.json)"
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            "导入密码数据",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        try:
            # 导入数据
            if "xlsx" in selected_filter.lower() or "xls" in selected_filter.lower():
                data = self.data_handler.import_from_excel(file_path)
            elif "csv" in selected_filter:
                data = self.data_handler.import_from_csv(file_path)
            elif "json" in selected_filter:
                data = self.data_handler.import_from_json(file_path)
            else:
                QMessageBox.warning(self, "错误", "不支持的文件格式")
                return
            
            # 验证数据
            valid_data, errors = self.data_handler.validate_import_data(data)
            
            if errors:
                error_msg = "\n".join(errors[:10])  # 只显示前10个错误
                if len(errors) > 10:
                    error_msg += f"\n... 还有 {len(errors) - 10} 个错误"
                
                QMessageBox.warning(
                    self,
                    "数据验证",
                    f"发现 {len(errors)} 条无效数据将被跳过：\n{error_msg}"
                )
            
            if not valid_data:
                QMessageBox.warning(self, "导入失败", "没有有效的数据可以导入")
                return
            
            # 检查重复数据
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QButtonGroup
            
            duplicate_dialog = QDialog(self)
            duplicate_dialog.setWindowTitle("导入选项")
            duplicate_dialog.setMinimumWidth(350)
            
            layout = QVBoxLayout(duplicate_dialog)
            
            label = QLabel(f"共 {len(valid_data)} 条有效数据\n\n如果遇到重复数据（网站名称+登录账号相同），如何处理？")
            label.setWordWrap(True)
            layout.addWidget(label)
            
            button_group = QButtonGroup(duplicate_dialog)
            
            skip_radio = QRadioButton("跳过重复的（保留现有数据）")
            skip_radio.setChecked(True)
            button_group.addButton(skip_radio, 1)
            layout.addWidget(skip_radio)
            
            overwrite_radio = QRadioButton("覆盖重复的（用导入数据更新）")
            button_group.addButton(overwrite_radio, 2)
            layout.addWidget(overwrite_radio)
            
            import_all_radio = QRadioButton("全部导入（允许重复）")
            button_group.addButton(import_all_radio, 3)
            layout.addWidget(import_all_radio)
            
            from PyQt5.QtWidgets import QDialogButtonBox
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(duplicate_dialog.accept)
            buttons.rejected.connect(duplicate_dialog.reject)
            layout.addWidget(buttons)
            
            if duplicate_dialog.exec_() != QDialog.Accepted:
                return
            
            # 执行导入
            import_mode = button_group.checkedId()
            imported_count = 0
            skipped_count = 0
            updated_count = 0
            
            # ⚡ 性能优化：在循环外查询一次所有密码
            all_passwords = self.db.get_all_passwords() if import_mode in [1, 2] else []
            
            for item in valid_data:
                # 检查是否重复
                existing = None
                if import_mode in [1, 2]:  # 需要检查重复
                    site_name = item.get('site_name')
                    login_account = item.get('login_account', '')
                    
                    # 查找是否已存在
                    for pwd in all_passwords:
                        if pwd.site_name == site_name and pwd.login_account == login_account:
                            existing = pwd
                            break
                
                if existing and import_mode == 1:
                    # 跳过
                    skipped_count += 1
                    continue
                elif existing and import_mode == 2:
                    # 覆盖
                    existing.url = item.get('url', '')
                    existing.password = item.get('password', '')
                    existing.phone = item.get('phone', '')
                    existing.email = item.get('email', '')
                    existing.category = item.get('category', '')
                    existing.notes = item.get('notes', '')
                    existing.register_date = item.get('register_date')
                    existing.custom_fields = item.get('custom_fields', {})
                    
                    self.db.update_password(existing, None)
                    updated_count += 1
                else:
                    # 新增
                    pwd = Password.from_dict(item)
                    self.db.add_password(pwd)
                    imported_count += 1
            
            # 显示结果
            result_msg = f"导入完成！\n"
            if imported_count > 0:
                result_msg += f"新增：{imported_count} 条\n"
            if updated_count > 0:
                result_msg += f"更新：{updated_count} 条\n"
            if skipped_count > 0:
                result_msg += f"跳过：{skipped_count} 条\n"
            
            QMessageBox.information(self, "导入成功", result_msg)
            
            # 刷新列表
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入过程中发生错误：\n{str(e)}")
    
    def on_select_all(self):
        """全选所有复选框"""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def on_deselect_all(self):
        """取消全选"""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def on_invert_selection(self):
        """反选"""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(not checkbox.isChecked())
    
    
    # ==================== TableManager 回调方法 ====================
    
    def on_edit_password_by_id(self, password_id: int):
        """通过ID编辑密码"""
        dialog = PasswordDialog(self, self.db.get_password(password_id))
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def on_delete_password_by_id(self, password_id: int):
        """通过ID删除密码"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条密码吗？\n密码将被移至回收站",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_password(password_id, soft_delete=True)
            self.load_data()
            QMessageBox.information(self, "成功", "密码已移至回收站")
    
    def on_cell_double_clicked(self, row: int, col: int):
        """双击单元格事件（用于双击网址打开）"""
        # 获取列配置
        visible_columns = self.table_manager.visible_columns
        if col >= len(visible_columns):
            return
        
        col_key = visible_columns[col]["key"]
        
        # 如果是网址列
        if col_key == "url":
            item = self.table.item(row, col)
            if item and item.text():
                url = item.text()
                self.on_open_url(url)
    
    def on_open_url(self, url: str):
        """打开URL"""
        import webbrowser
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开网址: {str(e)}")

