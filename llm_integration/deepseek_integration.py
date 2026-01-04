#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
deepseek日报信息总结：调用deepseek对当日热点进行总结
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from config.config import SOURCE_NAME_MAP, MAX_RELATED_IDS
from utils.utils import format_title_for_display

# 配置日志
logger = logging.getLogger(__name__)

def summarize_with_deepseek(hotspots, api_key, api_url=None, model_id=None, max_retries=3, tech_only=False):
    """
    使用Deepseek API对热点进行汇总归类，支持重试
    根据tech_only参数使用不同的prompt
    """
    if api_url is None:
        api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    if model_id is None:
        model_id = "ep-20251206191310-f92dj"
    
    retry_count = 0
    while retry_count < max_retries:
        try:
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
            input_filename = os.path.join(save_directory, f"deepseek_input_{today}_{timestamp}.json")
            with open(input_filename, 'w', encoding='utf-8') as f:
                f.write(hotspot_json)
            logger.info(f"已保存Deepseek输入数据至 {input_filename}")
            
            # 根据tech_only参数选择不同的prompt
            if tech_only:
                prompt = f"""
                以下是今日科技热点信息列表（包含新闻和社交媒体帖子，JSON格式），部分条目包含内容摘要：
                {hotspot_json}
                请总结出10条最重要的AI相关科技新闻，去除重复和无关内容。
                重点关注最新发布的AI技术、模型或者产品等，相关新闻在返回的结果排序中需要前置；公众号的文章权重更高，其余结果按重要性排序。
                你需要将相似的新闻合并为一条，并提供一个直观简洁的中文标题，需要讲清楚新闻内容不要太泛化（不超过30个字）。
                同时，也请关注来自 Twitter 等社交媒体源 (source: Twitter) 的重要信息，特别是关于最新 AI 技术突破、模型发布或重要行业及AI产品动态的帖子，它们同样具有很高的价值。
                返回的相关新闻列表ID数量不能超过3个，取最重要和直观的，不要全部列出。
                请特别注意，如果同一个账号在多个平台发布相同的内容，或不同平台的新闻标题相似度极高，请过滤掉重复条目，仅需列出1条即可。
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
                返回的相关新闻列表ID数量不能超过3个，取最重要和直观的，不要全部列出。
                请特别注意，如果同一个账号在多个平台发布相同的内容，或不同平台的新闻标题相似度极高，请过滤掉重复条目，仅需列出1条即可。
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
            
            # 调用Deepseek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": "你是一个专业的新闻编辑助手，擅长归纳总结热点新闻。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            logger.info(f"正在调用 Deepseek API，尝试次数: {retry_count + 1}/{max_retries}")
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=300
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 提取回复内容
            json_response = result["choices"][0]["message"]["content"]
            
            # 提取JSON部分
            json_str = json_response
            if "```json" in json_response:
                json_str = json_response.split("```json")[1].split("```")[0].strip()
            
            # 保存Deepseek的完整响应结果
            output_directory = os.path.join("data", "outputs")
            os.makedirs(output_directory, exist_ok=True)
            
            # 保存原始响应
            raw_output_filename = os.path.join(output_directory, f"deepseek_raw_response_{today}_{timestamp}.json")
            with open(raw_output_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存Deepseek原始响应至 {raw_output_filename}")
            
            # 保存处理后的JSON输出
            output_filename = os.path.join(output_directory, f"deepseek_output_{today}_{timestamp}.json")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"已保存Deepseek输出数据至 {output_filename}")
            
            # 解析JSON
            try:
                news_items = json.loads(json_str)
                
                # 根据JSON构建最终输出
                formatted_summary = ""
                for index, news in enumerate(news_items[:20]):
                    num = str(index + 1).zfill(2)
                    title = news.get("title", "未知标题")
                    
                    formatted_summary += f"## ** {num} {title} **  \n"
                    
                    # 添加相关链接，使用优化的格式，限制最大ID数量
                    related_ids = news.get("related_ids", [])[:MAX_RELATED_IDS]
                    for news_id in related_ids:
                        if news_id in hotspot_dict:
                            item = hotspot_dict[news_id]
                            source_name = SOURCE_NAME_MAP.get(item['source'], item['source'])
                            item_title = item['title']
                            # 格式化标题，确保长度一致
                            if len(item_title) > 18:
                                item_title = item_title[:15] + "..."
                            
                            # 添加链接
                            formatted_summary += f"- [{item_title}]({item['url']}) `🏷️{source_name}`\n"
                    
                    # 添加空行分隔
                    formatted_summary += "\n"
                
                # 保存格式化后的摘要内容
                summary_filename = os.path.join(output_directory, f"formatted_summary_{today}_{timestamp}.md")
                with open(summary_filename, 'w', encoding='utf-8') as f:
                    f.write(formatted_summary)
                logger.info(f"已保存格式化摘要至 {summary_filename}")
                
                return formatted_summary
                
            except json.JSONDecodeError as e:
                logger.error(f"解析Deepseek返回的JSON失败: {str(e)}")
                return f"解析Deepseek返回的JSON失败: {str(e)}"
            
        except requests.exceptions.Timeout:
            retry_count += 1
            logger.warning(f"Deepseek API 请求超时，正在重试 ({retry_count}/{max_retries})...")
            time.sleep(5)  # 等待5秒后重试
        
        except Exception as e:
            logger.error(f"调用Deepseek API时发生错误: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"5秒后重试 ({retry_count}/{max_retries})...")
                time.sleep(5)
            else:
                break
    
    # 如果所有重试都失败，抛出异常中断流程
    error_msg = f"Deepseek API调用失败，已达到最大重试次数 {max_retries}"
    logger.error(error_msg)
    raise Exception(error_msg)