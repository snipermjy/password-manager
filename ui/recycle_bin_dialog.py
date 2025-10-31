"""
回收站对话框 - 管理已删除的密码
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from typing import List

from core.database import Database
from core.models import Password
from .styles import DIALOG_STYLE


class RecycleBinDialog(QDialog):
    """回收站对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.deleted_passwords: List[Password] = []
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("回收站")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("已删除的密码记录")
        title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(title)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "网站名称", "登录账号", "删除时间", "操作"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 180)  # 操作列宽度
        
        # 设置行高
        self.table.verticalHeader().setDefaultSectionSize(50)
        
        layout.addWidget(self.table)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.status_label = QLabel("共 0 条已删除记录")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        clear_all_btn = QPushButton("清空回收站")
        clear_all_btn.setObjectName("deleteButton")
        clear_all_btn.clicked.connect(self.on_clear_all)
        bottom_layout.addWidget(clear_all_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
    
    def load_data(self):
        """加载已删除的密码"""
        self.deleted_passwords = self.db.get_deleted_passwords()
        self.refresh_table()
    
    def refresh_table(self):
        """刷新表格"""
        self.table.setRowCount(0)
        
        for idx, pwd in enumerate(self.deleted_passwords):
            self.table.insertRow(idx)
            
            # 网站名称
            self.table.setItem(idx, 0, QTableWidgetItem(pwd.site_name))
            
            # 登录账号
            self.table.setItem(idx, 1, QTableWidgetItem(pwd.login_account or ""))
            
            # 删除时间
            self.table.setItem(idx, 2, QTableWidgetItem(pwd.deleted_at or ""))
            
            # 操作按钮
            self.create_action_buttons(idx, pwd.id)
        
        # 更新状态
        self.status_label.setText(f"共 {len(self.deleted_passwords)} 条已删除记录")
    
    def create_action_buttons(self, row: int, password_id: int):
        """创建操作按钮"""
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(6, 6, 6, 6)
        btn_layout.setSpacing(6)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        # 恢复按钮
        restore_btn = QPushButton("恢复")
        restore_btn.setFixedWidth(70)
        restore_btn.setFixedHeight(32)
        restore_btn.setStyleSheet("font-size: 10pt;")
        restore_btn.clicked.connect(lambda: self.on_restore(password_id))
        btn_layout.addWidget(restore_btn)
        
        # 永久删除按钮
        delete_btn = QPushButton("永久删除")
        delete_btn.setFixedWidth(90)
        delete_btn.setFixedHeight(32)
        delete_btn.setStyleSheet("font-size: 10pt;")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.on_permanent_delete(password_id))
        btn_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 3, btn_widget)
    
    def on_restore(self, password_id: int):
        """恢复密码"""
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复这条密码记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.restore_password(password_id)
                QMessageBox.information(self, "成功", "密码已恢复")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"恢复失败: {str(e)}")
    
    def on_permanent_delete(self, password_id: int):
        """永久删除密码"""
        reply = QMessageBox.warning(
            self,
            "警告",
            "确定要永久删除这条记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_password(password_id, soft_delete=False)
                QMessageBox.information(self, "成功", "密码已永久删除")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def on_clear_all(self):
        """清空回收站"""
        if not self.deleted_passwords:
            QMessageBox.information(self, "提示", "回收站已经是空的")
            return
        
        reply = QMessageBox.warning(
            self,
            "警告",
            f"确定要清空回收站吗？\n将永久删除 {len(self.deleted_passwords)} 条记录，此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                for pwd in self.deleted_passwords:
                    self.db.delete_password(pwd.id, soft_delete=False)
                QMessageBox.information(self, "成功", "回收站已清空")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空失败: {str(e)}")

