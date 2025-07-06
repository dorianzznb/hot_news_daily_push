#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crawl4AI 集成模块：封装 Crawl4AI API 调用逻辑
支持RSS获取和网页内容提取，作为传统爬虫的替代方案
"""

import requests
import json
import time
import logging
import re
from typing import Dict, Any, Optional, List, Union
from config.config import (
    CRAWL4AI_ENABLED, 
    CRAWL4AI_API_URL, 
    CRAWL4AI_API_TOKEN, 
    CRAWL4AI_TIMEOUT, 
    CRAWL4AI_MAX_RETRIES
)

logger = logging.getLogger(__name__)


class Crawl4AIIntegration:
    """
    Crawl4AI 集成类，提供统一的API接口
    """
    
    def __init__(self):
        self.enabled = CRAWL4AI_ENABLED
        self.api_url = CRAWL4AI_API_URL
        self.api_token = CRAWL4AI_API_TOKEN
        self.timeout = CRAWL4AI_TIMEOUT
        self.max_retries = CRAWL4AI_MAX_RETRIES
        
    def is_enabled(self) -> bool:
        """检查crawl4ai是否已启用"""
        return self.enabled
    
    def is_available_as_fallback(self) -> bool:
        """检查crawl4ai是否可以作为备用方案使用"""
        # 即使CRAWL4AI_ENABLED为False，只要有API配置就可以作为备用方案
        return bool(self.api_url and self.api_token)
    
    def crawl_url(self, url: str, formats: List[str] = None, 
                  extract_content: bool = True, 
                  wait_for_content: bool = False, 
                  as_fallback: bool = False) -> Dict[str, Any]:
        """
        使用Crawl4AI爬取单个URL
        
        参数:
            url: 要爬取的URL
            formats: 返回格式列表，默认['markdown', 'html']
            extract_content: 是否提取内容
            wait_for_content: 是否等待内容加载完成
            as_fallback: 是否作为备用方案调用
            
        返回:
            包含爬取结果的字典
        """
        if not self.enabled and not as_fallback:
            logger.warning("Crawl4AI未启用，跳过爬取")
            return {"success": False, "error": "Crawl4AI未启用"}
        
        if not self.is_available_as_fallback():
            logger.warning("Crawl4AI配置不完整，无法使用")
            return {"success": False, "error": "Crawl4AI配置不完整"}
        
        if formats is None:
            formats = ["markdown", "html"]
        
        # 构建请求数据
        request_data = {
            "urls": [url],
            "formats": formats
        }
        
        # 根据参数添加额外配置
        if extract_content:
            request_data["extra"] = {
                "word_count_threshold": 1,
                "only_text": False
            }
        
        if wait_for_content:
            request_data["crawler_params"] = {
                "headless": True,
                "page_timeout": 30000,
                "wait_for": "js:() => document.readyState === 'complete'"
            }
        
        return self._make_request(request_data)
    
    def crawl_rss(self, rss_url: str, as_fallback: bool = False) -> Dict[str, Any]:
        """
        使用Crawl4AI爬取RSS源
        
        参数:
            rss_url: RSS源的URL
            as_fallback: 是否作为备用方案调用
            
        返回:
            包含RSS内容的字典
        """
        if not self.enabled and not as_fallback:
            logger.warning("Crawl4AI未启用，跳过RSS爬取")
            return {"success": False, "error": "Crawl4AI未启用"}
        
        if not self.is_available_as_fallback():
            logger.warning("Crawl4AI配置不完整，无法使用")
            return {"success": False, "error": "Crawl4AI配置不完整"}
        
        logger.info(f"使用Crawl4AI爬取RSS: {rss_url}")
        
        # 为RSS源设置特殊参数
        request_data = {
            "urls": [rss_url],
            "formats": ["markdown", "html"],
            "extra": {
                "word_count_threshold": 1,
                "only_text": False
            }
        }
        
        return self._make_request(request_data)
    
    def crawl_webpage(self, url: str, anti_bot: bool = True, as_fallback: bool = False) -> Dict[str, Any]:
        """
        使用Crawl4AI爬取网页内容
        
        参数:
            url: 要爬取的网页URL
            anti_bot: 是否启用反爬虫措施
            as_fallback: 是否作为备用方案调用
            
        返回:
            包含网页内容的字典
        """
        if not self.enabled and not as_fallback:
            logger.warning("Crawl4AI未启用，跳过网页爬取")
            return {"success": False, "error": "Crawl4AI未启用"}
        
        if not self.is_available_as_fallback():
            logger.warning("Crawl4AI配置不完整，无法使用")
            return {"success": False, "error": "Crawl4AI配置不完整"}
        
        logger.info(f"使用Crawl4AI爬取网页: {url}")
        
        # 构建请求数据
        request_data = {
            "urls": [url],
            "formats": ["markdown", "html"],
            "extra": {
                "word_count_threshold": 1,
                "only_text": False
            }
        }
        
        # 如果启用反爬虫措施，添加相应配置
        if anti_bot:
            request_data["crawler_params"] = {
                "headless": True,
                "simulate_user": True,
                "magic": True,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "page_timeout": 30000
            }
        
        return self._make_request(request_data)
    
    def _detect_anti_bot(self, response_text: str, status_code: int = None) -> bool:
        """
        检测反爬机制
        
        参数:
            response_text: 响应内容
            status_code: HTTP状态码
            
        返回:
            是否检测到反爬机制
        """
        if not response_text:
            return False
        
        # 检查HTTP状态码
        if status_code in [403, 429, 503]:
            logger.warning(f"检测到反爬状态码: {status_code}")
            return True
        
        # 检查响应内容中的反爬关键词
        anti_bot_keywords = [
            "cloudflare",
            "captcha",
            "验证码",
            "robot",
            "blocked",
            "access denied",
            "please enable javascript",
            "challenge",
            "ray id",
            "checking your browser",
            "ddos protection",
            "security check",
            "please wait",
            "please verify",
            "human verification",
            "too many requests",
            "rate limit",
            "suspicious activity",
            "anti-bot",
            "cf-browser-verification",
            "cf-ray",
            "iuam-challenge",
            "just a moment",
            "enable cookies",
            "enable javascript",
            "turnstile",
            "hcaptcha",
            "recaptcha",
            "geetest",
            "滑动验证",
            "点击验证",
            "拖拽验证",
            "请滑动",
            "请点击",
            "安全验证",
            "异常访问",
            "访问受限",
            "请稍等",
            "正在验证",
            "人机验证",
            "系统检测",
            "请开启javascript",
            "请开启cookie",
            "浏览器验证",
        ]
        
        response_lower = response_text.lower()
        for keyword in anti_bot_keywords:
            if keyword in response_lower:
                logger.warning(f"检测到反爬关键词: {keyword}")
                return True
        
        return False
    
    def _make_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送请求到Crawl4AI API
        
        参数:
            request_data: 请求数据
            
        返回:
            API响应结果
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        crawl_url = f"{self.api_url}/crawl"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"向Crawl4AI发送请求 (尝试 {attempt + 1}/{self.max_retries})")
                
                # 发送爬取请求
                response = requests.post(
                    crawl_url,
                    headers=headers,
                    json=request_data,
                    timeout=self.timeout
                )
                
                # 检测反爬机制
                if self._detect_anti_bot(response.text, response.status_code):
                    logger.warning("检测到反爬机制，跳过重试")
                    return {"success": False, "error": "检测到反爬机制（Cloudflare/验证码）"}
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # 检查result是否为None
                        if result is None:
                            error_msg = f"API返回空响应，状态码: {response.status_code}"
                            logger.error(error_msg)
                            logger.debug(f"响应内容: {response.text}")
                            if attempt == self.max_retries - 1:
                                return {"success": False, "error": error_msg}
                            continue
                        
                        # 检查返回的结果是否包含反爬信息
                        if result.get("success", False):
                            data = result.get("data") or result.get("results") or {}
                            if isinstance(data, list) and len(data) > 0:
                                data = data[0]
                            
                            # 检查返回的内容是否包含反爬信息
                            if isinstance(data, dict):
                                content = ""
                                if "markdown" in data and data["markdown"]:
                                    markdown_data = data["markdown"]
                                    if isinstance(markdown_data, dict) and "raw_markdown" in markdown_data:
                                        content = markdown_data["raw_markdown"] or ""
                                    elif isinstance(markdown_data, str):
                                        content = markdown_data
                                elif "html" in data and data["html"]:
                                    content = data["html"]
                                
                                if content and self._detect_anti_bot(content):
                                    logger.warning("检测到返回内容包含反爬信息，跳过重试")
                                    return {"success": False, "error": "返回内容包含反爬信息"}
                        
                        # 检查是否有task_id（异步任务）
                        if "task_id" in result:
                            return self._wait_for_task(result["task_id"])
                        else:
                            # 直接返回结果
                            return self._process_response(result)
                            
                    except json.JSONDecodeError as e:
                        error_msg = f"API响应JSON解析失败: {str(e)}"
                        logger.error(error_msg)
                        logger.debug(f"响应内容: {response.text}")
                        if attempt == self.max_retries - 1:
                            return {"success": False, "error": error_msg}
                        continue
                else:
                    error_msg = f"API请求失败，状态码: {response.status_code}"
                    logger.error(error_msg)
                    if attempt == self.max_retries - 1:
                        return {"success": False, "error": error_msg}
                    
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": "请求超时（可能遇到反爬）"}
                    
            except Exception as e:
                logger.error(f"请求失败: {str(e)}")
                logger.debug(f"异常详情: {type(e).__name__}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": f"请求异常: {str(e)}"}
            
            # 重试前等待
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        return {"success": False, "error": "达到最大重试次数"}
    
    def _wait_for_task(self, task_id: str) -> Dict[str, Any]:
        """
        等待异步任务完成
        
        参数:
            task_id: 任务ID
            
        返回:
            任务结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        task_url = f"{self.api_url}/task/{task_id}"
        max_wait_time = 60  # 最大等待时间（秒）
        wait_interval = 2   # 检查间隔（秒）
        waited_time = 0
        
        logger.info(f"等待Crawl4AI任务完成: {task_id}")
        
        while waited_time < max_wait_time:
            try:
                response = requests.get(task_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # 检查result是否为None
                        if result is None:
                            logger.warning(f"检查任务状态时返回空响应: {task_id}")
                            continue
                        
                        # 检查任务状态
                        if result.get("status") == "completed":
                            logger.info(f"任务完成: {task_id}")
                            return self._process_response(result)
                        elif result.get("status") == "failed":
                            error_msg = f"任务失败: {result.get('error', '未知错误')}"
                            logger.error(error_msg)
                            return {"success": False, "error": error_msg}
                        else:
                            # 任务仍在进行中
                            logger.debug(f"任务进行中: {task_id}, 状态: {result.get('status')}")
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"检查任务状态时JSON解析失败: {task_id}, 错误: {str(e)}")
                        continue
                        
                else:
                    logger.warning(f"检查任务状态失败，状态码: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"检查任务状态时出错: {str(e)}")
            
            time.sleep(wait_interval)
            waited_time += wait_interval
        
        return {"success": False, "error": "任务超时"}
    
    def _process_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理API响应结果
        
        参数:
            result: API响应结果
            
        返回:
            处理后的结果
        """
        # 检查result是否为None
        if result is None:
            return {"success": False, "error": "API响应结果为空"}
        
        if not result.get("success", False):
            return {"success": False, "error": result.get("error", "未知错误")}
        
        # 提取数据 - 支持data和results两种字段
        data = result.get("data") or result.get("results") or {}
        if isinstance(data, list) and len(data) > 0:
            data = data[0]  # 获取第一个结果
        elif not isinstance(data, dict):
            return {"success": False, "error": "响应数据格式不正确"}
        
        # 提取内容
        content = ""
        html_content = ""
        
        # 从markdown字段提取内容
        if "markdown" in data and data["markdown"]:
            markdown_data = data["markdown"]
            if isinstance(markdown_data, dict) and "raw_markdown" in markdown_data:
                content = markdown_data["raw_markdown"] or ""
            elif isinstance(markdown_data, str):
                content = markdown_data
        
        # 从html字段提取HTML内容
        if "html" in data and data["html"]:
            html_content = data["html"]
        
        # 获取其他信息
        url = data.get("url", "")
        title = data.get("title", "")
        
        # 如果没有从metadata中获取到title，尝试从markdown中提取
        if not title and "metadata" in data and data["metadata"]:
            title = data["metadata"].get("title", "")
        
        # 清理内容，去除导航栏等无用信息
        cleaned_content = self._clean_content(content, url)
        
        logger.info(f"Crawl4AI成功获取内容: {url}, 原始内容长度: {len(content)}, 清理后长度: {len(cleaned_content)}")
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "content": cleaned_content,
            "html": html_content,
            "raw_data": data
        }
    
    def _clean_content(self, content: str, url: str) -> str:
        """
        清理内容，去除导航栏、广告等无用信息
        
        参数:
            content: 原始内容
            url: 网页URL
            
        返回:
            清理后的内容
        """
        if not content:
            return content
            
        # 1. 去除常见的导航和UI元素
        navigation_patterns = [
            # 通用导航模式 - 更激进的清理
            r'\[App\]\([^)]+\).*?\[投稿\]\([^)]+\)',
            r'\[首页\]\([^)]+\).*?(?=\n|#|$)',
            r'\[登录\]\([^)]+\).*?\[注册\]\([^)]+\)',
            r'\[退出登录\].*?登录.*?搜索',
            r'\[搜索\]\([^)]+\)',
            r'\[.*?设置\]\([^)]+\)',
            r'\[.*?关注\]\([^)]+\)',
            r'\[.*?收藏\]\([^)]+\)',
            r'\[.*?申请.*?报道\]\([^)]+\)',
            r'\[退出登录\]\([^)]+\)',
            
            # 清理整行导航
            r'^.*?\[首页\].*?\[投稿\].*?$',
            r'^.*?\[登录\].*?\[注册\].*?$',
            r'^.*?\[App\].*?\[公众号\].*?$',
            r'^.*?业界.*?手机.*?电脑.*?测评.*?视频.*?AI.*?苹果.*?$',
            r'^.*?36氪Auto.*?数字时氪.*?未来消费.*?智能涌现.*?$',
            r'^.*?首页.*?AI Coding NEW.*?沸点.*?课程.*?直播.*?活动.*?AI刷题.*?$',
            
            # IT之家特殊模式
            r'\[App\]\([^)]+\)\s*\[公众号\]\([^)]+\)\s*\[投稿\]\([^)]+\)\s*\[.*?\]\([^)]+\)\s*\[顶部\]\([^)]+\)',
            r'!\[\]\([^)]*svg[^)]*\)',  # SVG图标
            r'\[.*?之家\]\([^)]+\)',
            r'\[软媒.*?\]\([^)]+\)',
            r'\[要知App\]\([^)]+\)',
            r'\[软媒魔方\]\([^)]+\)',
            r'热搜：.*?(?=\n|\[|$)',
            r'搜索.*?(?=\n|\[|$)',
            r'日夜间\s*随系统\s*浅色\s*深色',
            r'主题色\s*黑色',
            r'\[最会买\]\([^)]+\)',
            r'\[RSS订阅\]\([^)]+\)',
            r'\[App客户端\]\([^)]+\)',
            
            # 36氪特殊模式 - 更全面
            r'\[\]\([^)]*36kr[^)]*\)',
            r'\[36氪Auto\]\([^)]+\)',
            r'\[数字时氪\]\([^)]+\)',
            r'\[未来消费\]\([^)]+\)',
            r'\[智能涌现\]\([^)]+\)',
            r'\[未来城市\]\([^)]+\)',
            r'\[启动Power on\]\([^)]+\)',
            r'\[36氪出海\]\([^)]+\)',
            r'\[36氪研究院\]\([^)]+\)',
            r'\[潮生TIDE\]\([^)]+\)',
            r'\[36氪企服点评\]\([^)]+\)',
            r'\[36氪财经\]\([^)]+\)',
            r'\[职场bonus\]\([^)]+\)',
            r'\[36碳\]\([^)]+\)',
            r'\[后浪研究所\]\([^)]+\)',
            r'\[暗涌Waves\]\([^)]+\)',
            r'\[硬氪\]\([^)]+\)',
            r'媒体品牌.*?(?=\n|$)',
            r'企业服务.*?(?=\n|$)',
            r'政府服务.*?(?=\n|$)',
            r'投资人服务.*?(?=\n|$)',
            r'创业者服务.*?(?=\n|$)',
            r'创投平台.*?(?=\n|$)',
            
            # 掘金特殊模式 - 更全面
            r'稀土掘金.*?(?=\n|$)',
            r'\[\s*AI Coding NEW\]\([^)]+\)',
            r'\[\s*沸点\s*\]\([^)]+\)',
            r'\[\s*课程\s*\]\([^)]+\)',
            r'\[\s*直播\s*\]\([^)]+\)',
            r'\[\s*活动\s*\]\([^)]+\)',
            r'\[\s*AI刷题\s*\]\([^)]+\)',
            r'\[\s*APP\s*\]\([^)]+\)',
            r'\[插件\]\([^)]+\)',
            r'创作者中心.*?(?=\n|$)',
            r'写文章.*?草稿箱.*?(?=\n|$)',
            r'搜索历史\s*清空',
            r'vip.*?会员',
            r'首次.*?免费领取',
            
            # 通用链接和引用模式
            r'!\[.*?\]\([^)]+\)',  # 图片链接
            r'\[.*?\]\(javascript:.*?\)',  # JavaScript链接
            r'\[.*?\]\(#.*?\)',  # 锚点链接
            r'\[.*?\]\([^)]*\.(svg|png|jpg|jpeg|gif|ico)[^)]*\)',  # 图片文件链接
            r'\[.*?\]\([^)]*img[^)]*\)',  # 包含img的链接
        ]
        
        # 应用导航模式清理
        cleaned_content = content
        for pattern in navigation_patterns:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.MULTILINE)
        
        # 2. 去除重复的链接和标记
        link_patterns = [
            r'(\[.*?\]\([^)]+\))\s*\1+',  # 重复的链接
            r'(\*\s*){3,}',  # 连续的星号
            r'(\[\s*\]){2,}',  # 连续的空链接
        ]
        
        for pattern in link_patterns:
            cleaned_content = re.sub(pattern, r'\1', cleaned_content)
        
        # 3. 清理特定网站的内容
        if "ithome.com" in url:
            cleaned_content = self._clean_ithome_content(cleaned_content)
        elif "36kr.com" in url:
            cleaned_content = self._clean_36kr_content(cleaned_content)
        elif "juejin.cn" in url:
            cleaned_content = self._clean_juejin_content(cleaned_content)
        
        # 4. 通用清理
        cleaned_content = self._general_content_cleanup(cleaned_content)
        
        return cleaned_content
    
    def _clean_ithome_content(self, content: str) -> str:
        """清理IT之家特有的内容"""
        patterns = [
            r'业界\s*手机\s*电脑\s*测评\s*视频\s*AI\s*苹果\s*iPhone\s*鸿蒙\s*软件\s*智车\s*数码\s*学院\s*游戏\s*直播\s*5G\s*微软\s*Win10\s*Win11\s*专题',
            r'感谢IT之家网友.*?的线索投递',
            r'IT之家\s*\d+\s*月\s*\d+\s*日消息',
            r'责编：.*?(?=\n|$)',
            r'作者：.*?(?=\n|$)',
            r'来源：.*?(?=\n|$)',
            r'\d{4}/\d{1,2}/\d{1,2}\s*\d{1,2}:\d{1,2}:\d{1,2}',  # 时间戳
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content
    
    def _clean_36kr_content(self, content: str) -> str:
        """清理36氪特有的内容"""
        patterns = [
            # 清理整个导航栏块
            r'退出登录.*?登录.*?(?=\n|$)',
            r'企业号.*?36Kr创新咨询.*?(?=\n|$)',
            r'核心服务.*?城市之窗.*?(?=\n|$)',
            r'创投发布.*?投资人认证.*?(?=\n|$)',
            r'寻求报道.*?创投氪堂.*?企业入驻.*?(?=\n|$)',
            
            # 清理资讯分类导航
            r'快讯.*?资讯.*?推荐.*?财经.*?AI.*?自助报道.*?(?=\n|$)',
            r'最新.*?创投.*?汽车.*?科技.*?专精特新.*?视频.*?专题.*?(?=\n|$)',
            
            # 清理城市导航
            r'广东.*?江苏.*?四川.*?河南.*?湖北.*?安徽.*?(?=\n|$)',
            r'海南.*?浙江.*?陕西.*?重庆.*?山东.*?湖南.*?贵州.*?(?=\n|$)',
            
            # 清理业务服务链接
            r'\[企业号\].*?\[企服点评\].*?\[36Kr研究院\].*?\[36Kr创新咨询\].*?(?=\n|$)',
            r'\[核心服务\].*?\[城市之窗\].*?(?=\n|$)',
            r'\[创投发布\].*?\[投资人认证\].*?(?=\n|$)',
            r'\[寻求报道\].*?\[创投氪堂\].*?\[企业入驻\].*?(?=\n|$)',
            
            # 清理资讯分类链接
            r'\[快讯\].*?\[资讯\].*?\[推荐\].*?\[财经\].*?\[AI\].*?\[自助报道\].*?(?=\n|$)',
            r'\[最新\].*?\[创投\].*?\[汽车\].*?\[科技\].*?\[专精特新\].*?\[视频\].*?\[专题\].*?(?=\n|$)',
            
            # 清理城市链接
            r'\[广东\].*?\[江苏\].*?\[四川\].*?\[河南\].*?\[湖北\].*?\[安徽\].*?(?=\n|$)',
            r'\[海南\].*?\[浙江\].*?\[陕西\].*?\[重庆\].*?\[山东\].*?\[湖南\].*?\[贵州\].*?(?=\n|$)',
            
            # 清理顶部操作链接
            r'\[寻求报道\].*?我要入驻.*?\[城市合作\].*?(?=\n|$)',
            
            # 清理推广广告链接
            r'\[即刻报名.*?\].*?TrustDecision.*?(?=\n|$)',
            r'\[.*?&NIQ.*?\].*?(?=\n|$)',
            r'adx\.36kr\.com.*?(?=\n|$)',
            
            # 清理文章推荐链接
            r'\[OpenAI宫斗.*?\].*?(?=\n|$)',
            r'\[再融700亿.*?\].*?(?=\n|$)',
            r'\[2025过半.*?\].*?(?=\n|$)',
            r'\[36氪广东首发.*?\].*?(?=\n|$)',
            r'\[独家.*?\].*?(?=\n|$)',
            
            # 清理业务服务相关
            r'数字时氪.*?暗涌Waves.*?硬氪',
            r'企业号.*?创业者服务',
            r'核心服务.*?政府服务',
            r'创投发布.*?投资人服务',
            r'寻求报道.*?创业者服务',
            r'创投平台.*?(?=\n|$)',
            
            # 清理媒体品牌和服务
            r'36氪财经.*?职场bonus.*?36碳.*?后浪研究所.*?(?=\n|$)',
            r'媒体品牌.*?(?=\n|$)',
            r'企业服务.*?(?=\n|$)',
            r'政府服务.*?(?=\n|$)',
            r'投资人服务.*?(?=\n|$)',
            r'创业者服务.*?(?=\n|$)',
            
            # 清理底部推荐内容
            r'最新文章.*?推荐.*?(?=\n|$)',
            r'来自主题：.*?(?=\n|$)',
            
            # 清理特定的链接和标识
            r'\[.*?首发.*?\].*?(?=\n|$)',
            r'\[.*?独家.*?\].*?(?=\n|$)',
            r'城市\s*\*\s*(?=\n|$)',
            r'退出登录\s*登录\s*\*\s*(?=\n|$)',
            
            # 清理参数和签名
            r'sign=.*?&param\..*?(?=\n|$)',
            r'param\.redirectUrl=.*?(?=\n|$)',
            r'param\.adsdk=.*?(?=\n|$)',
            r'\.t=\d+.*?(?=\n|$)',
            
            # 清理时间戳和URL参数
            r'https://.*?\.36kr\.com/.*?(?=\s|\n|$)',
            r'https://.*?adx\.36kr\.com/.*?(?=\s|\n|$)',
            r'https://.*?topics\.36kr\.com/.*?(?=\s|\n|$)',
            r'https://.*?pitchhub\.36kr\.com/.*?(?=\s|\n|$)',
            r'https://.*?innovation\.36kr\.com/.*?(?=\s|\n|$)',
            r'https://.*?36dianping\.com/.*?(?=\s|\n|$)',
            r'https://.*?q\.36kr\.com/.*?(?=\s|\n|$)',
            
            # 清理空链接和占位符
            r'\[\s*\]\([^)]*\)',
            r'\[\s*\]\s*\[\s*\]\s*\[\s*\]',
            r'ttps://.*?(?=\s|\n|$)',  # 没有h的链接
            r'http://www\.bjjubao\.org\.cn/.*?(?=\s|\n|$)',
            
            # 清理多余的符号
            r'\*\s*\*\s*\*\s*',
            r'[\[\]]{3,}',
            r'[*]{3,}',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content
    
    def _clean_juejin_content(self, content: str) -> str:
        """清理掘金特有的内容"""
        patterns = [
            r'首页\s*AI Coding NEW\s*沸点\s*课程\s*直播\s*活动\s*AI刷题',
            r'APP\s*插件',
            r'创作者中心\s*写文章\s*发沸点\s*写笔记\s*写代码\s*草稿箱',
            r'创作灵感\s*查看更多',
            r'vip\s*会员',
            r'首次\s*免费领取',
            r'关注\s*阅读\d+分钟',
            r'体验AI代码助手\s*复制代码',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content
    
    def _general_content_cleanup(self, content: str) -> str:
        """通用内容清理"""
        # 1. 去除多余的空行
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # 2. 去除行首行尾的多余空格
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            # 跳过只包含链接或符号的行
            if cleaned_line and not re.match(r'^[\[\]().\*\-\s]*$', cleaned_line):
                cleaned_lines.append(cleaned_line)
        
        # 3. 重新组合内容
        cleaned_content = '\n'.join(cleaned_lines)
        
        # 4. 去除开头和结尾的多余空白
        cleaned_content = cleaned_content.strip()
        
        # 5. 如果清理后内容过短，返回原始内容
        if len(cleaned_content) < len(content) * 0.3:  # 如果清理后内容少于原始内容的30%
            logger.warning("内容清理后过短，返回原始内容")
            return content
        
        return cleaned_content


# 创建全局实例
crawl4ai = Crawl4AIIntegration()


def crawl_url_with_fallback(url: str, traditional_func, *args, **kwargs) -> tuple:
    """
    使用Crawl4AI爬取URL，失败时回退到传统方法
    遵循优先级：启用时优先使用，否则可作为备用方案
    
    参数:
        url: 要爬取的URL
        traditional_func: 传统爬取函数
        *args, **kwargs: 传递给传统函数的参数
        
    返回:
        (content, html_content) 元组
    """
    # 检查是否启用crawl4ai作为主要方案
    if crawl4ai.is_enabled():
        try:
            result = crawl4ai.crawl_webpage(url)
            if result["success"]:
                return result["content"], result["html"]
            else:
                error_msg = result.get("error", "")
                # 检查是否为反爬错误，如果是则直接跳过
                if "反爬" in error_msg or "Cloudflare" in error_msg or "验证码" in error_msg or "请求超时（可能遇到反爬）" in error_msg:
                    logger.warning(f"Crawl4AI检测到反爬机制，跳过URL: {url}")
                    return "", ""  # 返回空内容，跳过这个URL
                logger.warning(f"Crawl4AI爬取失败: {error_msg}, 回退到传统方法")
        except Exception as e:
            logger.error(f"Crawl4AI爬取出错: {str(e)}, 回退到传统方法")
    
    # 尝试传统方法
    try:
        return traditional_func(url, *args, **kwargs)
    except Exception as e:
        logger.error(f"传统方法爬取失败: {str(e)}")
        
        # 如果传统方法失败，且crawl4ai可作为备用方案，则尝试使用
        if crawl4ai.is_available_as_fallback() and not crawl4ai.is_enabled():
            logger.info(f"传统方法失败，尝试使用crawl4ai作为备用方案: {url}")
            try:
                result = crawl4ai.crawl_webpage(url, as_fallback=True)
                if result["success"]:
                    logger.info(f"crawl4ai备用方案成功: {url}")
                    return result["content"], result["html"]
                else:
                    logger.warning(f"crawl4ai备用方案也失败: {url}, 错误: {result.get('error', '未知错误')}")
            except Exception as e2:
                logger.error(f"crawl4ai备用方案出错: {url}, 错误: {str(e2)}")
        
        # 返回空内容
        return "", ""


def fetch_rss_with_fallback(rss_url: str, traditional_func, *args, **kwargs) -> str:
    """
    使用Crawl4AI获取RSS内容，失败时回退到传统方法
    遵循优先级：启用时优先使用，否则可作为备用方案
    
    参数:
        rss_url: RSS源URL
        traditional_func: 传统RSS获取函数
        *args, **kwargs: 传递给传统函数的参数
        
    返回:
        RSS内容字符串
    """
    # 检查是否启用crawl4ai作为主要方案
    if crawl4ai.is_enabled():
        try:
            result = crawl4ai.crawl_rss(rss_url)
            if result["success"]:
                # 返回HTML内容供feedparser解析
                return result["html"]
            else:
                error_msg = result.get("error", "")
                # 检查是否为反爬错误，如果是则直接跳过
                if "反爬" in error_msg or "Cloudflare" in error_msg or "验证码" in error_msg or "请求超时（可能遇到反爬）" in error_msg:
                    logger.warning(f"Crawl4AI检测到反爬机制，跳过RSS: {rss_url}")
                    return ""  # 返回空内容，跳过这个RSS
                logger.warning(f"Crawl4AI获取RSS失败: {error_msg}, 回退到传统方法")
        except Exception as e:
            logger.error(f"Crawl4AI获取RSS出错: {str(e)}, 回退到传统方法")
    
    # 尝试传统方法
    try:
        return traditional_func(rss_url, *args, **kwargs)
    except Exception as e:
        logger.error(f"传统方法获取RSS失败: {str(e)}")
        
        # 如果传统方法失败，且crawl4ai可作为备用方案，则尝试使用
        if crawl4ai.is_available_as_fallback() and not crawl4ai.is_enabled():
            logger.info(f"传统方法失败，尝试使用crawl4ai作为备用方案获取RSS: {rss_url}")
            try:
                result = crawl4ai.crawl_rss(rss_url, as_fallback=True)
                if result["success"]:
                    logger.info(f"crawl4ai备用方案成功获取RSS: {rss_url}")
                    return result["html"]
                else:
                    logger.warning(f"crawl4ai备用方案也失败: {rss_url}, 错误: {result.get('error', '未知错误')}")
            except Exception as e2:
                logger.error(f"crawl4ai备用方案出错: {rss_url}, 错误: {str(e2)}")
        
        # 返回空内容
        return "" 