#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误通知模块：当系统出现异常时，通过独立的通道发送错误通知
避免错误信息干扰正常的业务推送
"""

import os
import json
import logging
import requests
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

# 配置日志
logger = logging.getLogger(__name__)

class ErrorNotifier:
    """错误通知器，负责发送系统错误信息到独立的通知渠道"""
    
    def __init__(self):
        """初始化错误通知器，从环境变量读取配置"""
        self.enabled = os.getenv('ERROR_NOTIFICATION_ENABLED', 'true').lower() == 'true'
        self.webhook_url = os.getenv('ERROR_WEBHOOK_URL')
        self.qywx_key = os.getenv('ERROR_QYWX_KEY')
        self.tg_bot_token = os.getenv('ERROR_TG_BOT_TOKEN')
        self.tg_user_id = os.getenv('ERROR_TG_USER_ID')
        
        if not self.enabled:
            logger.info("错误通知功能已禁用")
            return
            
        # 检查是否至少配置了一种通知方式
        self.has_config = bool(
            self.webhook_url or 
            self.qywx_key or 
            (self.tg_bot_token and self.tg_user_id)
        )
        
        if not self.has_config:
            logger.warning("未配置任何错误通知渠道，错误通知功能将不可用")
    
    def notify_error(self, 
                    error_type: str, 
                    error_message: str, 
                    error_details: Optional[Dict[str, Any]] = None,
                    stage: str = "未知阶段",
                    traceback_info: Optional[str] = None) -> bool:
        """
        发送错误通知
        
        Args:
            error_type: 错误类型 (如: "API调用失败", "数据收集异常", "推送失败")
            error_message: 错误简要描述
            error_details: 详细错误信息字典
            stage: 发生错误的处理阶段
            traceback_info: 错误堆栈信息
            
        Returns:
            bool: 是否成功发送通知
        """
        if not self.enabled or not self.has_config:
            logger.debug(f"错误通知未启用或未配置，跳过错误通知: {error_type}")
            return False
        
        try:
            # 构建错误通知内容
            content = self._build_error_content(
                error_type, error_message, error_details, stage, traceback_info
            )
            
            # 保存错误日志
            self._save_error_log(content)
            
            # 尝试发送通知
            success = False
            
            # 企业微信机器人通知
            if self.qywx_key:
                if self._send_qywx_notification(content):
                    success = True
                    logger.info("已通过企业微信发送错误通知")
            
            # Telegram通知
            if self.tg_bot_token and self.tg_user_id:
                if self._send_telegram_notification(content):
                    success = True
                    logger.info("已通过Telegram发送错误通知")
            
            # 原始Webhook通知
            if self.webhook_url:
                if self._send_webhook_notification(content):
                    success = True
                    logger.info("已通过Webhook发送错误通知")
            
            if not success:
                logger.error("所有错误通知渠道均失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送错误通知时发生异常: {str(e)}")
            return False
    
    def _build_error_content(self, 
                           error_type: str, 
                           error_message: str, 
                           error_details: Optional[Dict[str, Any]],
                           stage: str,
                           traceback_info: Optional[str]) -> Dict[str, str]:
        """构建错误通知内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建标题
        title = f"🚨 系统错误通知 - {error_type}"
        
        # 构建消息内容
        content_lines = [
            f"⏰ **发生时间**: {timestamp}",
            f"🔍 **错误阶段**: {stage}",
            f"❌ **错误类型**: {error_type}",
            f"📝 **错误描述**: {error_message}",
        ]
        
        # 添加详细信息
        if error_details:
            content_lines.append("\n📋 **详细信息**:")
            for key, value in error_details.items():
                content_lines.append(f"- {key}: {value}")
        
        # 添加堆栈信息（截断以避免过长）
        if traceback_info:
            content_lines.append("\n🔧 **堆栈信息**:")
            # 限制堆栈信息长度
            if len(traceback_info) > 500:
                traceback_info = traceback_info[:500] + "\n... (堆栈信息已截断)"
            content_lines.append(f"```\n{traceback_info}\n```")
        
        content_lines.append(f"\n🏷️ **来源**: 热点新闻推送系统")
        
        markdown_content = "\n".join(content_lines)
        plain_content = markdown_content.replace("**", "").replace("`", "")
        
        return {
            "title": title,
            "markdown_content": markdown_content,
            "plain_content": plain_content,
            "timestamp": timestamp
        }
    
    def _send_qywx_notification(self, content: Dict[str, str]) -> bool:
        """通过企业微信机器人发送错误通知"""
        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.qywx_key}"
            headers = {"Content-Type": "application/json;charset=utf-8"}
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content["markdown_content"]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("errcode") == 0:
                return True
            else:
                logger.error(f"企业微信错误通知发送失败: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"企业微信错误通知发送异常: {str(e)}")
            return False
    
    def _send_telegram_notification(self, content: Dict[str, str]) -> bool:
        """通过Telegram发送错误通知"""
        try:
            url = f"https://api.telegram.org/bot{self.tg_bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.tg_user_id,
                "text": content["plain_content"],
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("ok"):
                return True
            else:
                logger.error(f"Telegram错误通知发送失败: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram错误通知发送异常: {str(e)}")
            return False
    
    def _send_webhook_notification(self, content: Dict[str, str]) -> bool:
        """通过原始Webhook发送错误通知"""
        try:
            # 如果是企业微信webhook，使用markdown格式
            if "qyapi.weixin.qq.com" in self.webhook_url:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": content["markdown_content"]
                    }
                }
            else:
                # 其他webhook，使用简单文本格式
                payload = {
                    "text": content["plain_content"]
                }
            
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook错误通知发送异常: {str(e)}")
            return False
    
    def _save_error_log(self, content: Dict[str, str]) -> None:
        """保存错误通知到文件"""
        try:
            # 确保错误日志目录存在
            log_dir = os.path.join("data", "error_logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成日志文件名
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = os.path.join(log_dir, f"error_notification_{timestamp}.json")
            
            # 保存错误信息
            error_data = {
                "timestamp": content["timestamp"],
                "title": content["title"],
                "content": content["markdown_content"],
                "plain_content": content["plain_content"]
            }
            
            with open(log_filename, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"已保存错误日志至: {log_filename}")
            
        except Exception as e:
            logger.error(f"保存错误日志失败: {str(e)}")


# 全局错误通知器实例（延迟初始化）
_error_notifier = None


def _get_error_notifier():
    """获取错误通知器实例（延迟初始化，确保环境变量已加载）"""
    global _error_notifier
    if _error_notifier is None:
        # 确保加载.env文件
        from dotenv import load_dotenv
        load_dotenv()
        _error_notifier = ErrorNotifier()
    return _error_notifier


def notify_critical_error(error_type: str, 
                         error_message: str, 
                         error_details: Optional[Dict[str, Any]] = None,
                         stage: str = "未知阶段") -> bool:
    """
    便捷函数：发送关键错误通知
    自动捕获当前异常的堆栈信息
    
    Args:
        error_type: 错误类型
        error_message: 错误信息
        error_details: 错误详情
        stage: 处理阶段
        
    Returns:
        bool: 是否成功发送通知
    """
    traceback_info = traceback.format_exc() if traceback else None
    
    notifier = _get_error_notifier()
    return notifier.notify_error(
        error_type=error_type,
        error_message=error_message,
        error_details=error_details,
        stage=stage,
        traceback_info=traceback_info
    )


def notify_simple_error(error_type: str, error_message: str, stage: str = "未知阶段") -> bool:
    """
    便捷函数：发送简单错误通知
    
    Args:
        error_type: 错误类型
        error_message: 错误信息
        stage: 处理阶段
        
    Returns:
        bool: 是否成功发送通知
    """
    notifier = _get_error_notifier()
    return notifier.notify_error(
        error_type=error_type,
        error_message=error_message,
        stage=stage
    ) 