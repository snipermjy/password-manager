"""
备份模块 - 邮件备份和本地备份
"""
import smtplib
import os
import tempfile
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import List, Tuple, Optional
from .models import Password, BackupHistory
from .data_handler import DataHandler
from .config import BackupConfig

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.data_handler = DataHandler()
    
    def backup_to_local(self, passwords: List[Password], directory: str, file_format: str = 'excel') -> str:
        """
        本地备份
        
        Args:
            passwords: 密码列表
            directory: 保存目录
            file_format: 文件格式 (excel, csv, json)
        
        Returns:
            备份文件路径
        """
        # 创建文件名
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        if file_format == 'excel':
            filename = f"密码备份_{timestamp}.xlsx"
            file_path = os.path.join(directory, filename)
            self.data_handler.export_to_excel(passwords, file_path)
        elif file_format == 'csv':
            filename = f"密码备份_{timestamp}.csv"
            file_path = os.path.join(directory, filename)
            self.data_handler.export_to_csv(passwords, file_path)
        elif file_format == 'json':
            filename = f"密码备份_{timestamp}.json"
            file_path = os.path.join(directory, filename)
            self.data_handler.export_to_json(passwords, file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")
        
        return file_path
    
    def backup_to_email(self,
                       passwords: List[Password],
                       smtp_server: str,
                       smtp_port: int,
                       smtp_email: str,
                       smtp_password: str,
                       backup_email: str) -> Tuple[bool, str]:
        """
        邮件备份
        
        Returns:
            (是否成功, 消息)
        """
        temp_file: Optional[str] = None  # 在try之前初始化，避免finally块错误
        server: Optional[smtplib.SMTP] = None  # 确保server能在finally中访问
        
        try:
            # 生成临时Excel文件（使用系统临时目录）
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            temp_dir = tempfile.gettempdir()
            filename = f"{BackupConfig.TEMP_FILE_PREFIX}{timestamp}.xlsx"
            temp_file = os.path.join(temp_dir, filename)
            
            logger.info(f"创建临时备份文件: {temp_file}")
            self.data_handler.export_to_excel(passwords, temp_file)
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = backup_email
            msg['Subject'] = f'密码备份 - {timestamp}'
            
            # 邮件正文
            body = f"""
这是您的密码管理工具自动备份。

备份时间：{timestamp}
备份数量：{len(passwords)} 条

请妥善保管此备份文件。

---
密码管理工具 (Mima)
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加Excel附件（修复：只使用文件名，不使用完整路径）
            with open(temp_file, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='xlsx')
                # 只使用文件名，不包含路径
                attachment.add_header('Content-Disposition', 'attachment', 
                                    filename=os.path.basename(temp_file))
                msg.attach(attachment)
            
            # 发送邮件
            logger.info(f"连接SMTP服务器: {smtp_server}:{smtp_port}")
            if smtp_port == 465:
                # SSL
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                # TLS
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.starttls()
            
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            server.quit()
            server = None  # 标记已关闭
            
            logger.info(f"备份邮件已发送到: {backup_email}")
            return True, f"备份成功发送到 {backup_email}"
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False, "SMTP认证失败，请检查邮箱账号和授权码"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False, f"邮件发送失败: {str(e)}"
        except Exception as e:
            logger.error(f"备份失败: {e}", exc_info=True)
            return False, f"备份失败: {str(e)}"
        finally:
            # 确保SMTP连接被关闭
            if server is not None:
                try:
                    server.quit()
                except Exception as e:
                    logger.warning(f"关闭SMTP连接失败: {e}")
            
            # 确保临时文件被删除（temp_file已在try之前初始化，不会报错）
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"已删除临时文件: {temp_file}")
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")
    
    def test_smtp_connection(self,
                            smtp_server: str,
                            smtp_port: int,
                            smtp_email: str,
                            smtp_password: str) -> Tuple[bool, str]:
        """
        测试SMTP连接
        
        Returns:
            (是否成功, 消息)
        """
        server: Optional[smtplib.SMTP] = None
        
        try:
            logger.info(f"测试SMTP连接: {smtp_server}:{smtp_port}")
            
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
            
            server.login(smtp_email, smtp_password)
            server.quit()
            server = None
            
            logger.info("SMTP连接测试成功")
            return True, "SMTP连接成功"
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False, "认证失败，请检查邮箱账号和授权码"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False, f"SMTP错误: {str(e)}"
        except Exception as e:
            logger.error(f"SMTP连接失败: {e}", exc_info=True)
            return False, f"连接失败: {str(e)}"
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception as e:
                    logger.warning(f"关闭SMTP连接失败: {e}")

