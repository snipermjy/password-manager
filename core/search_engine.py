"""
搜索引擎模块 - 提供更智能的密码搜索和匹配功能
"""
import re
import logging
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from .models import Password
from .config import SearchConfig

logger = logging.getLogger(__name__)


class SearchEngine:
    """密码搜索引擎"""
    
    def __init__(self):
        self.field_weights = SearchConfig.FIELD_WEIGHTS
    
    def search_passwords(self, passwords: List[Password], keyword: str) -> List[Password]:
        """
        智能搜索密码
        
        Args:
            passwords: 密码列表
            keyword: 搜索关键词
            
        Returns:
            按相关度排序的密码列表
        """
        if not keyword:
            return passwords
        
        keyword = keyword.strip().lower()
        if len(keyword) < SearchConfig.MIN_KEYWORD_LENGTH:
            return passwords
        
        # 计算每个密码的相关度分数
        scored_passwords = []
        for pwd in passwords:
            score = self._calculate_relevance_score(pwd, keyword)
            if score > 0:
                scored_passwords.append((pwd, score))
        
        # 按分数降序排序
        scored_passwords.sort(key=lambda x: x[1], reverse=True)
        
        # 返回排序后的密码列表
        results = [pwd for pwd, score in scored_passwords]
        logger.info(f"搜索 '{keyword}' 找到 {len(results)} 条结果")
        
        return results[:SearchConfig.MAX_RESULTS]
    
    def _calculate_relevance_score(self, pwd: Password, keyword: str) -> float:
        """
        计算密码与关键词的相关度分数
        
        分数越高，相关度越高
        """
        score = 0.0
        
        # 检查各个字段
        fields = {
            'site_name': pwd.site_name or '',
            'login_account': pwd.login_account or '',
            'email': pwd.email or '',
            'phone': pwd.phone or '',
            'url': pwd.url or '',
            'notes': pwd.notes or ''
        }
        
        for field_name, field_value in fields.items():
            if not field_value:
                continue
                
            field_value_lower = field_value.lower()
            weight = self.field_weights.get(field_name, 1)
            
            # 完全匹配：最高分
            if keyword == field_value_lower:
                score += weight * 10
            # 开头匹配：高分
            elif field_value_lower.startswith(keyword):
                score += weight * 5
            # 包含匹配：中等分
            elif keyword in field_value_lower:
                score += weight * 3
            # 模糊匹配：低分
            elif self._fuzzy_match(keyword, field_value_lower):
                score += weight * 1
        
        return score
    
    def _fuzzy_match(self, keyword: str, text: str) -> bool:
        """
        模糊匹配（支持拼音首字母、部分字符匹配等）
        """
        # 移除空格后匹配
        if keyword.replace(' ', '') in text.replace(' ', ''):
            return True
        
        # 检查关键词的每个字符是否都在文本中（顺序不重要）
        keyword_chars = set(keyword)
        text_chars = set(text)
        if keyword_chars.issubset(text_chars):
            return True
        
        return False
    
    def match_domain(self, domain1: str, domain2: str) -> bool:
        """
        精确的域名匹配
        
        解决简单字符串包含匹配导致的误匹配问题
        例如：google.com 不应该匹配 google.com.cn
        """
        if not domain1 or not domain2:
            return False
        
        # 标准化域名（移除 www. 前缀）
        domain1 = self._normalize_domain(domain1)
        domain2 = self._normalize_domain(domain2)
        
        # 完全匹配
        if domain1 == domain2:
            return True
        
        # 检查是否是子域名关系
        if domain1.endswith('.' + domain2) or domain2.endswith('.' + domain1):
            return True
        
        return False
    
    def _normalize_domain(self, domain: str) -> str:
        """标准化域名"""
        domain = domain.lower().strip()
        
        # 如果是完整URL，提取域名
        if '://' in domain:
            try:
                parsed = urlparse(domain)
                domain = parsed.hostname or domain
            except Exception:
                pass
        
        # 移除 www. 前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    
    def find_passwords_by_domain(self, passwords: List[Password], domain: str) -> List[Password]:
        """
        根据域名查找密码（支持精确匹配）
        
        Args:
            passwords: 密码列表
            domain: 域名
            
        Returns:
            匹配的密码列表
        """
        domain = self._normalize_domain(domain)
        matched = []
        
        for pwd in passwords:
            # 检查网站名称
            if pwd.site_name and self.match_domain(domain, pwd.site_name):
                matched.append(pwd)
                continue
            
            # 检查URL
            if pwd.url:
                pwd_domain = self._normalize_domain(pwd.url)
                if self.match_domain(domain, pwd_domain):
                    matched.append(pwd)
                    continue
        
        logger.info(f"域名 '{domain}' 匹配到 {len(matched)} 条密码")
        return matched
    
    def filter_by_multiple_criteria(self, 
                                    passwords: List[Password],
                                    keyword: str = None,
                                    category: str = None,
                                    has_email: bool = None,
                                    has_phone: bool = None) -> List[Password]:
        """
        多条件筛选
        
        Args:
            passwords: 密码列表
            keyword: 搜索关键词
            category: 分类
            has_email: 是否有邮箱
            has_phone: 是否有手机号
            
        Returns:
            筛选后的密码列表
        """
        filtered = passwords
        
        # 按关键词搜索
        if keyword:
            filtered = self.search_passwords(filtered, keyword)
        
        # 按分类筛选
        if category:
            filtered = [pwd for pwd in filtered if pwd.category == category]
        
        # 按是否有邮箱筛选
        if has_email is not None:
            if has_email:
                filtered = [pwd for pwd in filtered if pwd.email]
            else:
                filtered = [pwd for pwd in filtered if not pwd.email]
        
        # 按是否有手机号筛选
        if has_phone is not None:
            if has_phone:
                filtered = [pwd for pwd in filtered if pwd.phone]
            else:
                filtered = [pwd for pwd in filtered if not pwd.phone]
        
        return filtered

