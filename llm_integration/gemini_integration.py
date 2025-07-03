#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini 2.5 Flash日报信息总结：调用Google Gemini对当日热点进行总结
"""

import os
import json
import time
import logging
import requests
import re
import google.generativeai as genai
from datetime import datetime
from config.config import SOURCE_NAME_MAP
from utils.utils import format_title_for_display

# 配置日志
logger = logging.getLogger(__name__)

def summarize_with_gemini(hotspots, api_key, model_name="gemini-2.0-flash-exp", base_url="https://gemini.kbz.ink", max_retries=3, tech_only=False):
    """
    使用Google Gemini API对热点进行汇总归类，支持重试
    根据tech_only参数使用不同的prompt
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            # 构建API请求URL
            api_url = f"{base_url.rstrip('/')}/v1beta/models/{model_name}:generateContent"
            
            # 简化输入数据，只传递必要信息，但包含摘要
            simplified_hotspots = []
            for idx, item in enumerate(hotspots):
                source_name = SOURCE_NAME_MAP.get(item['source'], item['source'])
                simplified_hotspots.append({
                    "id": idx,
                    "title": item['title'],
                    "source": source_name,
                    "summary": item.get('summary', '')  # 添加摘要信息
                })
            
            # 将完整数据转换为字典以便后续查找
            hotspot_dict = {idx: item for idx, item in enumerate(hotspots)}
            
            # 转换为JSON格式的输入
            hotspot_json = json.dumps(simplified_hotspots, ensure_ascii=False)
            
            # 保存输入的JSON数据，使用相对路径
            save_directory = os.path.join("data", "inputs")
            os.makedirs(save_directory, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%H-%M-%S")
            input_filename = os.path.join(save_directory, f"gemini_input_{today}_{timestamp}.json")
            with open(input_filename, 'w', encoding='utf-8') as f:
                f.write(hotspot_json)
            logger.info(f"已保存Gemini输入数据至 {input_filename}")
            
            # 根据tech_only参数选择不同的prompt
            if tech_only:
                prompt = f"""
                以下是今日科技热点信息列表（包含新闻和社交媒体帖子，JSON格式），部分条目包含内容摘要：
                {hotspot_json}
                请总结出10条最重要的科技新闻，优先选择AI相关新闻，去除重复和无关内容。
                重点关注最新发布的AI技术、模型或者产品等，相关新闻在返回的结果排序中需要前置；公众号的文章权重更高，其余结果按重要性排序。
                你需要将相似的新闻合并为一条，并提供一个直观简洁的中文标题，需要讲清楚新闻内容不要太泛化（不超过30个字）。
                同时，也请关注来自 Twitter 等社交媒体源 (source: Twitter) 的重要信息，特别是关于最新 AI 技术突破、模型发布或重要行业及AI产品动态的帖子，它们同样具有很高的价值。
                相关新闻的ID列表最多选择其中3条，取最典型的，超过数量不需要全部给出。请特别注意，如果同一家媒体在多个渠道发布相同的内容，或新闻标题相似度极高，不要同时选择，则仅需列出1条即可。
                如果有摘要信息，请参考摘要提供更准确的标题。
                
                请以JSON格式返回结果，格式如下：
                ```json
                [
                  {{
                    "title": "热点标题",
                    "related_ids": [相关热点的ID列表]
                  }},
                  ...
                ]
                ```
                
                只返回JSON数据，不要有任何额外说明。
                """
            else:
                prompt = f"""
                以下是今日热点信息列表（包含新闻和社交媒体帖子，JSON格式），部分条目包含内容摘要：
                {hotspot_json}
                请总结出10条最重要的热点新闻，优先选择科技和AI相关新闻，但也要包含其他领域（如社会、娱乐、体育等）的重要新闻，去除重复内容。
                你需要将相似的新闻合并为一条，并提供一个直观简洁的中文标题，需要讲清楚新闻内容不要太泛化（不超过30个字）。
                同时，也请关注来自 Twitter 等社交媒体源 (source: Twitter) 的重要信息，特别是关于最新 AI 技术突破、模型发布或重要行业动态的帖子，将它们与新闻同等对待进行筛选和总结。
                相关新闻的ID列表最多选择其中3条，取最典型的，超过数量不需要全部给出。请特别注意，如果同一家媒体在多个渠道发布相同的内容，或新闻标题相似度极高，不要同时选择，则仅需列出1条即可。
                如果有摘要信息，请参考摘要提供更准确的标题。
                
                请以JSON格式返回结果，格式如下：
                ```json
                [
                  {{
                    "title": "热点标题",
                    "related_ids": [相关热点的ID列表]
                  }},
                  ...
                ]
                ```
                
                只返回JSON数据，不要有任何额外说明。
                """
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            
            # 构建请求体
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 100000  # 增加token限制以避免截断
                }
            }
            
            logger.info(f"正在调用 Gemini API，模型: {model_name}，端点: {api_url}，尝试次数: {retry_count + 1}/{max_retries}")
            
            # 调用Gemini API
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 添加详细的响应日志记录
            logger.info(f"Gemini API 响应状态码: {response.status_code}")
            logger.debug(f"Gemini API 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 提取回复内容 - 改进的格式解析
            json_response = ""
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                logger.debug(f"候选响应结构: {json.dumps(candidate, ensure_ascii=False, indent=2)}")
                
                # 检查响应是否被截断
                finish_reason = candidate.get("finishReason", "UNKNOWN")
                if finish_reason == "MAX_TOKENS":
                    logger.warning("⚠️  API响应因token限制被截断，尝试增加maxOutputTokens或简化输入")
                
                if "content" in candidate and "parts" in candidate["content"]:
                    json_response = candidate["content"]["parts"][0].get("text", "")
                elif "text" in candidate:
                    # 某些API版本可能直接在candidate中返回text
                    json_response = candidate["text"]
                elif "output" in candidate:
                    # 另一种可能的格式
                    json_response = candidate["output"]
                else:
                    logger.error(f"无法解析候选响应，可用字段: {list(candidate.keys())}")
                    raise Exception(f"响应格式错误：candidate中无法找到文本内容，可用字段: {list(candidate.keys())}")
                    
                # 如果响应被截断且JSON不完整，给出明确提示
                if finish_reason == "MAX_TOKENS" and not json_response.strip().endswith('}]'):
                    logger.error("响应被截断导致JSON不完整")
                    return "响应被截断，请尝试减少输入数据量或使用更高token限制的模型"
                    
            else:
                logger.error(f"响应中无candidates字段，响应结构: {list(result.keys())}")
                raise Exception(f"响应格式错误：无法找到candidates，响应字段: {list(result.keys())}")
            
            if not json_response:
                logger.error("提取的响应文本为空")
                raise Exception("响应文本为空")
            
            # 提取JSON部分
            json_str = json_response
            if "```json" in json_response:
                json_str = json_response.split("```json")[1].split("```")[0].strip()
            elif "```" in json_response:
                # 处理没有明确标记json的情况
                json_str = json_response.split("```")[1].split("```")[0].strip()
            
            # 保存Gemini的完整响应结果
            output_directory = os.path.join("data", "outputs")
            os.makedirs(output_directory, exist_ok=True)
            
            # 保存原始响应
            raw_output_filename = os.path.join(output_directory, f"gemini_raw_response_{today}_{timestamp}.json")
            raw_response_data = {
                "model": model_name,
                "api_url": api_url,
                "response": result
            }
            with open(raw_output_filename, 'w', encoding='utf-8') as f:
                json.dump(raw_response_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"已保存Gemini原始响应至 {raw_output_filename}")
            
            # 保存处理后的JSON输出
            output_filename = os.path.join(output_directory, f"gemini_output_{today}_{timestamp}.json")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"已保存Gemini输出数据至 {output_filename}")
            
            # 解析JSON
            try:
                news_items = json.loads(json_str)
                
                # 构建完整的格式化输出函数
                def build_formatted_summary(news_items, max_ids_per_news=10):
                    """构建格式化摘要，支持动态调整每条新闻的关联ID数量"""
                    formatted_summary = ""
                    for index, news in enumerate(news_items[:20]):
                        num = str(index + 1).zfill(2)
                        title = news.get("title", "未知标题")
                        
                        formatted_summary += f"## ** {num} {title} **  \n"
                        
                        # 添加相关链接，使用优化的格式
                        related_ids = news.get("related_ids", [])[:max_ids_per_news]
                        for news_id in related_ids:
                            if news_id in hotspot_dict:
                                item = hotspot_dict[news_id]
                                source_name = SOURCE_NAME_MAP.get(item['source'], item['source'])
                                item_title = item['title']
                                
                                # 清理标题中的换行符和特殊字符
                                item_title = item_title.replace('\n', ' ').replace('\r', ' ').strip()
                                # 将多个空格合并为单个空格
                                item_title = re.sub(r'\s+', ' ', item_title)
                                
                                # 格式化标题，确保长度一致
                                if len(item_title) > 18:
                                    item_title = item_title[:15] + "..."
                                
                                # 添加链接
                                formatted_summary += f"- [{item_title}]({item['url']}) `🏷️{source_name}`\n"
                        
                        # 添加空行分隔
                        formatted_summary += "\n"
                    
                    return formatted_summary
                
                # 先按原始数量生成完整内容
                formatted_summary = build_formatted_summary(news_items)
                original_length = len(formatted_summary)
                
                # 检查长度是否超限
                max_length = 4000  # 企业微信限制4096，留一些余量
                if original_length > max_length:
                    logger.warning(f"生成的内容长度 {original_length} 超过限制 {max_length}，开始智能压缩...")
                    
                    # 逐步减少每条新闻的关联ID数量
                    for max_ids in [3, 2, 1]:
                        compressed_summary = build_formatted_summary(news_items, max_ids)
                        compressed_length = len(compressed_summary)
                        logger.info(f"尝试每条新闻最多 {max_ids} 个ID，内容长度: {compressed_length}")
                        
                        if compressed_length <= max_length:
                            formatted_summary = compressed_summary
                            logger.info(f"✅ 压缩成功！最终长度: {compressed_length}，每条新闻最多 {max_ids} 个关联ID")
                            break
                    else:
                        # 如果还是超长，则移除部分新闻条目
                        for max_news in [8, 6, 5]:
                            truncated_summary = build_formatted_summary(news_items[:max_news], 1)
                            truncated_length = len(truncated_summary)
                            logger.info(f"尝试只保留前 {max_news} 条新闻，内容长度: {truncated_length}")
                            
                            if truncated_length <= max_length:
                                formatted_summary = truncated_summary
                                logger.warning(f"⚠️  极端压缩：只保留前 {max_news} 条新闻，最终长度: {truncated_length}")
                                break
                else:
                    logger.info(f"✅ 内容长度 {original_length} 在限制范围内，无需压缩")
                
                # 保存格式化后的摘要内容
                summary_filename = os.path.join(output_directory, f"formatted_summary_{today}_{timestamp}.md")
                with open(summary_filename, 'w', encoding='utf-8') as f:
                    f.write(formatted_summary)
                logger.info(f"已保存格式化摘要至 {summary_filename}")
                
                return formatted_summary
                
            except json.JSONDecodeError as e:
                logger.error(f"解析Gemini返回的JSON失败: {str(e)}")
                logger.error(f"原始响应内容: {json_str}")
                return f"解析Gemini返回的JSON失败: {str(e)}"
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # 检查是否是API密钥无效或地理位置限制错误
                try:
                    error_response = e.response.json()
                    error_message = str(error_response)
                    if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
                        logger.error(f"Gemini API密钥无效: 请检查GEMINI_API_KEY是否正确")
                        return "Gemini API密钥无效，请检查API密钥"
                    elif "User location is not supported" in error_message:
                        logger.error(f"Gemini API地理位置限制: 当前地区不支持API使用")
                        return "Gemini API地理位置限制，当前地区不支持API使用，请尝试使用VPN"
                except:
                    pass
                logger.error(f"Gemini API请求错误: {str(e)}")
                return f"Gemini API请求错误: {str(e)}"
            elif e.response.status_code == 401:
                logger.error(f"Gemini API认证失败: 请检查GEMINI_API_KEY是否正确")
                return "Gemini API认证失败，请检查API密钥"
            elif e.response.status_code == 403:
                logger.error(f"Gemini API权限不足: {str(e)}")
                return "Gemini API权限不足，请检查API密钥权限"
            else:
                logger.error(f"Gemini API HTTP错误: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"5秒后重试 ({retry_count}/{max_retries})...")
                    time.sleep(5)
                else:
                    break
        except Exception as e:
            logger.error(f"调用Gemini API失败: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"5秒后重试 ({retry_count}/{max_retries})...")
                time.sleep(5)
            else:
                break
    
    logger.error(f"Gemini API调用失败，已达到最大重试次数 {max_retries}")
    return "Gemini API调用失败，请检查API密钥和网络连接"

def test_gemini_connection(api_key, model_name="gemini-2.0-flash-exp", base_url="https://gemini.kbz.ink"):
    """
    测试Gemini API连接
    """
    try:
        # 构建API请求URL
        api_url = f"{base_url.rstrip('/')}/v1beta/models/{model_name}:generateContent"
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # 构建测试请求体
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "测试连接，请回复'连接成功'"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 10000
            }
        }
        
        # 发送测试请求
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 添加详细的响应日志记录
        logger.info(f"测试连接 - Gemini API 响应状态码: {response.status_code}")
        logger.debug(f"测试连接 - Gemini API 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 提取响应文本 - 改进的格式解析
        response_text = ""
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            logger.debug(f"测试连接 - 候选响应结构: {json.dumps(candidate, ensure_ascii=False, indent=2)}")
            
            if "content" in candidate and "parts" in candidate["content"]:
                response_text = candidate["content"]["parts"][0].get("text", "")
            elif "text" in candidate:
                # 某些API版本可能直接在candidate中返回text
                response_text = candidate["text"]
            elif "output" in candidate:
                # 另一种可能的格式
                response_text = candidate["output"]
            else:
                logger.error(f"测试连接 - 无法解析候选响应，可用字段: {list(candidate.keys())}")
                return False, f"响应格式错误：candidate中无法找到文本内容，可用字段: {list(candidate.keys())}"
                
            logger.info(f"Gemini API连接测试成功，模型: {model_name}，端点: {api_url}")
            return True, f"连接成功，响应: {response_text}"
        else:
            logger.error(f"测试连接 - 响应中无candidates字段，响应结构: {list(result.keys())}")
            return False, f"响应格式错误：无法找到candidates，响应字段: {list(result.keys())}"
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            # 检查是否是API密钥无效或地理位置限制错误
            try:
                error_response = e.response.json()
                error_message = str(error_response)
                logger.error(f"收到400错误响应: {error_response}")  # 添加调试信息
                
                if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
                    logger.error("Gemini API连接测试失败：API密钥无效，请检查GEMINI_API_KEY是否正确")
                    return False, "API密钥无效，请检查API密钥"
                elif "User location is not supported" in error_message:
                    logger.error("Gemini API连接测试失败：地理位置限制，当前地区不支持API使用")
                    return False, "地理位置限制，当前地区不支持API使用，请尝试使用VPN"
            except Exception as parse_error:
                logger.error(f"解析错误响应失败: {parse_error}")
                logger.error(f"原始响应内容: {e.response.text}")
            logger.error(f"Gemini API连接测试失败: 请求错误 (400)")
            return False, "请求错误，请检查API密钥格式"
        elif e.response.status_code == 401:
            logger.error("Gemini API连接测试失败：认证失败，请检查GEMINI_API_KEY是否正确")
            return False, "认证失败，请检查API密钥"
        elif e.response.status_code == 403:
            logger.error("Gemini API连接测试失败：权限不足，请检查API密钥权限")
            return False, "权限不足，请检查API密钥权限"
        else:
            logger.error(f"Gemini API连接测试失败: HTTP {e.response.status_code}")
            return False, f"HTTP {e.response.status_code} 错误"
    except Exception as e:
        logger.error(f"Gemini API连接测试失败: {str(e)}")
        return False, str(e) 