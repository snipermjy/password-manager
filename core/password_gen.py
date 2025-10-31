"""
密码生成器模块 - 生成随机密码
"""
import random
import string
from typing import Tuple


class PasswordGenerator:
    """密码生成器"""
    
    def __init__(self):
        self.uppercase = string.ascii_uppercase  # A-Z
        self.lowercase = string.ascii_lowercase  # a-z
        self.digits = string.digits  # 0-9
        self.symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"  # 特殊符号
    
    def generate(self,
                 length: int = 12,
                 use_uppercase: bool = True,
                 use_lowercase: bool = True,
                 use_digits: bool = True,
                 use_symbols: bool = True) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度（8-32）
            use_uppercase: 是否使用大写字母
            use_lowercase: 是否使用小写字母
            use_digits: 是否使用数字
            use_symbols: 是否使用特殊符号
        
        Returns:
            生成的密码字符串
        """
        if length < 8:
            length = 8
        elif length > 32:
            length = 32
        
        # 构建字符集
        charset = ""
        if use_uppercase:
            charset += self.uppercase
        if use_lowercase:
            charset += self.lowercase
        if use_digits:
            charset += self.digits
        if use_symbols:
            charset += self.symbols
        
        # 如果没有选择任何字符类型，默认使用小写字母和数字
        if not charset:
            charset = self.lowercase + self.digits
        
        # 生成密码
        password_chars = []
        
        # 确保至少包含每种选中的字符类型
        if use_uppercase and self.uppercase:
            password_chars.append(random.choice(self.uppercase))
        if use_lowercase and self.lowercase:
            password_chars.append(random.choice(self.lowercase))
        if use_digits and self.digits:
            password_chars.append(random.choice(self.digits))
        if use_symbols and self.symbols:
            password_chars.append(random.choice(self.symbols))
        
        # 填充剩余长度
        remaining_length = length - len(password_chars)
        password_chars.extend(random.choice(charset) for _ in range(remaining_length))
        
        # 打乱顺序
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def evaluate_strength(self, password: str) -> Tuple[str, int]:
        """
        评估密码强度
        
        Returns:
            (强度描述, 强度分数0-5)
        """
        if not password:
            return "无", 0
        
        score = 0
        
        # 长度评分
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # 字符类型评分
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in self.symbols for c in password)
        
        if has_upper:
            score += 0.5
        if has_lower:
            score += 0.5
        if has_digit:
            score += 0.5
        if has_symbol:
            score += 0.5
        
        # 转换为0-5的整数分数
        score = min(int(score), 5)
        
        # 强度描述
        strength_desc = {
            0: "极弱",
            1: "弱",
            2: "一般",
            3: "中",
            4: "强",
            5: "很强"
        }
        
        return strength_desc[score], score

