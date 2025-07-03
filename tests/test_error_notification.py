#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误通知系统测试脚本
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notification.error_notifier import (
    ErrorNotifier, 
    notify_critical_error, 
    notify_simple_error
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_error_notifier_initialization():
    """测试错误通知器初始化"""
    logger.info("=== 测试错误通知器初始化 ===")
    
    # 创建错误通知器实例
    notifier = ErrorNotifier()
    
    logger.info(f"错误通知是否启用: {notifier.enabled}")
    logger.info(f"是否有配置: {notifier.has_config}")
    
    if notifier.has_config:
        logger.info("✅ 错误通知器配置检测正常")
        config_info = []
        if notifier.webhook_url:
            config_info.append(f"原始Webhook: {notifier.webhook_url[:30]}...")
        if notifier.qywx_key:
            config_info.append(f"企业微信Key: {notifier.qywx_key[:10]}...")
        if notifier.tg_bot_token and notifier.tg_user_id:
            config_info.append(f"Telegram: {notifier.tg_user_id}")
        
        logger.info(f"配置的通知渠道: {', '.join(config_info) if config_info else '无'}")
    else:
        logger.warning("⚠️  未检测到任何错误通知配置")
    
    return notifier


def test_simple_error_notification():
    """测试简单错误通知"""
    logger.info("\n=== 测试简单错误通知 ===")
    
    success = notify_simple_error(
        "测试错误类型",
        "这是一个测试错误消息，用于验证简单错误通知功能",
        "测试阶段"
    )
    
    if success:
        logger.info("✅ 简单错误通知发送成功")
    else:
        logger.warning("⚠️  简单错误通知发送失败或未配置")
    
    return success


def test_critical_error_notification():
    """测试关键错误通知"""
    logger.info("\n=== 测试关键错误通知 ===")
    
    error_details = {
        "错误代码": "TEST_001",
        "影响范围": "测试环境",
        "预期修复时间": "立即",
        "相关组件": ["错误通知模块", "测试脚本"]
    }
    
    try:
        # 故意抛出异常以测试堆栈跟踪
        raise ValueError("这是一个测试异常，用于验证关键错误通知功能")
    except Exception:
        success = notify_critical_error(
            "关键测试错误",
            "这是一个测试关键错误，包含完整的上下文信息",
            error_details,
            "测试阶段"
        )
        
        if success:
            logger.info("✅ 关键错误通知发送成功")
        else:
            logger.warning("⚠️  关键错误通知发送失败或未配置")
        
        return success


def test_error_notification_content():
    """测试错误通知内容格式"""
    logger.info("\n=== 测试错误通知内容格式 ===")
    
    notifier = ErrorNotifier()
    
    # 测试内容构建
    content = notifier._build_error_content(
        error_type="内容格式测试",
        error_message="测试错误通知的内容格式是否正确",
        error_details={
            "测试参数1": "值1",
            "测试参数2": "值2",
            "嵌套对象": {"子属性": "子值"}
        },
        stage="内容测试",
        traceback_info="这是一个模拟的堆栈跟踪信息\n  at test_function()\n  at main()"
    )
    
    logger.info("生成的错误通知内容:")
    logger.info(f"标题: {content['title']}")
    logger.info(f"Markdown内容长度: {len(content['markdown_content'])} 字符")
    logger.info(f"纯文本内容长度: {len(content['plain_content'])} 字符")
    logger.info(f"时间戳: {content['timestamp']}")
    
    # 显示内容预览
    logger.info("\nMarkdown内容预览:")
    print("=" * 50)
    print(content['markdown_content'])
    print("=" * 50)
    
    return True


def test_multiple_error_scenarios():
    """测试多种错误场景"""
    logger.info("\n=== 测试多种错误场景 ===")
    
    test_scenarios = [
        {
            "type": "配置错误",
            "message": "缺少必要的API密钥配置",
            "details": {"缺少密钥": ["DEEPSEEK_API_KEY", "GEMINI_API_KEY"]},
            "stage": "初始化"
        },
        {
            "type": "网络连接失败",
            "message": "无法连接到外部API服务",
            "details": {"URL": "https://api.example.com", "状态码": 503},
            "stage": "数据收集"
        },
        {
            "type": "数据处理异常",
            "message": "处理新闻数据时发生解析错误",
            "details": {"数据量": 150, "失败条目": 5},
            "stage": "内容处理"
        },
        {
            "type": "AI服务异常",
            "message": "AI总结服务返回异常响应",
            "details": {"模型": "gemini-2.5-flash", "错误码": "RATE_LIMIT"},
            "stage": "AI总结"
        },
        {
            "type": "推送失败",
            "message": "所有配置的推送渠道均无法正常工作",
            "details": {"尝试渠道": ["企业微信", "Telegram", "Webhook"]},
            "stage": "消息推送"
        }
    ]
    
    success_count = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n测试场景 {i}: {scenario['type']}")
        
        success = notify_simple_error(
            scenario["type"],
            scenario["message"],
            scenario["stage"]
        )
        
        if success:
            success_count += 1
            logger.info(f"✅ 场景 {i} 通知发送成功")
        else:
            logger.warning(f"⚠️  场景 {i} 通知发送失败")
    
    logger.info(f"\n多场景测试完成：{success_count}/{len(test_scenarios)} 个场景成功")
    return success_count == len(test_scenarios)


def main():
    """主测试函数"""
    logger.info("🚀 开始错误通知系统测试")
    
    try:
        # 测试初始化
        notifier = test_error_notifier_initialization()
        
        if not notifier.enabled:
            logger.warning("错误通知功能已禁用，跳过测试")
            return
        
        if not notifier.has_config:
            logger.warning("未配置错误通知渠道，部分测试将跳过")
            logger.info("要测试错误通知功能，请配置以下环境变量之一：")
            logger.info("- ERROR_WEBHOOK_URL: 自定义错误通知webhook")
            logger.info("- ERROR_QYWX_KEY: 企业微信机器人密钥")
            logger.info("- ERROR_TG_BOT_TOKEN + ERROR_TG_USER_ID: Telegram通知")
        
        # 执行各项测试
        tests = [
            ("内容格式测试", test_error_notification_content),
            ("简单错误通知测试", test_simple_error_notification),
            ("关键错误通知测试", test_critical_error_notification),
            ("多场景错误测试", test_multiple_error_scenarios)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"执行测试: {test_name}")
                logger.info(f"{'='*60}")
                
                result = test_func()
                if result:
                    passed_tests += 1
                    logger.info(f"✅ {test_name} - 通过")
                else:
                    logger.warning(f"⚠️  {test_name} - 未通过（可能因为未配置）")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} - 执行失败: {str(e)}")
        
        # 输出测试结果
        logger.info(f"\n{'='*60}")
        logger.info("测试总结")
        logger.info(f"{'='*60}")
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 所有测试通过！错误通知系统工作正常")
        else:
            logger.warning("⚠️  部分测试未通过，请检查配置或日志")
            
    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}")
        # 测试错误通知系统本身
        try:
            notify_critical_error(
                "测试系统异常",
                f"错误通知系统测试过程中发生异常: {str(e)}",
                {"测试脚本": __file__},
                "测试执行"
            )
        except Exception as notify_error:
            logger.error(f"连错误通知都失败了: {str(notify_error)}")


if __name__ == "__main__":
    main() 