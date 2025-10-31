"""
数据导入导出模块 - 处理CSV/JSON/Excel格式的导入导出
"""
import json
import csv
import pandas as pd
from typing import List, Dict, Any, Tuple
from .models import Password


class DataHandler:
    """数据处理器"""
    
    def export_to_csv(self, passwords: List[Password], file_path: str):
        """导出为CSV格式"""
        if not passwords:
            raise ValueError("没有要导出的数据")
        
        # 准备数据
        data = []
        for pwd in passwords:
            row = {
                '网站名称': pwd.site_name,
                '网址': pwd.url,
                '登录账号': pwd.login_account,
                '密码': pwd.password,
                '手机号': pwd.phone,
                '邮箱': pwd.email,
                '分类': pwd.category,
                '备注': pwd.notes,
                '注册时间': pwd.register_date,
                '创建时间': pwd.created_at,
                '最后修改时间': pwd.updated_at
            }
            
            # 添加自定义字段
            for field_name, value in pwd.custom_fields.items():
                row[field_name] = value
            
            data.append(row)
        
        # 使用pandas导出
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # utf-8-sig for Excel compatibility
    
    def export_to_json(self, passwords: List[Password], file_path: str):
        """导出为JSON格式"""
        data = [pwd.to_dict() for pwd in passwords]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def export_to_excel(self, passwords: List[Password], file_path: str):
        """导出为Excel格式"""
        if not passwords:
            raise ValueError("没有要导出的数据")
        
        # 准备数据
        data = []
        for pwd in passwords:
            row = {
                '网站名称': pwd.site_name,
                '网址': pwd.url,
                '登录账号': pwd.login_account,
                '密码': pwd.password,
                '手机号': pwd.phone,
                '邮箱': pwd.email,
                '分类': pwd.category,
                '备注': pwd.notes,
                '注册时间': pwd.register_date,
                '创建时间': pwd.created_at,
                '最后修改时间': pwd.updated_at
            }
            
            # 添加自定义字段
            for field_name, value in pwd.custom_fields.items():
                row[field_name] = value
            
            data.append(row)
        
        # 使用pandas导出为Excel
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, engine='openpyxl')
    
    def import_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """从CSV导入数据"""
        data = []
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 字段映射
            field_mapping = {
                '网站名称': 'site_name',
                '网址': 'url',
                '登录账号': 'login_account',
                '密码': 'password',
                '手机号': 'phone',
                '邮箱': 'email',
                '分类': 'category',
                '备注': 'notes',
                '注册时间': 'register_date'
            }
            
            for _, row in df.iterrows():
                pwd_data = {}
                custom_fields = {}
                
                for col_name, value in row.items():
                    if pd.isna(value):
                        value = ''
                    else:
                        value = str(value)
                    
                    if col_name in field_mapping:
                        pwd_data[field_mapping[col_name]] = value
                    elif col_name not in ['创建时间', '最后修改时间']:
                        # 其他字段作为自定义字段
                        custom_fields[col_name] = value
                
                if custom_fields:
                    pwd_data['custom_fields'] = custom_fields
                
                data.append(pwd_data)
            
            return data
        except Exception as e:
            raise Exception(f"CSV导入失败: {str(e)}")
    
    def import_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """从JSON导入数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON格式错误：应为数组格式")
            
            return data
        except Exception as e:
            raise Exception(f"JSON导入失败: {str(e)}")
    
    def import_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """从Excel导入数据"""
        data = []
        
        try:
            # 使用openpyxl引擎读取Excel文件，支持.xlsx和.xls格式
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 字段映射
            field_mapping = {
                '网站名称': 'site_name',
                '网址': 'url',
                '登录账号': 'login_account',
                '密码': 'password',
                '手机号': 'phone',
                '邮箱': 'email',
                '分类': 'category',
                '备注': 'notes',
                '注册时间': 'register_date'
            }
            
            for _, row in df.iterrows():
                pwd_data = {}
                custom_fields = {}
                
                for col_name, value in row.items():
                    if pd.isna(value):
                        value = ''
                    else:
                        value = str(value)
                    
                    if col_name in field_mapping:
                        pwd_data[field_mapping[col_name]] = value
                    elif col_name not in ['创建时间', '最后修改时间']:
                        # 其他字段作为自定义字段
                        custom_fields[col_name] = value
                
                if custom_fields:
                    pwd_data['custom_fields'] = custom_fields
                
                data.append(pwd_data)
            
            return data
        except Exception as e:
            raise Exception(f"Excel导入失败: {str(e)}")
    
    def validate_import_data(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[str]]:
        """
        验证导入数据
        
        Returns:
            (有效数据列表, 错误信息列表)
        """
        valid_data = []
        errors = []
        
        for idx, item in enumerate(data, 1):
            # 检查必填字段
            if not item.get('site_name'):
                errors.append(f"第 {idx} 条：缺少网站名称")
                continue
            
            if not item.get('password'):
                errors.append(f"第 {idx} 条：缺少密码")
                continue
            
            valid_data.append(item)
        
        return valid_data, errors

