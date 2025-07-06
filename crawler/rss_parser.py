#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RSS解析器：提供标准化的RSS内容提取功能
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# 尝试导入crawl4ai集成模块
try:
    from crawler.crawl4ai_integration import crawl4ai
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logger.warning("无法导入crawl4ai集成模块，将使用传统方法")


def extract_rss_entry(entry: Any, feed: Any = None, feed_url: str = "") -> Dict[str, Any]:
    """
    从RSS条目中提取标准化的信息
    
    参数:
        entry: feedparser解析后的单个条目
        feed: feedparser解析后的feed对象（可选）
        feed_url: RSS源的URL（可选）
        
    返回:
        包含标准化信息的字典
    """
    result = {
        "title": "",
        "link": "",
        "author": "未知作者",
        "published": "",
        "content": "",
        "summary": ""
    }
    
    # 1. 提取标题
    result["title"] = _extract_title(entry)
    
    # 2. 提取链接
    result["link"] = _extract_link(entry)
    
    # 3. 提取作者
    result["author"] = _extract_author(entry, feed, feed_url)
    
    # 4. 提取发布时间
    pub_time = _extract_publish_time(entry)
    if pub_time:
        result["published"] = pub_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 5. 提取内容
    result["content"] = _extract_content(entry)
    
    # 6. 使用crawl4ai增强内容获取
    if CRAWL4AI_AVAILABLE and crawl4ai.is_enabled():
        result["content"] = _enhance_content_with_crawl4ai(entry, result["content"], result["link"])
    
    # 7. 提取摘要
    result["summary"] = _extract_summary(entry)
    
    return result


def _extract_title(entry: Any) -> str:
    """
    提取标题
    """
    if not hasattr(entry, 'title'):
        return "无标题"
    
    title = entry.title
    
    # 处理标题是字典的情况
    if isinstance(title, dict) and 'value' in title:
        title = title.value
    
    # 处理CDATA标签
    if isinstance(title, str) and title.startswith('<![CDATA[') and title.endswith(']]>'):
        title = title[9:-3]  # 去除CDATA标签
    
    return title


def _extract_link(entry: Any) -> str:
    """
    提取链接
    """
    if not hasattr(entry, 'link'):
        return ""
    
    # 处理链接是字符串的情况
    if isinstance(entry.link, str):
        return entry.link
    
    # 处理链接是字典的情况（Atom格式常见）
    if isinstance(entry.link, dict) and 'href' in entry.link:
        return entry.link.href
    
    # 处理链接是列表的情况
    if isinstance(entry.link, list) and len(entry.link) > 0:
        for link_item in entry.link:
            if isinstance(link_item, dict) and 'href' in link_item:
                # 优先选择rel="alternate"的链接
                if link_item.get('rel') == 'alternate':
                    return link_item['href']
        # 如果没有找到rel="alternate"，使用第一个有href的链接
        for link_item in entry.link:
            if isinstance(link_item, dict) and 'href' in link_item:
                return link_item['href']
    
    # 尝试其他可能的属性
    if hasattr(entry, 'links') and isinstance(entry.links, list):
        for link_item in entry.links:
            if isinstance(link_item, dict) and 'href' in link_item:
                return link_item['href']
    
    return ""


def _extract_author(entry: Any, feed: Any = None, feed_url: str = "") -> str:
    """
    提取作者信息
    """
    # 检查是否是werss.tuber.cc的微信公众号RSS源
    is_wechat_rss = feed_url and "werss.tuber.cc" in feed_url
    
    if is_wechat_rss:
        # 对于微信公众号RSS源，如果没有author字段，使用feed的title作为作者
        if not hasattr(entry, 'author') or not entry.author:
            if feed and hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                wechat_author = feed.feed.title
                logger.info(f"检测到微信公众号RSS源，使用feed标题作为作者: {wechat_author}")
                return wechat_author
    
    # 标准的author字段处理
    if not hasattr(entry, 'author') or not entry.author:
        return "未知作者"
    
    # 处理作者是字典的情况（Atom格式常见）
    if isinstance(entry.author, dict) and 'name' in entry.author:
        return entry.author.name
    
    # 处理作者是字符串的情况
    return str(entry.author)


def _extract_publish_time(entry: Any) -> Optional[datetime]:
    """
    提取发布时间
    """
    # 首选published_parsed字段
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime.fromtimestamp(time.mktime(entry.published_parsed))
    
    # 其次使用updated_parsed字段
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime.fromtimestamp(time.mktime(entry.updated_parsed))
    
    # 如果feedparser无法解析，尝试手动解析时间字段
    # 先尝试published字段
    if hasattr(entry, 'published') and entry.published:
        try:
            from dateutil.parser import parse
            parsed_time = parse(entry.published.strip())
            logger.info(f"手动解析published字段成功: {parsed_time}")
            return parsed_time
        except Exception as e:
            logger.debug(f"手动解析published字段失败: {e}")
    
    # 再尝试updated字段（微信公众号常用）
    if hasattr(entry, 'updated') and entry.updated:
        try:
            from dateutil.parser import parse
            parsed_time = parse(entry.updated.strip())
            logger.info(f"手动解析updated字段成功: {parsed_time}")
            return parsed_time
        except Exception as e:
            logger.debug(f"手动解析updated字段失败: {e}")
    
    return None


def _extract_content(entry: Any) -> str:
    """
    提取内容，优先级：
    1. content字段
    2. content:encoded字段
    3. description字段（对于机器之心等特殊源）
    4. summary字段（对于机器之心等特殊源）
    """
    # 1. 尝试从content字段获取内容
    if hasattr(entry, 'content') and entry.content:
        content_value = ""
        
        # 处理content是列表的情况
        if isinstance(entry.content, list) and len(entry.content) > 0:
            content_item = entry.content[0]
            
            # 处理content_item是字典的情况
            if isinstance(content_item, dict) and 'value' in content_item:
                content_value = content_item['value']
            # 处理content_item有value属性的情况
            elif hasattr(content_item, 'value'):
                content_value = content_item.value
            # 其他情况，转为字符串
            else:
                content_value = str(content_item)
            
            if content_value and len(content_value.strip()) > 20:
                return content_value
    
    # 2. 尝试从content:encoded字段获取内容
    content_encoded = None
    
    # 直接作为属性
    if hasattr(entry, 'content_encoded'):
        content_encoded = entry.content_encoded
    # 作为字典项
    elif hasattr(entry, 'get') and callable(getattr(entry, 'get')) and entry.get('content_encoded'):
        content_encoded = entry.get('content_encoded')
    
    if content_encoded:
        # 处理CDATA标签
        if isinstance(content_encoded, str) and content_encoded.startswith('<![CDATA[') and content_encoded.endswith(']]>'):
            content_encoded = content_encoded[9:-3]
        
        if len(content_encoded.strip()) > 20:
            return content_encoded
    
    # 3. 尝试从description字段获取内容（对机器之心等特殊源有效）
    if hasattr(entry, 'description') and entry.description:
        desc = entry.description
        # 处理CDATA标签
        if isinstance(desc, str) and desc.startswith('<![CDATA[') and desc.endswith(']]>'):
            desc = desc[9:-3]
        
        if len(desc.strip()) > 20:
            return desc
    
    # 4. 尝试从summary字段获取内容（对机器之心等特殊源有效）
    if hasattr(entry, 'summary') and entry.summary:
        summary = entry.summary
        # 处理CDATA标签
        if isinstance(summary, str) and summary.startswith('<![CDATA[') and summary.endswith(']]>'):
            summary = summary[9:-3]
        
        if len(summary.strip()) > 20:
            return summary
    
    # 5. 尝试从source字段获取内容（对机器之心等特殊源有效）
    if hasattr(entry, 'source') and isinstance(entry.source, dict):
        # 检查source字段中的title
        if 'title' in entry.source and entry.source['title']:
            # 对于机器之心，我们可以使用标题作为内容的一部分
            return f"来源: {entry.source['title']}，标题: {entry.title if hasattr(entry, 'title') else '无标题'}"
        
        # 检查source字段中的value
        if 'value' in entry.source and entry.source['value']:
            source_value = entry.source['value']
            if len(source_value.strip()) > 20:
                return source_value
    
    return ""


def _enhance_content_with_crawl4ai(entry: Any, existing_content: str, article_url: str) -> str:
    """
    使用crawl4ai增强内容获取
    
    参数:
        entry: RSS条目
        existing_content: 现有内容
        article_url: 文章链接
        
    返回:
        增强后的内容
    """
    if not CRAWL4AI_AVAILABLE:
        return existing_content
    
    # 检查是否可以使用crawl4ai（优先使用启用状态，备用方案检查配置）
    can_use_crawl4ai = crawl4ai.is_enabled() or crawl4ai.is_available_as_fallback()
    if not can_use_crawl4ai:
        return existing_content
    
    # 判断是否需要使用crawl4ai增强内容
    should_enhance = False
    
    # 1. 内容过短（少于100字符）
    if len(existing_content.strip()) < 100:
        should_enhance = True
        logger.info(f"内容过短({len(existing_content)}字符)，使用crawl4ai增强: {article_url}")
    
    # 2. 特殊RSS源（已知内容获取困难的源）
    problem_domains = [
        "jiqizhixin.com",  # 机器之心
        "openai.com",      # OpenAI
        "deepmind.google", # Google DeepMind
        "research.facebook.com", # Meta Research
        "marktechpost.com", # MarkTechPost
    ]
    
    for domain in problem_domains:
        if domain in article_url:
            should_enhance = True
            logger.info(f"检测到问题域名({domain})，使用crawl4ai增强: {article_url}")
            break
    
    # 3. 内容看起来像是截断的（以...结尾或包含"阅读全文"等关键词）
    if existing_content and (
        existing_content.strip().endswith("...") or 
        existing_content.strip().endswith("…") or
        "阅读全文" in existing_content or
        "Read more" in existing_content or
        "查看原文" in existing_content
    ):
        should_enhance = True
        logger.info(f"内容疑似截断，使用crawl4ai增强: {article_url}")
    
    if not should_enhance:
        return existing_content
    
    # 使用crawl4ai获取完整内容
    if not article_url:
        logger.warning("文章链接为空，无法使用crawl4ai增强")
        return existing_content
    
    try:
        # 根据优先级决定调用方式
        is_fallback = not crawl4ai.is_enabled()
        if is_fallback:
            logger.info(f"开始使用crawl4ai作为备用方案增强内容: {article_url}")
        else:
            logger.info(f"开始使用crawl4ai增强内容: {article_url}")
        
        result = crawl4ai.crawl_webpage(article_url, anti_bot=True, as_fallback=is_fallback)
        
        if result["success"] and result["content"]:
            enhanced_content = result["content"]
            method = "备用方案" if is_fallback else "主要方案"
            logger.info(f"crawl4ai增强成功({method}): {article_url}, 原内容{len(existing_content)}字符 -> 增强后{len(enhanced_content)}字符")
            return enhanced_content
        else:
            method = "备用方案" if is_fallback else "主要方案"
            logger.warning(f"crawl4ai增强失败({method}): {article_url}, 错误: {result.get('error', '未知错误')}")
            return existing_content
            
    except Exception as e:
        method = "备用方案" if is_fallback else "主要方案"
        logger.error(f"使用crawl4ai增强内容时出错({method}): {article_url}, 错误: {str(e)}")
        return existing_content


def _extract_summary(entry: Any) -> str:
    """
    提取摘要
    """
    if not hasattr(entry, 'summary'):
        return ""
    
    summary = entry.summary
    
    # 处理summary是字典的情况
    if isinstance(summary, dict) and 'value' in summary:
        summary = summary['value']
    
    # 处理CDATA标签
    if isinstance(summary, str) and summary.startswith('<![CDATA[') and summary.endswith(']]>'):
        summary = summary[9:-3]
    
    # 如果摘要为空，尝试使用description字段
    if not summary or len(summary.strip()) < 20:
        if hasattr(entry, 'description') and entry.description:
            desc = entry.description
            if isinstance(desc, str) and desc.startswith('<![CDATA[') and desc.endswith(']]>'):
                desc = desc[9:-3]
            if len(desc.strip()) > 20:
                return desc
    
    return summary