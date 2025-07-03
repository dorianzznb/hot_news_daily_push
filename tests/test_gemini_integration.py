#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Gemini集成功能
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_integration.gemini_integration import summarize_with_gemini, test_gemini_connection

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_api_connection():
    """测试Gemini API连接"""
    api_key = os.getenv('GEMINI_API_KEY')
    base_url = os.getenv('GEMINI_BASE_URL', 'https://gemini.kbz.ink')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash-exp')
    
    if not api_key:
        logger.error("未设置GEMINI_API_KEY环境变量")
        return False
    
    logger.info(f"测试Gemini API连接... (端点: {base_url}, 模型: {model_name})")
    success, message = test_gemini_connection(api_key, model_name=model_name, base_url=base_url)
    
    if success:
        logger.info(f"✅ Gemini API连接测试成功: {message}")
        return True
    else:
        logger.error(f"❌ Gemini API连接测试失败: {message}")
        return False

def test_gemini_summarization():
    """测试Gemini总结功能"""
    api_key = os.getenv('GEMINI_API_KEY')
    base_url = os.getenv('GEMINI_BASE_URL', 'https://gemini.kbz.ink')
    if not api_key:
        logger.error("未设置GEMINI_API_KEY环境变量")
        return False
    
    # 模拟热点数据
    mock_hotspots = [
        {
            "title": "OpenAI发布GPT-5模型，性能大幅提升",
            "url": "https://example.com/news1",
            "source": "tech_news",
            "summary": "OpenAI今日宣布推出新一代语言模型GPT-5，在多项基准测试中表现出色。"
        },
        {
            "title": "谷歌推出Gemini Ultra模型",
            "url": "https://example.com/news2", 
            "source": "google_ai",
            "summary": "谷歌发布了其最新的多模态AI模型Gemini Ultra，支持文本、图像和代码理解。"
        },
        {
            "title": "Meta发布开源大模型Llama 3",
            "url": "https://example.com/news3",
            "source": "meta_research", 
            "summary": "Meta公司开源了新版本的Llama模型，提供更强的推理能力和更广泛的应用场景。"
        }
    ]
    
    logger.info("测试Gemini总结功能...")
    
    try:
        # 测试科技模式
        logger.info("测试科技模式总结...")
        summary_tech = summarize_with_gemini(mock_hotspots, api_key, base_url=base_url, tech_only=True)
        
        if summary_tech and "解析Gemini返回的JSON失败" not in summary_tech:
            logger.info("✅ 科技模式总结测试成功")
            logger.info("生成的总结预览:")
            logger.info(summary_tech[:200] + "..." if len(summary_tech) > 200 else summary_tech)
        else:
            logger.error("❌ 科技模式总结测试失败")
            return False
        
        # 测试普通模式
        logger.info("测试普通模式总结...")
        summary_normal = summarize_with_gemini(mock_hotspots, api_key, base_url=base_url, tech_only=False)
        
        if summary_normal and "解析Gemini返回的JSON失败" not in summary_normal:
            logger.info("✅ 普通模式总结测试成功")
            logger.info("生成的总结预览:")
            logger.info(summary_normal[:200] + "..." if len(summary_normal) > 200 else summary_normal)
        else:
            logger.error("❌ 普通模式总结测试失败")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Gemini总结功能测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    logger.info("开始Gemini集成测试...")
    
    # 检查环境变量
    if not os.getenv('GEMINI_API_KEY'):
        logger.error("请设置GEMINI_API_KEY环境变量")
        logger.info("例如: export GEMINI_API_KEY='your_api_key_here'")
        return
    
    # 测试API连接
    if not test_gemini_api_connection():
        logger.error("API连接测试失败，跳过后续测试")
        return
    
    # 测试总结功能
    if test_gemini_summarization():
        logger.info("🎉 所有Gemini集成测试通过！")
    else:
        logger.error("❌ 部分测试失败")

if __name__ == "__main__":
    main() 