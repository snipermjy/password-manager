"""
表格管理器 - 负责密码表格的创建、更新和管理
"""
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QCheckBox, QWidget,
    QHBoxLayout, QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt
from typing import List, Optional, Callable
import logging
from datetime import datetime

from core.models import Password
from core.database import Database

logger = logging.getLogger(__name__)


class NumericTableWidgetItem(QTableWidgetItem):
    """支持数值排序的表格项"""
    def __init__(self, text, numeric_value=None):
        super().__init__(text)
        self._numeric_value = numeric_value if numeric_value is not None else 0
    
    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self._numeric_value < other._numeric_value
        return super().__lt__(other)


class DateTableWidgetItem(QTableWidgetItem):
    """支持日期排序的表格项"""
    def __init__(self, text, date_value=None):
        super().__init__(text)
        self._date_value = date_value
    
    def __lt__(self, other):
        if isinstance(other, DateTableWidgetItem):
            if self._date_value is None and other._date_value is None:
                return False
            if self._date_value is None:
                return True
            if other._date_value is None:
                return False
            return self._date_value < other._date_value
        return super().__lt__(other)


class TableManager:
    """表格管理器"""
    
    def __init__(self, table: QTableWidget, db: Database):
        """
        初始化表格管理器
        
        Args:
            table: QTableWidget实例
            db: Database实例
        """
        self.table = table
        self.db = db
        self.visible_columns = []
        self.all_selected = False
        self.show_password = True
        
        # 回调函数
        self.on_edit_callback: Optional[Callable] = None
        self.on_delete_callback: Optional[Callable] = None
        self.on_copy_callback: Optional[Callable] = None
        self.on_open_url_callback: Optional[Callable] = None
    
    def set_callbacks(self, 
                     on_edit: Callable = None,
                     on_delete: Callable = None,
                     on_copy: Callable = None,
                     on_open_url: Callable = None):
        """设置回调函数"""
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete
        self.on_copy_callback = on_copy
        self.on_open_url_callback = on_open_url
    
    def get_visible_columns(self) -> List[dict]:
        """获取应该显示的列配置"""
        all_columns = {
            "checkbox": {"key": "checkbox", "label": "☑", "width": 50, "visible": True, "fixed": True},
            "site_name": {"key": "site_name", "label": "网站名称", "width": 150, "visible": True, "fixed": True},
            "account": {"key": "account", "label": "登录账号", "width": 150, "visible": self.db.get_setting('show_account', '1') == '1'},
            "password": {"key": "password", "label": "密码", "width": 150, "visible": self.db.get_setting('show_password_column', '1') == '1'},
            "url": {"key": "url", "label": "网址", "width": 200, "visible": self.db.get_setting('show_url', '0') == '1'},
            "phone": {"key": "phone", "label": "手机号", "width": 120, "visible": self.db.get_setting('show_phone', '0') == '1'},
            "email": {"key": "email", "label": "邮箱", "width": 150, "visible": self.db.get_setting('show_email', '0') == '1'},
            "category": {"key": "category", "label": "分类", "width": 100, "visible": self.db.get_setting('show_category', '1') == '1'},
            "register_date": {"key": "register_date", "label": "注册时间", "width": 120, "visible": self.db.get_setting('show_register_date', '1') == '1'},
            "actions": {"key": "actions", "label": "操作", "width": 140, "visible": True, "fixed": True},
        }
        
        # 获取保存的列顺序
        saved_order = self.db.get_setting('column_order', '')
        
        if saved_order:
            column_keys = saved_order.split(',')
            columns = []
            for key in column_keys:
                if key in all_columns and all_columns[key]["visible"]:
                    columns.append(all_columns[key])
            
            # 添加新增的列
            for key, col in all_columns.items():
                if col["visible"] and key not in column_keys:
                    columns.append(col)
        else:
            # 默认顺序
            default_order = ["checkbox", "site_name", "account", "password", "url", 
                           "phone", "email", "category", "register_date", "actions"]
            columns = [all_columns[key] for key in default_order 
                      if key in all_columns and all_columns[key]["visible"]]
        
        return columns
    
    def setup_table(self):
        """初始化表格"""
        self.visible_columns = self.get_visible_columns()
        
        # 设置列数和标题
        self.table.setColumnCount(len(self.visible_columns))
        headers = [col["label"] for col in self.visible_columns]
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # ⚡ 启用列头点击排序功能
        self.table.setSortingEnabled(True)
        
        # 启用列拖拽排序
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setDragEnabled(True)
        header.setDragDropMode(QHeaderView.InternalMove)
        
        # 设置列头可点击排序
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        
        # 设置列宽
        for idx, col in enumerate(self.visible_columns):
            self.table.setColumnWidth(idx, col["width"])
        
        # 设置行高
        self.table.verticalHeader().setDefaultSectionSize(50)
        
        logger.info(f"表格初始化完成，共 {len(self.visible_columns)} 列，已启用排序功能")
    
    def refresh_table(self, passwords: List[Password]):
        """刷新表格显示"""
        # ⚡ 安全检查：确保表格对象仍然有效
        try:
            if not self.table or not hasattr(self.table, 'setRowCount'):
                logger.warning("表格对象已失效，跳过刷新")
                return
            
            # ⚡ 填充数据时临时禁用排序，提高性能
            self.table.setSortingEnabled(False)
            
            self.table.setRowCount(0)
            
            for row_idx, pwd in enumerate(passwords):
                self.table.insertRow(row_idx)
                self._fill_row(row_idx, pwd)
            
            # ⚡ 填充完成后重新启用排序
            self.table.setSortingEnabled(True)
            
            logger.debug(f"表格刷新完成，共 {len(passwords)} 行")
        except RuntimeError as e:
            logger.error(f"表格刷新失败（对象已被删除）: {e}")
        except Exception as e:
            logger.error(f"表格刷新失败: {e}", exc_info=True)
    
    def _fill_row(self, row_idx: int, pwd: Password):
        """填充一行数据"""
        for col_idx, col in enumerate(self.visible_columns):
            col_key = col["key"]
            
            if col_key == "checkbox":
                self._add_checkbox(row_idx, col_idx)
            elif col_key == "site_name":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.site_name))
            elif col_key == "account":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.login_account or ""))
            elif col_key == "password":
                # ⚡ 使用密码长度进行数值排序
                password_text = pwd.password if self.show_password else "••••••••"
                password_length = len(pwd.password) if pwd.password else 0
                item = NumericTableWidgetItem(password_text, password_length)
                self.table.setItem(row_idx, col_idx, item)
            elif col_key == "url":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.url or ""))
            elif col_key == "phone":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.phone or ""))
            elif col_key == "email":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.email or ""))
            elif col_key == "category":
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(pwd.category or ""))
            elif col_key == "register_date":
                # ⚡ 使用日期对象进行排序
                date_text = pwd.register_date or ""
                date_value = None
                if pwd.register_date:
                    try:
                        # 尝试多种日期格式
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']:
                            try:
                                date_value = datetime.strptime(pwd.register_date, fmt)
                                break
                            except:
                                continue
                    except:
                        pass
                item = DateTableWidgetItem(date_text, date_value)
                self.table.setItem(row_idx, col_idx, item)
            elif col_key == "actions":
                self._add_action_buttons(row_idx, col_idx, pwd)
    
    def _add_checkbox(self, row_idx: int, col_idx: int):
        """添加复选框"""
        checkbox = QCheckBox()
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row_idx, col_idx, checkbox_widget)
    
    def _add_action_buttons(self, row_idx: int, col_idx: int, pwd: Password):
        """添加操作按钮（只保留编辑和删除）"""
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(2, 2, 2, 2)
        action_layout.setSpacing(5)
        
        # 编辑按钮样式
        edit_btn_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        
        # 删除按钮样式
        delete_btn_style = """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(55, 32)
        edit_btn.setStyleSheet(edit_btn_style)
        if self.on_edit_callback:
            edit_btn.clicked.connect(lambda: self.on_edit_callback(pwd.id))
        action_layout.addWidget(edit_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(55, 32)
        delete_btn.setStyleSheet(delete_btn_style)
        if self.on_delete_callback:
            delete_btn.clicked.connect(lambda: self.on_delete_callback(pwd.id))
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        self.table.setCellWidget(row_idx, col_idx, action_widget)
    
    def get_selected_passwords(self, passwords: List[Password]) -> List[Password]:
        """获取选中的密码"""
        selected = []
        for row_idx in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row_idx, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    if row_idx < len(passwords):
                        selected.append(passwords[row_idx])
        
        logger.debug(f"获取到 {len(selected)} 个选中的密码")
        return selected
    
    def toggle_select_all(self, passwords: List[Password]):
        """全选/取消全选"""
        self.all_selected = not self.all_selected
        
        for row_idx in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row_idx, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(self.all_selected)
        
        logger.debug(f"全选状态: {self.all_selected}")
    
    def set_password_visibility(self, visible: bool):
        """设置密码显示/隐藏"""
        self.show_password = visible
        logger.debug(f"密码显示: {visible}")

