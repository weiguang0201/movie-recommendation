
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日影视推荐脚本 V3 - 实时数据 + 美化推送
优化版本：实时数据获取 + Markdown美化 + 智能重试
"""

import requests
import json
import time
from datetime import datetime

# 豆瓣API配置（多源备用）
DOUBAN_APIS = [
    {
        "name": "豆瓣官方API",
        "base": "https://api.douban.com/v2/movie",
        "need_apikey": False
    },
    {
        "name": "豆瓣镜像站1",
        "base": "https://douban.uieee.com/v2/movie",
        "need_apikey": True,
        "apikey": "0df993c66c0c636e29ecbb5344252a4a"
    }
]

# Server酱配置
SENDKEY = None


def fetch_with_retry(api_base, endpoint, params=None, max_retries=3):
    """带重试机制的API请求"""
    if params is None:
        params = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            url = f"{api_base}/{endpoint}"
            print(f"  [尝试 {attempt + 1}/{max_retries}] 请求: {url}")
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"  ✓ 成功获取数据")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ 请求失败: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            continue
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON解析失败: {e}")
            continue
    
    return None


def get_realtime_data_tv():
    """获取实时电视剧数据"""
    print("\n[电视剧] 开始获取实时数据...")
    
    # 方法1: 尝试豆瓣搜索电视剧
    for api in DOUBAN_APIS:
        print(f"\n[方法1] 尝试 {api['name']} - 搜索电视剧")
        
        params = {}
        if api.get('need_apikey'):
            params['apikey'] = api['apikey']
        params['tag'] = '电视剧'
        params['count'] = 10
        
        data = fetch_with_retry(api['base'], 'search', params)
        
        if data and 'subjects' in data and len(data['subjects']) > 0:
            print(f"✓ {api['name']} 成功！")
            return parse_douban_data(data['subjects'][:5], 'tv')
    
    # 方法2: 使用备用推荐列表（经典高分电视剧）
    print("\n[方法2] 使用高分电视剧推荐列表")
    return get_classic_tv_shows()


def get_realtime_data_movie():
    """获取实时电影数据"""
    print("\n[电影] 开始获取实时数据...")
    
    # 方法1: 尝试豆瓣新片榜
    for api in DOUBAN_APIS:
        print(f"\n[方法1] 尝试 {api['name']} - 新片榜")
        
        params = {}
        if api.get('need_apikey'):
            params['apikey'] = api['apikey']
        
        data = fetch_with_retry(api['base'], 'new_movies', params)
        
        if data and 'subjects' in data and len(data['subjects']) > 0:
            print(f"✓ {api['name']} 成功！")
            return parse_douban_data(data['subjects'][:5], 'movie')
    
    # 方法2: 尝试豆瓣Top250
    for api in DOUBAN_APIS:
        print(f"\n[方法2] 尝试 {api['name']} - Top250")
        
        params = {}
        if api.get('need_apikey'):
            params['apikey'] = api['apikey']
        params['start'] = 0
        params['count'] = 5
        
        data = fetch_with_retry(api['base'], 'top250', params)
        
        if data and 'subjects' in data and len(data['subjects']) > 0:
            print(f"✓ {api['name']} 成功！")
            return parse_douban_data(data['subjects'][:5], 'movie')
    
    # 方法3: 使用备用推荐列表
    print("\n[方法3] 使用高分电影推荐列表")
    return get_classic_movies()


def parse_douban_data(items, content_type):
    """解析豆瓣API数据"""
    results = []
    
    for item in items:
        if content_type == 'tv':
            # 电视剧数据
            results.append({
                'title': item.get('title', '未知'),
                'rating': item.get('rating', {}).get('average', 0),
                'year': item.get('year', '未知'),
                'genres': ', '.join(item.get('genres', [])),
                'directors': ', '.join([d['name'] for d in item.get('directors', [])]),
                'casts': ', '.join([c['name'] for c in item.get('casts', [])]),
                'url': f"https://movie.douban.com/subject/{item.get('id', '')}/"
            })
        else:
            # 电影数据
            results.append({
                'title': item.get('title', '未知'),
                'rating': item.get('rating', {}).get('average', 0),
                'year': item.get('year', '未知'),
                'genres': ', '.join(item.get('genres', [])),
                'directors': ', '.join([d['name'] for d in item.get('directors', [])]),
                'casts': ', '.join([c['name'] for c in item.get('casts', [])]),
                'url': f"https://movie.douban.com/subject/{item.get('id', '')}/"
            })
    
    return results


def get_classic_tv_shows():
    """经典电视剧推荐（备用数据）"""
    classic_shows = [
        {
            'title': '繁花',
            'rating': 8.5,
            'year': '2023',
            'genres': '剧情',
            'directors': '王家卫',
            'casts': '胡歌, 马伊琍, 唐嫣',
            'url': 'https://movie.douban.com/subject/35231322/'
        },
        {
            'title': '漫长的季节',
            'rating': 9.4,
            'year': '2023',
            'genres': '悬疑, 剧情',
            'directors': '辛爽',
            'casts': '范伟, 秦昊, 陈明昊',
            'url': 'https://movie.douban.com/subject/35230912/'
        },
        {
            'title': '狂飙',
            'rating': 8.5,
            'year': '2023',
            'genres': '剧情, 犯罪',
            'directors': '徐纪周',
            'casts': '张译, 张颂文, 李一桐',
            'url': 'https://movie.douban.com/subject/35465232/'
        },
        {
            'title': '三体',
            'rating': 8.0,
            'year': '2023',
            'genres': '科幻, 剧情',
            'directors': '杨磊',
            'casts': '张鲁一, 于和伟, 陈瑾',
            'url': 'https://movie.douban.com/subject/26797690/'
        },
        {
            'title': '去有风的地方',
            'rating': 8.7,
            'year': '2023',
            'genres': '剧情, 爱情',
            'directors': '丁梓光',
            'casts': '刘亦菲, 李现, 胡冰卿',
            'url': 'https://movie.douban.com/subject/35642423/'
        }
    ]
    return classic_shows


def get_classic_movies():
    """经典电影推荐（备用数据）"""
    classic_movies = [
        {
            'title': '奥本海默',
            'rating': 8.8,
            'year': '2023',
            'genres': '剧情, 传记',
            'directors': '克里斯托弗·诺兰',
            'casts': '基里安·墨菲, 艾米莉·布朗特, 马特·达蒙',
            'url': 'https://movie.douban.com/subject/34562342/'
        },
        {
            'title': '流浪地球2',
            'rating': 8.3,
            'year': '2023',
            'genres': '科幻, 冒险',
            'directors': '郭帆',
            'casts': '吴京, 刘德华, 李雪健',
            'url': 'https://movie.douban.com/subject/26266893/'
        },
        {
            'title': '蜘蛛侠：纵横宇宙',
            'rating': 8.6,
            'year': '2023',
            'genres': '动画, 动作',
            'directors': '华金·多斯·桑托斯',
            'casts': '沙梅克·摩尔, 海莉·斯坦菲尔德',
            'url': 'https://movie.douban.com/subject/34562342/'
        },
        {
            'title': '芭比',
            'rating': 8.3,
            'year': '2023',
            'genres': '喜剧, 奇幻',
            'directors': '格蕾塔·葛韦格',
            'casts': '玛格特·罗比, 瑞恩·高斯林',
            'url': 'https://movie.douban.com/subject/35106807/'
        },
        {
            'title': '银河护卫队3',
            'rating': 8.4,
            'year': '2023',
            'genres': '科幻, 冒险',
            'directors': '詹姆斯·古恩',
            'casts': '克里斯·帕拉特, 佐伊·索尔达娜',
            'url': 'https://movie.douban.com/subject/26184657/'
        }
    ]
    return classic_movies


def format_markdown_message(tv_shows, movies):
    """格式化美化Markdown推送消息"""
    today = datetime.now()
    date_display = today.strftime("%Y年%m月%d日")
    weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]
    
    # 顶部标题
    message = f"""# 📺 每日影视推荐

> **{date_display} {weekday}**
> 数据来源：豆瓣电影

---

"""

    # 热门电视剧
    message += f"## 🔥 热门电视剧 TOP5\n\n"
    
    for i, tv in enumerate(tv_shows, 1):
        # 评分颜色
        if tv['rating'] >= 9.0:
            rating_emoji = "⭐⭐⭐"
        elif tv['rating'] >= 8.0:
            rating_emoji = "⭐⭐"
        else:
            rating_emoji = "⭐"
        
        message += f"""### {i}. [{tv['title']}]({tv['url']})

{rating_emoji} **评分 **: {tv['rating']}/10
📅 **年份 **: {tv['year']}
🎭 **类型 **: {tv['genres']}
🎬 **导演 **: {tv['directors']}
👥 **主演 **: {tv['casts']}

---

"""

    # 热门电影
    message += f"## 🎬 热门电影 TOP5\n\n"
    
    for i, movie in enumerate(movies, 1):
        # 评分颜色
        if movie['rating'] >= 9.0:
            rating_emoji = "⭐⭐⭐"
        elif movie['rating'] >= 8.0:
            rating_emoji = "⭐⭐"
        else:
            rating_emoji = "⭐"
        
        message += f"""### {i}. [{movie['title']}]({movie['url']})

{rating_emoji} **评分 **: {movie['rating']}/10
📅 **年份 **: {movie['year']}
🎭 **类型 **: {movie['genres']}
🎬 **导演 **: {movie['directors']}
👥 **主演 **: {movie['casts']}

---

"""

    # 底部
    message += f"""
---

💡 **温馨提示**
> 每天早上10点准时推送
> 点击电影名称可直接跳转豆瓣查看详情

*本推荐由AI自动生成，数据仅供参考*
"""

    return message


def send_to_wechat(title, content):
    """通过Server酱发送Markdown格式的微信消息"""
    if not SENDKEY:
        print("错误: 未配置SENDKEY")
        return False
    
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    
    data = {
        'title': title,
        'desp': conte
