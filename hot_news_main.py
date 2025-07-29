#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主文件：调用各个函数，确保逻辑清晰
"""

import os
import sys
import asyncio
import logging
import gc  # 添加垃圾回收模块
from datetime import datetime, timedelta
from distutils.util import strtobool

# 导入配置
from config.config import (
    TECH_SOURCES, ALL_SOURCES, WEBHOOK_URL, DEEPSEEK_API_KEY, 
    HUNYUAN_API_KEY, GEMINI_API_KEY, SUMMARY_MODEL, GEMINI_MODEL_NAME, GEMINI_BASE_URL,
    BASE_URL, DEEPSEEK_API_URL, DEEPSEEK_MODEL_ID,
    RSS_URL, RSS_DAYS, TITLE_LENGTH, MAX_WORKERS, FILTER_DAYS, RSS_FEEDS
)

# 导入工具函数
from utils.utils import save_hotspots_to_jsonl, check_base_url, cleanup_old_files

# 导入数据收集模块
from crawler.data_collector import (
    collect_all_hotspots, fetch_rss_articles, filter_recent_hotspots,
    fetch_twitter_feed
)

# 导入处理模块
from processor.news_processor import process_hotspot_with_summary

# 导入LLM集成模块
from llm_integration.deepseek_integration import summarize_with_deepseek
from llm_integration.gemini_integration import summarize_with_gemini

# 导入通知模块
from notification.webhook_sender import notify, send_to_webhook
from notification.error_notifier import notify_critical_error, notify_simple_error

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def force_garbage_collection(stage_name=""):
    """
    强制执行垃圾回收并记录内存使用情况
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        before_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 强制垃圾回收
        collected = gc.collect()
        
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        freed_memory = before_memory - after_memory
        
        logger.info(f"🧹 内存清理 {stage_name}: 回收 {collected} 个对象, "
                   f"内存从 {before_memory:.1f}MB 降至 {after_memory:.1f}MB "
                   f"(释放 {freed_memory:.1f}MB)")
        
        return after_memory
    except ImportError:
        # 如果没有psutil，只执行垃圾回收
        collected = gc.collect()
        logger.info(f"🧹 内存清理 {stage_name}: 回收 {collected} 个对象")
        return None

def cleanup_variables(*variables):
    """
    清理变量并设置为None
    """
    for var_name, var_value in variables:
        if var_value is not None:
            try:
                if hasattr(var_value, 'clear') and callable(var_value.clear):
                    var_value.clear()
                del var_value
                logger.debug(f"已清理变量: {var_name}")
            except Exception as e:
                logger.debug(f"清理变量 {var_name} 时出错: {str(e)}")

def safe_main():
    """
    安全的主函数，包含完整的错误处理和通知机制
    当出现致命错误时发送错误通知而不是正常推送
    """
    # 初始内存检查
    initial_memory = force_garbage_collection("程序启动")
    
    # 动态优化缓存设置
    try:
        from utils.utils import optimize_cache_settings
        cache_settings = optimize_cache_settings()
        logger.info(f"📊 动态缓存设置: 最大缓存大小={cache_settings['max_cache_size']}, "
                   f"清理天数={cache_settings['cleanup_days']}")
        
        # 更新全局缓存设置
        import utils.utils as utils_module
        utils_module.MAX_CACHE_SIZE = cache_settings['max_cache_size']
        utils_module.CACHE_CLEANUP_DAYS = cache_settings['cleanup_days']
        
    except Exception as opt_err:
        logger.warning(f"动态缓存优化失败，使用默认设置: {opt_err}")
    
    # 检测当前内存使用情况
    try:
        from utils.utils import get_memory_usage
        memory_info = get_memory_usage()
        logger.info(f"💾 当前内存使用: RSS={memory_info['rss_mb']:.1f}MB, VMS={memory_info['vms_mb']:.1f}MB")
    except Exception as mem_err:
        logger.warning(f"获取内存信息失败: {mem_err}")
    
    # 从环境变量中读取配置，优先使用环境变量，如果不存在则使用config.py中的默认值
    tech_only = bool(strtobool(os.getenv('TECH_ONLY', 'False')))
    webhook = os.getenv('WEBHOOK_URL', WEBHOOK_URL)
    deepseek_key = os.getenv('DEEPSEEK_API_KEY', DEEPSEEK_API_KEY)
    hunyuan_key = os.getenv('HUNYUAN_API_KEY', HUNYUAN_API_KEY)
    gemini_key = os.getenv('GEMINI_API_KEY', GEMINI_API_KEY)
    summary_model = os.getenv('SUMMARY_MODEL', SUMMARY_MODEL).lower()
    gemini_model_name = os.getenv('GEMINI_MODEL_NAME', GEMINI_MODEL_NAME)
    gemini_base_url = os.getenv('GEMINI_BASE_URL', GEMINI_BASE_URL)
    no_cache = bool(strtobool(os.getenv('NO_CACHE', 'False')))
    base_url = os.getenv('BASE_URL', BASE_URL)
    deepseek_url = os.getenv('DEEPSEEK_API_URL', DEEPSEEK_API_URL)
    model_id = os.getenv('DEEPSEEK_MODEL_ID', DEEPSEEK_MODEL_ID)
    rss_url = os.getenv('RSS_URL', RSS_URL)
    rss_days = int(os.getenv('RSS_DAYS', str(RSS_DAYS)))
    title_length = int(os.getenv('TITLE_LENGTH', str(TITLE_LENGTH)))
    max_workers = int(os.getenv('MAX_WORKERS', str(MAX_WORKERS)))
    skip_content = bool(strtobool(os.getenv('SKIP_CONTENT', 'False')))
    filter_days = int(os.getenv('FILTER_DAYS', str(FILTER_DAYS)))
    
    # 检查必要的API密钥和配置
    config_errors = []
    
    if not webhook:
        config_errors.append("未提供Webhook URL")
    
    # 根据选择的总结模型检查相应的API密钥
    if summary_model == 'gemini':
        if not gemini_key:
            config_errors.append("选择了Gemini总结模型但未提供API Key")
        else:
            logger.info(f"使用Gemini模型进行总结: {gemini_model_name}")
    elif summary_model == 'deepseek':
        if not deepseek_key:
            config_errors.append("选择了DeepSeek总结模型但未提供API Key")
        else:
            logger.info("使用DeepSeek模型进行总结")
    else:
        config_errors.append(f"不支持的总结模型: {summary_model}")
    
    if not hunyuan_key and not skip_content:
        config_errors.append("未提供腾讯混元 API Key且未跳过内容处理")
    
    # 如果有配置错误，发送错误通知并退出
    if config_errors:
        error_details = {
            "配置错误列表": config_errors,
            "当前配置": {
                "SUMMARY_MODEL": summary_model,
                "TECH_ONLY": tech_only,
                "SKIP_CONTENT": skip_content,
                "有WEBHOOK_URL": bool(webhook),
                "有DEEPSEEK_API_KEY": bool(deepseek_key),
                "有GEMINI_API_KEY": bool(gemini_key),
                "有HUNYUAN_API_KEY": bool(hunyuan_key)
            }
        }
        notify_critical_error(
            "配置错误",
            f"检测到 {len(config_errors)} 个配置问题，程序无法启动",
            error_details,
            "配置检查"
        )
        logger.error("配置错误，程序退出")
        sys.exit(1)
    
    # 检查 BASE_URL 是否可访问
    try:
        if not check_base_url(base_url):
            notify_critical_error(
                "网络连接错误",
                f"BASE_URL {base_url} 不可访问",
                {"BASE_URL": base_url},
                "网络检查"
            )
            logger.error(f"BASE_URL {base_url} 不可访问，程序退出")
            sys.exit(1)
    except Exception as e:
        notify_critical_error(
            "网络检查异常",
            f"检查BASE_URL时发生异常: {str(e)}",
            {"BASE_URL": base_url, "错误": str(e)},
            "网络检查"
        )
        sys.exit(1)
    
    # 根据参数选择信息源
    sources = TECH_SOURCES if tech_only else ALL_SOURCES
    
    # 收集热点
    logger.info("🚀 开始收集热点数据...")
    hotspots = collect_all_hotspots(sources, base_url)
    
    if not hotspots:
        logger.warning("未能收集到任何热点数据，将继续尝试其他来源...")
        hotspots = [] # 确保 hotspots 是列表
    
    # 保存原始热点数据
    if hotspots:
        save_hotspots_to_jsonl(hotspots, directory=os.path.join("data", "raw")) # 指定 raw 目录
    
    # 筛选最近的热点
    hotspots = filter_recent_hotspots(hotspots, filter_days)
    
    # 保存筛选后的热点数据
    if hotspots:
        save_hotspots_to_jsonl(hotspots, directory=os.path.join("data", "filtered"))
    
    # 第一次内存清理（热点数据收集后）
    force_garbage_collection("热点数据收集后")
    
    # 获取RSS文章
    logger.info("📰 开始获取RSS文章...")
    # 优先使用RSS_FEEDS列表，如果为空则使用单个RSS_URL
    rss_articles = fetch_rss_articles(rss_url=rss_url, days=rss_days, rss_feeds=RSS_FEEDS)
    
    # --- 新增：获取 Twitter Feed ---
    logger.info("🐦 开始获取Twitter数据...")
    twitter_feed_raw = fetch_twitter_feed(days_to_fetch=2) # 获取最近2天
    
    # 过滤推文，只保留最近1天 (24小时) 的
    recent_tweets = []
    cutoff_time_tweets = datetime.now() - timedelta(days=1)
    if twitter_feed_raw:
        logger.info(f"开始过滤最近24小时的推文 (截止时间: {cutoff_time_tweets})...")
        for tweet in twitter_feed_raw:
            if tweet.get("timestamp"): # 确保有时间戳
                # Ensure timestamp is treated correctly (it's already in milliseconds from fetch_twitter_feed)
                tweet_time_ms = tweet["timestamp"]
                if isinstance(tweet_time_ms, (int, float)):
                   tweet_time = datetime.fromtimestamp(tweet_time_ms / 1000)
                   if tweet_time >= cutoff_time_tweets:
                       recent_tweets.append(tweet)
                   # else: # 可以取消注释以查看被丢弃的推文
                   #     logger.debug(f"丢弃较早的推文: {tweet['title']} @ {tweet_time}")
                else:
                   logger.warning(f"推文时间戳格式不正确: {tweet_time_ms}, 类型: {type(tweet_time_ms)}, 跳过推文: {tweet.get('title')}")

            else:
                 logger.warning(f"推文缺少时间戳，无法过滤: {tweet.get('title')}")
                 # Decide whether to include tweets without timestamps or skip them
                 # For now, we skip them to ensure only recent ones are included
                 # recent_tweets.append(tweet) # Uncomment to include tweets without timestamp

        logger.info(f"筛选后保留 {len(recent_tweets)}/{len(twitter_feed_raw)} 条最近24小时的推文。")
    # --- 结束：获取 Twitter Feed ---
    
    # 清理原始Twitter数据
    cleanup_variables(("twitter_feed_raw", twitter_feed_raw))
    
    # 给每个数据项添加来源类型标识
    for item in hotspots:
        item['data_source_type'] = 'hotspot'
    for item in rss_articles:
        item['data_source_type'] = 'rss'
    for item in recent_tweets:
        item['data_source_type'] = 'twitter'
    
    # 合并热点、RSS文章和过滤后的推文
    all_content = hotspots + rss_articles + recent_tweets # 添加 recent_tweets
    logger.info(f"合并后共有 {len(all_content)} 条内容 (包括推文)")
    
    # 第二次内存清理（数据合并后）
    force_garbage_collection("数据收集和合并后")
    
    # 检查合并后是否有内容
    if not all_content:
        notify_simple_error(
            "数据收集失败",
            "所有数据源均未获取到有效内容",
            "数据收集"
        )
        logger.error("所有来源均未获取到有效内容，程序退出")
        sys.exit(1)
    
    # 保存合并后的数据
    save_hotspots_to_jsonl(all_content, directory=os.path.join("data", "merged"))
    
    # 获取网页内容并生成摘要
    if not skip_content:
        try:
            logger.info("🤖 开始内容处理和摘要生成...")
            # 确保有事件循环
            if asyncio.get_event_loop().is_closed():
                asyncio.set_event_loop(asyncio.new_event_loop())
            
            # 使用异步方式处理所有内容，传递tech_only参数和use_cache参数
            loop = asyncio.get_event_loop()
            all_content_with_summary = loop.run_until_complete(
                process_hotspot_with_summary(all_content, hunyuan_key, max_workers, 
                                           tech_only, use_cache=not no_cache)
            )
            logger.info(f"已为 {len(all_content_with_summary)} 条内容生成摘要")
            
            # 清理原始内容数据
            cleanup_variables(("all_content", all_content))
            
        except Exception as e:
            # 内容处理失败时发送错误通知，但不退出程序，使用原始内容继续
            notify_simple_error(
                "内容处理失败",
                f"获取网页内容或生成摘要时发生错误: {str(e)}",
                "内容处理"
            )
            logger.error(f"获取网页内容或生成摘要时发生错误: {str(e)}")
            # 如果出错，继续使用原始内容
            all_content_with_summary = all_content
    else:
        all_content_with_summary = all_content
        logger.info("已跳过获取网页内容和生成摘要步骤")
    
    # 第三次内存清理（内容处理后）
    force_garbage_collection("内容处理后")
    
    # --- 新增：基于标题去重，优先保留 RSS 和 Twitter --- 
    logger.info(f"🔄 开始基于标题去重 (保留RSS/Twitter优先)，处理前数量: {len(all_content_with_summary)}")
    seen_titles = {}
    # 定义优先级：rss > twitter > hotspot
    source_priority = {'rss': 3, 'twitter': 2, 'hotspot': 1}
    
    def get_source_priority(item):
        """获取数据源优先级"""
        data_source_type = item.get('data_source_type', 'unknown')
        return source_priority.get(data_source_type, 0)
    
    def normalize_title(title):
        """标准化标题，用于更好的去重匹配"""
        if not title:
            return ""
        # 移除多余的空格和常见的标点符号
        import re
        normalized = re.sub(r'\s+', ' ', title.strip())  # 统一空格
        normalized = re.sub(r'[，。！？：；""''「」（）()【】\[\]…—]', '', normalized)  # 移除标点符号
        return normalized.lower()
    
    def titles_are_similar(title1, title2, min_prefix_length=30):
        """判断两个标题是否相似"""
        # 如果完全相同
        if title1 == title2:
            return True
            
        # 标准化后比较
        norm1 = normalize_title(title1)
        norm2 = normalize_title(title2)
        
        if norm1 == norm2:
            return True
            
        # 如果两个标题都足够长，比较前缀
        if len(norm1) >= min_prefix_length and len(norm2) >= min_prefix_length:
            prefix1 = norm1[:min_prefix_length]
            prefix2 = norm2[:min_prefix_length]
            return prefix1 == prefix2
            
        # 对于较短的标题，比较80%的相似度
        if len(norm1) < min_prefix_length or len(norm2) < min_prefix_length:
            shorter_len = min(len(norm1), len(norm2))
            if shorter_len > 10:  # 至少10个字符
                match_len = int(shorter_len * 0.8)
                return norm1[:match_len] == norm2[:match_len]
                
        return False
    
    def find_similar_title(title, seen_titles):
        """在已存在的标题中查找相似的标题"""
        for existing_title in seen_titles.keys():
            if titles_are_similar(title, existing_title):
                return existing_title
        return None
    
    for item in all_content_with_summary:
        title = item.get("title", "").strip()
        if not title: # 跳过没有标题的条目
            continue
            
        current_source = item.get("source", "")
        current_data_source_type = item.get('data_source_type', 'unknown')
        
        # 查找相似的标题
        similar_title = find_similar_title(title, seen_titles)
        
        if similar_title is None:
            # 没有找到相似的标题，直接添加
            seen_titles[title] = item
        else:
            # 找到相似的标题，进行优先级比较
            existing_item = seen_titles[similar_title]
            existing_source = existing_item.get("source", "")
            existing_data_source_type = existing_item.get('data_source_type', 'unknown')
            
            current_priority = get_source_priority(item)
            existing_priority = get_source_priority(existing_item)
            
            # 如果当前条目优先级更高，则替换
            if current_priority > existing_priority:
                logger.debug(f"去重：替换相似标题 '{similar_title}' (来自 {existing_data_source_type}:{existing_source}) 为 '{title}' (来自更高优先级 {current_data_source_type}:{current_source})")
                # 删除旧的标题，添加新的
                del seen_titles[similar_title]
                seen_titles[title] = item
            # 如果优先级相同，保留先遇到的那个
            elif current_priority == existing_priority:
                logger.debug(f"去重：保留相似标题 '{similar_title}' (来自 {existing_data_source_type}:{existing_source}), 忽略 '{title}' (来自同级 {current_data_source_type}:{current_source})")
            # 如果当前条目优先级较低，保留已存在的
            else:
                logger.debug(f"去重：保留相似标题 '{similar_title}' (来自高优先级 {existing_data_source_type}:{existing_source}), 忽略 '{title}' (来自低优先级 {current_data_source_type}:{current_source})")
                
    deduplicated_content = list(seen_titles.values())
    logger.info(f"去重后剩余数量: {len(deduplicated_content)}")
    
    # 清理去重过程中的临时数据
    cleanup_variables(("all_content_with_summary", all_content_with_summary), ("seen_titles", seen_titles))
    
    # 第四次内存清理（去重后）
    force_garbage_collection("去重处理后")
    # --- 结束：去重逻辑 ---

    # --- 新增：保存最终处理和去重后的新闻列表 ---
    logger.info(f"💾 准备保存处理和去重后的 {len(deduplicated_content)} 条新闻...")
    processed_output_dir = os.path.join("data", "processed_output")
    os.makedirs(processed_output_dir, exist_ok=True) # 确保目录存在
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    processed_filename = os.path.join(processed_output_dir, f"processed_news_{timestamp_str}.json")
    
    try:
        # 导入 json 模块（如果尚未导入）
        import json 
        with open(processed_filename, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_content, f, ensure_ascii=False, indent=4)
        logger.info(f"成功将处理后的新闻列表保存到: {processed_filename}")
    except Exception as e:
        logger.error(f"保存处理后的新闻列表到 {processed_filename} 时出错: {str(e)}")
    # --- 结束：保存逻辑 ---
    
    # AI总结阶段
    logger.info("🤖 开始AI总结阶段...")
    summary = None
    try:
        if summary_model == 'gemini':
            summary = summarize_with_gemini(deduplicated_content, gemini_key,
                                           gemini_model_name, gemini_base_url, tech_only=tech_only)
        else:  # 默认使用 DeepSeek
            summary = summarize_with_deepseek(deduplicated_content, deepseek_key,
                                             deepseek_url, model_id, tech_only=tech_only)
        
        # 检查总结结果是否有效
        # 修改验证逻辑：使用更精确的错误检测，避免误判新闻内容中的关键词
        specific_error_keywords = [
            "API错误", "API密钥", "地理位置限制", "认证失败", "权限不足", "请求错误", "连接失败", 
            "解析Gemini返回的JSON失败", "解析DeepSeek返回的JSON失败",
            "模型调用失败", "服务不可用", "配额不足", "请求超时"
        ]
        
        # 检查是否为明显的错误格式（通常错误信息比较简短且直接）
        error_patterns = [
            "失败：",  # 以"失败："开头的错误信息
            "错误：",  # 以"错误："开头的错误信息
            "Error:",  # 英文错误信息
            "Exception:",  # 异常信息
        ]
        
        is_error_response = False
        if not summary or summary.strip() == "":
            is_error_response = True
        else:
            # 检查是否包含特定的API错误关键词
            for keyword in specific_error_keywords:
                if keyword in summary:
                    is_error_response = True
                    break
            
            # 检查是否符合错误信息的格式模式
            if not is_error_response:
                summary_lower = summary.lower()
                for pattern in error_patterns:
                    if pattern.lower() in summary_lower:
                        is_error_response = True
                        break
            
            # 如果总结过短（少于50个字符），可能是错误信息
            if not is_error_response and len(summary.strip()) < 50:
                # 检查是否包含错误相关词汇且内容很短
                short_error_keywords = ["失败", "错误", "无法", "不能"]
                for keyword in short_error_keywords:
                    if keyword in summary:
                        is_error_response = True
                        break
        
        if is_error_response:
            raise Exception(f"AI总结返回无效或错误结果: {summary}")
            
    except Exception as e:
        notify_critical_error(
            "AI总结失败",
            f"AI总结阶段发生错误: {str(e)}",
            {
                "总结模型": summary_model,
                "内容数量": len(deduplicated_content),
                "错误类型": type(e).__name__
            },
            "AI总结"
        )
        logger.error(f"AI总结失败: {str(e)}")
        sys.exit(1)
    
    # 清理去重内容数据（在AI总结后）
    cleanup_variables(("deduplicated_content", deduplicated_content))
    
    # 第五次内存清理（AI总结后）
    force_garbage_collection("AI总结后")
    
    # 推送阶段
    logger.info("📤 开始推送阶段...")
    try:
        # 使用多种方式推送消息
        success = notify(summary, tech_only)
        if not success:
            # 如果所有推送方式都失败，尝试使用原始webhook方式作为备选
            logger.warning("所有配置的推送方式均失败，尝试使用原始webhook方式推送")
            fallback_success = send_to_webhook(webhook, summary, tech_only)
            if not fallback_success:
                raise Exception("所有推送方式（包括备选方案）均失败")
        
        logger.info("✅ 推送成功完成")
        
    except Exception as e:
        notify_critical_error(
            "推送失败",
            f"消息推送阶段发生错误: {str(e)}",
            {
                "推送渠道数": "多种",
                "备选webhook": bool(webhook),
                "摘要长度": len(summary) if summary else 0
            },
            "消息推送"
        )
        logger.error(f"推送失败: {str(e)}")
        sys.exit(1)
    
    # 清理阶段
    logger.info("🧹 开始清理阶段...")
    try:
        directories_to_clean = [
            "data/raw", "data/filtered", "data/merged", "data/inputs", 
            "data/outputs", "data/webhook", "cache/summary"
        ]
        days_to_keep = 7
        logger.info(f"开始清理超过 {days_to_keep} 天的旧数据...")
        for directory in directories_to_clean:
            cleanup_old_files(directory, days_to_keep=days_to_keep)
        logger.info("旧数据清理完成")
        
    except Exception as e:
        # 清理失败不是致命错误，只记录日志
        logger.error(f"清理旧数据时发生错误: {str(e)}")
        notify_simple_error(
            "清理失败",
            f"清理旧数据时发生错误: {str(e)}",
            "数据清理"
        )
    
    # 最终内存清理
    final_memory = force_garbage_collection("程序结束前")
    if initial_memory and final_memory:
        total_freed = initial_memory - final_memory
        logger.info(f"🎯 程序运行完成，总共释放内存: {total_freed:.1f}MB")
    
    logger.info("🎉 所有处理步骤完成")


def main():
    """
    主函数入口点，包含完整的错误处理和通知机制
    当出现致命错误时发送错误通知而不是正常推送
    """
    try:
        safe_main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        notify_simple_error(
            "程序中断",
            "程序被用户手动中断",
            "程序执行"
        )
        sys.exit(0)
    except SystemExit:
        # 正常退出，不需要额外处理
        raise
    except Exception as e:
        # 捕获所有未处理的异常
        notify_critical_error(
            "未知异常",
            f"程序执行过程中发生未预期的错误: {str(e)}",
            {"异常类型": type(e).__name__},
            "程序执行"
        )
        logger.error(f"程序发生未知异常: {str(e)}")
        sys.exit(1)
    finally:
        # 最终清理
        force_garbage_collection("程序异常退出")


if __name__ == "__main__":
    main()