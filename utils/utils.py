#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数：各种用到的工具函数
"""

import os
import hashlib
import pickle
import json
import logging
import gc  # 添加垃圾回收模块
from pathlib import Path
from datetime import datetime, timedelta
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 缓存配置常量
MAX_CACHE_SIZE = 1000  # 最大缓存条目数
CACHE_CLEANUP_DAYS = 30  # 清理超过30天的缓存条目

def save_hotspots_to_jsonl(hotspots, directory="data"):
    """
    将热点数据保存为JSONL格式，按日期组织，使用绝对路径
    """
    try:
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建绝对路径
        abs_directory = os.path.join(script_dir, directory)
        # 确保目录存在
        os.makedirs(abs_directory, exist_ok=True)
        
        # 生成文件名，使用当前日期
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = os.path.join(abs_directory, f"hotspots_{today}_{timestamp}.jsonl")
        
        # 写入JSONL文件
        with open(filename, 'w', encoding='utf-8') as f:
            for item in hotspots:
                # 添加时间戳
                item_with_timestamp = item.copy()
                item_with_timestamp['saved_at'] = datetime.now().isoformat()
                f.write(json.dumps(item_with_timestamp, ensure_ascii=False) + '\n')
        
        logger.info(f"已将 {len(hotspots)} 条热点数据保存至 {filename}")
        return filename
    except Exception as e:
        logger.error(f"保存热点数据时发生错误: {str(e)}")
        return None

def get_content_hash(content):
    """
    计算内容的哈希值，用于缓存标识
    """
    if not content:
        return None
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def cleanup_old_cache_entries(cache, max_size=MAX_CACHE_SIZE, cleanup_days=CACHE_CLEANUP_DAYS):
    """
    清理过期和过多的缓存条目
    
    参数:
        cache: 缓存字典
        max_size: 最大缓存条目数
        cleanup_days: 清理超过多少天的条目
    
    返回:
        清理后的缓存字典和清理统计信息
    """
    if not cache:
        return cache, {"removed_expired": 0, "removed_overflow": 0}
    
    original_size = len(cache)
    cutoff_time = datetime.now() - timedelta(days=cleanup_days)
    
    # 第一步：移除过期条目
    expired_keys = []
    for key, value in cache.items():
        if isinstance(value, dict) and 'created_at' in value:
            try:
                created_time = datetime.fromisoformat(value['created_at'])
                if created_time < cutoff_time:
                    expired_keys.append(key)
            except (ValueError, TypeError):
                # 如果时间解析失败，保留条目
                pass
    
    # 移除过期条目
    for key in expired_keys:
        del cache[key]
    
    removed_expired = len(expired_keys)
    
    # 第二步：如果仍然超过大小限制，移除最旧的条目
    removed_overflow = 0
    if len(cache) > max_size:
        # 按创建时间排序，移除最旧的条目
        cache_items = []
        for key, value in cache.items():
            created_time = datetime.now()  # 默认当前时间
            if isinstance(value, dict) and 'created_at' in value:
                try:
                    created_time = datetime.fromisoformat(value['created_at'])
                except (ValueError, TypeError):
                    pass
            cache_items.append((key, created_time))
        
        # 按时间排序，保留最新的max_size条目
        cache_items.sort(key=lambda x: x[1], reverse=True)
        keys_to_keep = set(item[0] for item in cache_items[:max_size])
        
        # 移除多余的条目
        keys_to_remove = [key for key in cache.keys() if key not in keys_to_keep]
        for key in keys_to_remove:
            del cache[key]
        
        removed_overflow = len(keys_to_remove)
    
    final_size = len(cache)
    stats = {
        "original_size": original_size,
        "final_size": final_size,
        "removed_expired": removed_expired,
        "removed_overflow": removed_overflow
    }
    
    if removed_expired > 0 or removed_overflow > 0:
        logger.info(f"缓存清理完成: 原始大小 {original_size}, 最终大小 {final_size}, "
                   f"移除过期 {removed_expired} 条, 移除溢出 {removed_overflow} 条")
    
    return cache, stats

def load_summary_cache(cache_dir="cache/summary"):
    """
    加载摘要缓存，同时进行清理
    """
    cache = {}
    try:
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建绝对路径
        abs_cache_dir = os.path.join(script_dir, cache_dir)
        cache_path = Path(abs_cache_dir) / "summary_cache.pkl"
        
        if not cache_path.exists():
            logger.info("摘要缓存文件不存在，创建新的空缓存")
            return {}
        
        # 检查缓存文件大小
        cache_size = cache_path.stat().st_size / 1024 / 1024  # MB
        if cache_size > 50:  # 如果缓存文件超过50MB
            logger.warning(f"缓存文件过大 ({cache_size:.1f}MB)，将在加载后进行清理")
        
        with open(cache_path, 'rb') as f:
            cache = pickle.load(f)
            logger.info(f"已加载摘要缓存，包含 {len(cache)} 条记录，文件大小: {cache_size:.1f}MB")
        
        # 自动清理缓存
        cache, cleanup_stats = cleanup_old_cache_entries(cache)
        
        # 如果进行了清理，保存清理后的缓存
        if cleanup_stats["removed_expired"] > 0 or cleanup_stats["removed_overflow"] > 0:
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache, f)
                logger.info("已保存清理后的缓存")
            except Exception as save_err:
                logger.warning(f"保存清理后的缓存失败: {str(save_err)}")
        
        return cache
        
    except Exception as e:
        logger.warning(f"加载摘要缓存失败: {str(e)}，将返回空缓存")
        return {}

def save_summary_cache(cache, cache_dir="cache/summary"):
    """
    保存摘要缓存，添加时间戳并进行清理
    """
    if not cache:
        logger.debug("缓存为空，跳过保存")
        return
    
    try:
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建绝对路径
        abs_cache_dir = os.path.join(script_dir, cache_dir)
        cache_path = Path(abs_cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 为新条目添加创建时间戳
        current_time = datetime.now().isoformat()
        for key, value in cache.items():
            if isinstance(value, dict) and 'created_at' not in value:
                value['created_at'] = current_time
        
        # 清理缓存
        cleaned_cache, cleanup_stats = cleanup_old_cache_entries(cache)
        
        # 保存清理后的缓存
        cache_file_path = cache_path / "summary_cache.pkl"
        with open(cache_file_path, 'wb') as f:
            pickle.dump(cleaned_cache, f)
        
        # 计算保存后的文件大小
        file_size = cache_file_path.stat().st_size / 1024 / 1024  # MB
        
        logger.info(f"已保存摘要缓存，共 {len(cleaned_cache)} 条记录，文件大小: {file_size:.1f}MB")
        
        # 如果文件仍然很大，记录警告
        if file_size > 50:
            logger.warning(f"缓存文件仍然较大 ({file_size:.1f}MB)，考虑进一步减少缓存条目")
        
        # 强制垃圾回收
        gc.collect()
        
    except Exception as e:
        logger.warning(f"保存摘要缓存失败: {str(e)}")

def check_base_url(base_url):
    """
    检查 BASE_URL 是否可访问
    """
    import requests
    session = None
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        
        response = session.get(f"{base_url}/bilibili?limit=5", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 200:
            logger.info(f"BASE_URL 检查通过: {base_url}")
            return True
        else:
            logger.error(f"BASE_URL 返回错误: {data}")
            return False
    except Exception as e:
        logger.error(f"BASE_URL 检查失败: {str(e)}")
        return False
    finally:
        # 确保Session被正确关闭
        if session:
            try:
                session.close()
            except:
                pass

def format_title_for_display(title, source, max_length=30):
    """
    格式化标题，确保长度一致，适配手机宽度
    """
    # 如果来源包含公众号标识，去掉前缀
    if source.startswith("公众号-"):
        source = source[4:]
    
    # 计算标题最大长度（考虑到后面要加上来源）
    source_part = f" - {source}"
    title_max_length = max_length - len(source_part)
    
    # 如果标题太长，截断并添加省略号
    if len(title) > title_max_length:
        title = title[:title_max_length-1] + "…"
    
    # 返回格式化后的标题
    return f"{title}{source_part}"

def cleanup_old_files(directory, days_to_keep=7):
    """
    清理指定目录下超过指定天数的旧文件。

    参数:
        directory (str): 需要清理的目录路径 (相对于项目根目录)。
        days_to_keep (int): 文件保留的最长天数，默认为7天。
    """
    try:
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建要清理目录的绝对路径
        abs_directory = os.path.join(script_dir, directory)

        if not os.path.isdir(abs_directory):
            logger.warning(f"清理目录不存在，跳过清理: {abs_directory}")
            return

        logger.info(f"开始清理目录 '{abs_directory}' 中超过 {days_to_keep} 天的旧文件...")

        # 计算截止时间戳
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        total_freed_size = 0  # 释放的总大小（字节）

        # 遍历目录中的所有文件
        for filename in os.listdir(abs_directory):
            file_path = os.path.join(abs_directory, filename)
            # 确保是文件而不是子目录
            if os.path.isfile(file_path):
                try:
                    # 获取文件的最后修改时间和大小
                    file_mtime = os.path.getmtime(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    # 如果文件的修改时间早于截止时间，则删除
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"已删除旧文件: {file_path} (大小: {file_size/1024:.1f}KB)")
                        deleted_count += 1
                        total_freed_size += file_size
                except Exception as e:
                    logger.error(f"删除文件 {file_path} 时出错: {str(e)}")

        freed_mb = total_freed_size / 1024 / 1024
        logger.info(f"目录 '{abs_directory}' 清理完成，共删除 {deleted_count} 个旧文件，释放空间: {freed_mb:.1f}MB")

    except Exception as e:
        logger.error(f"清理目录 {directory} 时发生意外错误: {str(e)}")

def get_memory_usage():
    """
    获取当前进程的内存使用情况
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
            "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
        }
    except ImportError:
        return {"rss_mb": "N/A", "vms_mb": "N/A"}

def optimize_cache_settings():
    """
    根据系统内存情况动态调整缓存设置
    """
    try:
        import psutil
        # 获取系统总内存
        total_memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        
        # 根据系统内存调整缓存大小
        if total_memory_gb < 4:
            # 小于4GB内存，减少缓存
            return {"max_cache_size": 500, "cleanup_days": 15}
        elif total_memory_gb < 8:
            # 4-8GB内存，标准缓存
            return {"max_cache_size": 1000, "cleanup_days": 30}
        else:
            # 大于8GB内存，增加缓存
            return {"max_cache_size": 2000, "cleanup_days": 45}
    except ImportError:
        # 如果没有psutil，使用默认设置
        return {"max_cache_size": MAX_CACHE_SIZE, "cleanup_days": CACHE_CLEANUP_DAYS}