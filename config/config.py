#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件：存放各种变量值和配置信息
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API密钥
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
HUNYUAN_API_KEY = os.getenv('HUNYUAN_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Crawl4AI 配置
CRAWL4AI_ENABLED = os.getenv('CRAWL4AI_ENABLED', 'false').lower() == 'true'
CRAWL4AI_API_URL = os.getenv('CRAWL4AI_API_URL', 'http://crawl.tuber.cc')
CRAWL4AI_API_TOKEN = os.getenv('CRAWL4AI_API_TOKEN', 'sk-tuber0613kobezhao')
CRAWL4AI_TIMEOUT = int(os.getenv('CRAWL4AI_TIMEOUT', '20'))
CRAWL4AI_MAX_RETRIES = int(os.getenv('CRAWL4AI_MAX_RETRIES', '2'))

# 总结模型选择 (支持: deepseek, gemini)
SUMMARY_MODEL = os.getenv('SUMMARY_MODEL', 'deepseek')
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash')
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com')

# Webhook URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# 错误通知配置 - 独立的错误推送通道
ERROR_WEBHOOK_URL = os.getenv('ERROR_WEBHOOK_URL')  # 专门用于错误通知的webhook
ERROR_QYWX_KEY = os.getenv('ERROR_QYWX_KEY')        # 错误通知企业微信机器人key
ERROR_TG_BOT_TOKEN = os.getenv('ERROR_TG_BOT_TOKEN')  # 错误通知Telegram机器人token
ERROR_TG_USER_ID = os.getenv('ERROR_TG_USER_ID')      # 错误通知Telegram用户ID
ERROR_NOTIFICATION_ENABLED = os.getenv('ERROR_NOTIFICATION_ENABLED', 'true').lower() == 'true'

# API配置
BASE_URL = os.getenv('BASE_URL', 'https://api-hot.imsyy.top')
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL')
DEEPSEEK_MODEL_ID = os.getenv('DEEPSEEK_MODEL_ID')

# RSS配置
RSS_URL = os.getenv('RSS_URL')
RSS_DAYS = int(os.getenv('RSS_DAYS', '1'))

# 推送内容配置
MAX_RELATED_IDS = int(os.getenv('MAX_RELATED_IDS', '3'))  # 每条新闻最多显示的关联ID数量

# RSS源列表
RSS_FEEDS = [
    {
        'name': 'OpenAI Blog',
        'url': 'https://openai.com/blog/rss.xml'
    },
    {
        'name': '机器之心',
        'url': 'https://www.jiqizhixin.com/rss'
    },
    {
        'name': '极客公园',
        'url': 'http://www.geekpark.net/rss'
    },
    {
        'name': 'Google DeepMind',
        'url': 'https://deepmind.google/blog/rss.xml'
    },
    {
        'name': '量子位',
        'url': 'https://www.qbitai.com/feed'
    },
    {
        'name': 'InfoQ',
        'url': 'https://www.infoq.cn/feed'
    },
    {
        'name': 'MarkTechPost',
        'url': 'https://marktechpost.com/feed'
    },
    {
        'name': 'Meta Research',
        'url': 'https://research.facebook.com/feed/'
    },
    {
        'name': 'VentureBeat',
        'url': 'https://venturebeat.com/category/ai/feed/'
    },
    {
        'name': 'AI news',
        'url': 'https://www.artificialintelligence-news.com/feed/'
    },
    {
        'name': 'Wired',
        'url': 'https://www.wired.com/feed/tag/ai/latest/rss'
    },
    {
        'name': 'Bloomberg',
        'url': 'https://feeds.bloomberg.com/technology/news.rss'
    },
    {
        'name': 'TechCrunch',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/'
    },
    {
        'name': 'huggingface',
        'url': 'https://huggingface.co/blog/feed.xml'
    },
    {
        'name': 'TechSpot',
        'url': 'https://www.techspot.com/backend.xml'
    },
    {
        'name': 'The Verge',
        'url': 'https://www.theverge.com/rss/index.xml'
    },
    # {
    #     'name': 'Twitter',
    #     'accounts': [
    #         # {
    #         #     'name': 'Barsee',
    #         #     'url': 'https://rsshub.app/twitter/user/heyBarsee'
    #         # },
    #         # {
    #         #     'name': 'Sam Altman',
    #         #     'url': 'https://rsshub.app/twitter/user/sama'
    #         # },
    #         # {
    #         #     'name': 'Anthropic',
    #         #     'url': 'https://rsshub.app/twitter/user/AnthropicAI'
    #         # },
    #         # {
    #         #     'name': 'AI at Meta',
    #         #     'url': 'https://rsshub.app/twitter/user/AIatMeta'
    #         # },
    #         # {
    #         #     'name': 'Google DeepMind',
    #         #     'url': 'https://rsshub.app/twitter/user/GoogleDeepMind'
    #         # },
    #         # {
    #         #     'name': 'Hugging Face',
    #         #     'url': 'https://rsshub.app/twitter/user/huggingface'
    #         # },
    #         # {
    #         #     'name': 'Pieter Abbeel',
    #         #     'url': 'https://rsshub.app/twitter/user/pabbeel'
    #         # },
    #         # {
    #         #     'name': 'Eliezer Yudkowsky',
    #         #     'url': 'https://rsshub.app/twitter/user/ESYudkowsky'
    #         # },
    #         # {
    #         #     'name': 'Ilya Sutskever',
    #         #     'url': 'https://rsshub.app/twitter/user/ilyasut'
    #         # },
    #         # {
    #         #     'name': 'Eric Schmidt',
    #         #     'url': 'https://rsshub.app/twitter/user/ericschmidt'
    #         # },
    #         # {
    #         #     'name': 'Hugo Larochelle',
    #         #     'url': 'https://rsshub.app/twitter/user/hugo_larochelle'
    #         # },
    #         # {
    #         #     'name': 'elvis',
    #         #     'url': 'https://rsshub.app/twitter/user/omarsar0'
    #         # },
    #         # {
    #         #     'name': 'Jim Fan',
    #         #     'url': 'https://rsshub.app/twitter/user/DrJimFan'
    #         # },
    #         # {
    #         #     'name': 'Fei-Fei Li',
    #         #     'url': 'https://rsshub.app/twitter/user/drfeifei'
    #         # },
    #         # {
    #         #     'name': 'Emad',
    #         #     'url': 'https://rsshub.app/twitter/user/EMostaque'
    #         # },
    #         # {
    #         #     'name': 'Sebastian Raschka',
    #         #     'url': 'https://rsshub.app/twitter/user/rasbt'
    #         # },
    #         # {
    #         #     'name': 'Lucas Beyer',
    #         #     'url': 'https://rsshub.app/twitter/user/giffmana'
    #         # },
    #         # {
    #         #     'name': 'Aakanksha Chowdhery',
    #         #     'url': 'https://rsshub.app/twitter/user/achowdhery'
    #         # },
    #         # {
    #         #     'name': 'Jeff Dean',
    #         #     'url': 'https://rsshub.app/twitter/user/JeffDean'
    #         # },
    #         # {
    #         #     'name': 'Michael Black',
    #         #     'url': 'https://rsshub.app/twitter/user/Michael_J_Black'
    #         # },
    #         # {
    #         #     'name': 'Oriol Vinyals',
    #         #     'url': 'https://rsshub.app/twitter/user/OriolVinyalsML'
    #         # },
    #         # {
    #         #     'name': 'Lilian Weng',
    #         #     'url': 'https://rsshub.app/twitter/user/lilianweng'
    #         # },
    #         # {
    #         #     'name': 'hardmaru',
    #         #     'url': 'https://rsshub.app/twitter/user/hardmaru'
    #         # },
    #         # {
    #         #     'name': 'Demis Hassabis',
    #         #     'url': 'https://rsshub.app/twitter/user/demishassabis'
    #         # },
    #         # {
    #         #     'name': 'Sara Hooker',
    #         #     'url': 'https://rsshub.app/twitter/user/sarahookr'
    #         # },
    #         # {
    #         #     'name': 'Jürgen Schmidhuber',
    #         #     'url': 'https://rsshub.app/twitter/user/SchmidhuberAI'
    #         # },
    #         # {
    #         #     'name': 'François Chollet',
    #         #     'url': 'https://rsshub.app/twitter/user/fchollet'
    #         # },
    #         # {
    #         #     'name': 'Yao Fu',
    #         #     'url': 'https://rsshub.app/twitter/user/Francis_YAO_'
    #         # },
    #         # {
    #         #     'name': 'OpenAI',
    #         #     'url': 'https://rsshub.app/twitter/user/OpenAI'
    #         # },
    #         # {
    #         #     'name': 'Andrew Ng',
    #         #     'url': 'https://rsshub.app/twitter/user/AndrewYNg'
    #         # },
    #         # {
    #         #     'name': 'Jay Hack',
    #         #     'url': 'https://rsshub.app/twitter/user/mathemagic1an'
    #         # },
    #         # {
    #         #     'name': 'John Nay',
    #         #     'url': 'https://rsshub.app/twitter/user/johnjnay'
    #         # },
    #         # {
    #         #     'name': 'LangChain',
    #         #     'url': 'https://rsshub.app/twitter/user/LangChainAI'
    #         # },
    #         # {
    #         #     'name': '歸藏',
    #         #     'url': 'https://rsshub.app/twitter/user/op7418'
    #         # },
    #         # {
    #         #     'name': '宝玉',
    #         #     'url': 'https://rsshub.app/twitter/user/dotey'
    #         # },
    #         # {
    #         #     'name': 'Lex Fridman',
    #         #     'url': 'https://rsshub.app/twitter/user/lexfridman'
    #         # },
    #         # {
    #         #     'name': 'roon',
    #         #     'url': 'https://rsshub.app/twitter/user/tszzl'
    #         # },
    #         # {
    #         #     'name': 'Suhail',
    #         #     'url': 'https://rsshub.app/twitter/user/Suhail'
    #         # },
    #         # {
    #         #     'name': 'Aaron Levie',
    #         #     'url': 'https://rsshub.app/twitter/user/levie'
    #         # },
    #     ]
    # },
    {
        'name': '公众号',
        'url': RSS_URL
    },
    {
        "name": "公众号-Z Potentials",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3285810954.atom"
    },
    {
        "name": "公众号-向阳乔木推荐看",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3008229483.atom"
    },
    {
        "name": "公众号-微软亚洲研究院",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3001073387.atom"
    },
    {
        "name": "公众号-通往AGI之路",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3933490096.atom"
    },
    {
        "name": "公众号-赛博禅心",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3934419561.atom"
    },
    {
        "name": "公众号-PaperWeekly",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3201788143.atom"
    },
    {
        "name": "公众号-MacTalk",
        "url": "https://werss.tuber.cc/feed/MP_WXS_2398460220.atom"
    },
    {
        "name": "公众号-李继刚",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3913757353.atom"
    },
    {
        "name": "公众号-歸藏的AI工具箱",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3540975510.atom"
    },
    {
        "name": "公众号-谷歌开发者",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3008689962.atom"
    },
    {
        "name": "公众号-EverAI酱",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3099987471.atom"
    },
    {
        "name": "公众号-Tech星球",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3591736224.atom"
    },
    {
        "name": "公众号-甲子光年",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3599245772.atom"
    },
    {
        "name": "公众号-极客公园",
        "url": "https://werss.tuber.cc/feed/MP_WXS_1304308441.atom"
    },
    {
        "name": "公众号-Hugging Face",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3940425683.atom"
    },
    {
        "name": "公众号-海外独角兽",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3869640945.atom"
    },
    {
        "name": "公众号-Founder Park",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3895742803.atom"
    },
    {
        "name": "公众号-AIGC开放社区",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3873892677.atom"
    },
    {
        "name": "公众号-APPSO",
        "url": "https://werss.tuber.cc/feed/MP_WXS_2392024520.atom"
    },
    {
        "name": "公众号-AI硬核科技",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3004341395.atom"
    },
    {
        "name": "公众号-AI生活研究所",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3013745912.atom"
    },
    {
        "name": "公众号-AI前线",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3554086560.atom"
    },
    {
        "name": "公众号-AI科技评论",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3098132220.atom"
    },
    {
        "name": "公众号-AI科技大本营",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3884405249.atom"
    },
    {
        "name": "公众号-AIGCLINK",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3005297687.atom"
    },
    {
        "name": "公众号-AI产品榜",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3099356578.atom"
    },
    {
        "name": "公众号-InfoQ",
        "url": "https://werss.tuber.cc/feed/MP_WXS_2390142780.atom"
    },
    {
        "name": "公众号-新智元",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3271041950.atom"
    },
    {
        "name": "公众号-机器之心",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3073282833.atom"
    },
    {
        "name": "公众号-量子位",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3236757533.atom"
    },
    {
        "name": "公众号-数字生命卡兹克",
        "url": "https://werss.tuber.cc/feed/MP_WXS_3223096120.atom"
    }

]

# RSS源分批处理配置
RSS_BATCH_SIZE = 5  # 每批处理的RSS源数量
RSS_BATCH_DELAY = 2  # 批次间延迟（秒）

# 其他配置
TITLE_LENGTH = int(os.getenv('TITLE_LENGTH', '20'))
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '5'))
FILTER_DAYS = int(os.getenv('FILTER_DAYS', '1'))

# 科技相关的信息源列表
TECH_SOURCES = [
    # "bilibili",     # 含大量科技区UP主（评测/教程/极客）
    "zhihu",        # 科技类问答和专栏文章
    "sspai",        # 专注效率工具和科技应用
    "ithome",       # IT科技新闻门户
    "36kr",         # 科技创新创业资讯平台
    "juejin",       # 开发者技术社区
    "csdn",         # 专业技术博客平台
    "51cto",        # IT技术运维社区  
    "huxiu",        # 科技商业媒体
    "ifanr",        # 聚焦智能硬件的科技媒体
    # "coolapk",      # 安卓应用和科技产品讨论
    # "v2ex",         # 创意工作者技术社区
    # "hostloc",      # 服务器和网络技术交流
    # "hupu",         # 虎扑数码区（手机/电脑讨论）
    "guokr",        # 泛科学科普平台
    "hellogithub",  # GitHub开源项目推荐
    "nodeseek",     # 服务器和网络技术论坛
    "52pojie",      # 软件逆向技术社区
    # "ithome-xijiayi",# 免费软件/游戏资讯
    "zhihu-daily",  # 含科技类深度报道
    # "tieba",        # 百度贴吧（手机/电脑相关贴吧）
]

# 所有可用的信息源
ALL_SOURCES = [
    "bilibili",   # 哔哩哔哩
    "weibo",      # 微博
    "zhihu",      # 知乎
    "baidu",      # 百度
    "douyin",     # 抖音
    "kuaishou",   # 快手
    "tieba",      # 百度贴吧
    "sspai",      # 少数派
    "ithome",     # IT之家
    "toutiao",    # 今日头条
    "36kr",       # 36氪
    "juejin",     # 掘金
    "csdn",       # CSDN
    "51cto",      # 51CTO
    "huxiu",      # 虎嗅
    "ifanr",      # 爱范儿
    "coolapk",    # 酷安
    "hupu",       # 虎扑
    "v2ex",       # V2EX
    "hostloc",    # 全球主机交流
    "sina-news",  # 新浪新闻
    "netease-news", # 网易新闻
    "qq-news",    # 腾讯新闻
    "thepaper",   # 澎湃新闻
    "jianshu",    # 简书
    "guokr",      # 果壳
    "acfun",      # AcFun
    "douban-movie", # 豆瓣电影
    "douban-group", # 豆瓣讨论小组
    "zhihu-daily", # 知乎日报
    "ithome-xijiayi", # IT之家「喜加一」
    "ngabbs",     # NGA
    "hellogithub", # HelloGitHub
    "nodeseek",   # NodeSeek
    "miyoushe",   # 米游社
    "genshin",    # 原神
    "honkai",     # 崩坏3
    "starrail",   # 崩坏：星穹铁道
    "weread",     # 微信读书
    "lol",        # 英雄联盟
    "52pojie",    # 吾爱破解
]

# 添加源名称映射字典
SOURCE_NAME_MAP = {
    "bilibili": "哔哩哔哩",
    "weibo": "微博",
    "zhihu": "知乎",
    "baidu": "百度",
    "douyin": "抖音",
    "kuaishou": "快手",
    "tieba": "百度贴吧",
    "sspai": "少数派",
    "ithome": "IT之家",
    "toutiao": "今日头条",
    "36kr": "36氪",
    "juejin": "掘金",
    "csdn": "CSDN",
    "51cto": "51CTO",
    "huxiu": "虎嗅",
    "ifanr": "爱范儿",
    "coolapk": "酷安",
    "hupu": "虎扑",
    "v2ex": "V2EX",
    "hostloc": "全球主机交流",
    "sina-news": "新浪新闻",
    "netease-news": "网易新闻",
    "qq-news": "腾讯新闻",
    "thepaper": "澎湃新闻",
    "jianshu": "简书",
    "guokr": "果壳",
    "acfun": "AcFun",
    "douban-movie": "豆瓣电影",
    "douban-group": "豆瓣讨论小组",
    "zhihu-daily": "知乎日报",
    "ithome-xijiayi": "IT之家喜加一",
    "ngabbs": "NGA",
    "hellogithub": "HelloGitHub",
    "nodeseek": "NodeSeek",
    "miyoushe": "米游社",
    "genshin": "原神",
    "honkai": "崩坏3",
    "starrail": "崩坏：星穹铁道",
    "weread": "微信读书",
    "lol": "英雄联盟",
    "52pojie": "吾爱破解",
}
