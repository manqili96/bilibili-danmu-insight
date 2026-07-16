import re
import requests
import json
import os
import time
import xml.etree.ElementTree as ET
import pandas as pd
import datetime
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# 配置文件路径
CONFIG_FILE = "bili_config.json"

# 随机User-Agent生成器
def get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ]
    return random.choice(agents)

## 旧的cookies配置存储和载入函数
def save_config(cookie, save_path=None):
    """保存配置到本地文件"""
    cfg = {
        "cookie": cookie,
        "save_path": save_path or config.DATA_DIR
    }
    config_file = os.path.join(config.PROJECT_ROOT, "bili_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_config():
    """从本地文件加载配置"""
    config_file = os.path.join(config.PROJECT_ROOT, "bili_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def extract_bvid(url):
    """从B站视频URL中提取BV号"""
    # 尝试直接匹配BV号
    bvid_match = re.search(r"(BV\w+)", url)
    if bvid_match:
        return bvid_match.group(1)

    # 如果是短链接，需要解析
    if "b23.tv" in url:
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            final_url = response.url
            bvid_match = re.search(r"video/(BV\w+)", final_url)
            if bvid_match:
                return bvid_match.group(1)
        except:
            pass

    return None

def get_cid(video_url):
    """
    从视频页面获取cid (弹幕ID)

    Args:
        video_url: B站视频URL

    Returns:
        cid: 视频的弹幕ID
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Referer": "https://www.bilibili.com/"
    }

    try:
        response = requests.get(video_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"获取视频页面失败: HTTP {response.status_code}")
            return None

        # 使用正则表达式提取cid
        match = re.search(r'"cid":(\d+)', response.text)
        if match:
            return match.group(1)
        else:
            print("在视频页面中未找到cid")
            return None
    except Exception as e:
        print(f"获取cid时出错: {e}")
        return None

def get_video_info(bvid):
    """通过BV号获取视频信息"""
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "user-agent": get_random_user_agent(),
        "referer": f"https://www.bilibili.com/video/{bvid}/"
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()

        if data.get("code") == 0:
            # 获取发布日期和标题
            pub_date = datetime.datetime.fromtimestamp(data["data"]["pubdate"]).strftime('%Y-%m-%d')
            title = data["data"]["title"]

            return {
                "pub_date": pub_date,
                "title": title
            }
        else:
            print(f"API返回错误: code={data.get('code')}, message={data.get('message')}")
            return None
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None

def parse_danmaku_xml(xml_content):
    """
    解析弹幕XML数据

    Args:
        xml_content: XML格式的弹幕数据

    Returns:
        list: 弹幕数据列表，每个元素是一个字典
    """
    try:
        # 解析XML
        root = ET.fromstring(xml_content)
        danmaku_list = []

        # 弹幕存储在 <d> 标签中
        for d in root.findall("d"):
            attributes = d.attrib
            content = d.text  # 弹幕内容
            p = attributes.get("p", "")

            if p:
                params = p.split(",")
                if len(params) >= 7:
                    danmaku = {
                        "time": float(params[0]),  # 弹幕出现时间 (秒)
                        "mode": int(params[1]),    # 弹幕模式
                        "font_size": int(params[2]),  # 字体大小
                        "color": int(params[3]),   # 颜色 (十进制 RGB)
                        "timestamp": int(params[4]),  # 弹幕发送时间戳
                        "pool": int(params[5]),    # 弹幕池
                        "user_hash": params[6],    # 用户哈希
                        "content": content         # 弹幕内容
                    }
                    danmaku_list.append(danmaku)
        return danmaku_list
    except Exception as e:
        print(f"解析弹幕XML时出错: {e}")
        return []

def fetch_danmaku(cid):
    """
    根据cid获取弹幕数据（普通弹幕API）

    Args:
        cid: 视频的弹幕ID

    Returns:
        bytes: XML格式的弹幕数据
    """
    url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Referer": f"https://www.bilibili.com/video/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content
        else:
            print(f"获取弹幕失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"获取弹幕时出错: {e}")
        return None

def save_danmu_to_file(danmakus, filename, save_path=None, video_title=None):
    """将弹幕内容保存到本地文件（CSV格式）"""
    if not save_path:
        save_path = os.getcwd()

    # 确保目录存在
    os.makedirs(save_path, exist_ok=True)

    if not danmakus:
        print("没有弹幕数据可保存")
        return None

    # 创建数据框
    df = pd.DataFrame(danmakus)

    # 添加视频标题信息
    if video_title:
        df['video_title'] = video_title

    # 保存为CSV
    csv_path = os.path.join(save_path, f"{filename}.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # 同时保存为文本文件（仅内容）
    txt_path = os.path.join(save_path, f"{filename}_content.txt")
    with open(txt_path, 'w', encoding='utf-8') as file:
        for danmu in danmakus:
            file.write(danmu['content'] + '\n')

    print(f"\n弹幕文件已保存至: {csv_path} (结构化数据)")
    print(f"弹幕内容已保存至: {txt_path} (纯文本)")
    print(f"共保存 {len(danmakus)} 条弹幕")
    return csv_path

def crawl_single_video(video_url, save_path):
    """爬取单个视频的弹幕"""
    # 获取视频BV号
    bvid = extract_bvid(video_url)
    if not bvid:
        print(f"无法从URL中提取视频ID: {video_url}")
        return None

    print(f"\n{'='*50}")
    print(f"开始处理视频: {bvid}")

    # 从视频页面获取cid
    cid = get_cid(video_url)
    if not cid:
        print("获取视频cid失败，请检查链接是否正确")
        return None

    print(f"获取到的cid: {cid}")

    # 获取视频信息（标题）
    video_info = get_video_info(bvid)
    if not video_info:
        print("获取视频信息失败，将使用默认值")
        video_title = f"视频_{bvid}"
    else:
        video_title = video_info["title"]

    print(f"视频标题: {video_title}")

    # 获取弹幕数据
    xml_content = fetch_danmaku(cid)
    if not xml_content:
        print("获取弹幕数据失败")
        return None

    # 解析弹幕
    danmakus = parse_danmaku_xml(xml_content)

    if not danmakus:
        print("未获取到弹幕数据")
        return None

    # 生成文件名（使用视频标题，去掉时间戳以支持覆盖）
    safe_title = re.sub(r'[\\/*?:"<>|]', "", video_title)[:50]
    filename = f"{safe_title}"

    # 保存弹幕
    file_path = save_danmu_to_file(danmakus, filename, save_path, video_title)

    print(f"视频 {video_title} 弹幕爬取完成")
    return file_path

def get_video_count():
    """获取用户要爬取的视频数量"""
    while True:
        try:
            count = int(input("请输入要爬取的视频数量(1-10): "))
            if 1 <= count <= 10:
                return count
            else:
                print("请输入1到10之间的数字")
        except ValueError:
            print("请输入有效的数字")

def get_video_urls(count):
    """依次获取每个视频的链接"""
    urls = []
    print(f"\n请依次输入{count}个视频链接(输入一个按一次回车):")
    for i in range(count):
        while True:
            url = input(f"视频 {i+1}/{count}: ").strip()
            if url:
                urls.append(url)
                break
            else:
                print("链接不能为空，请重新输入")
    return urls

def main():
    print("=" * 50)
    print("B站弹幕爬取工具")
    print("=" * 50)

    # 尝试加载本地配置
    config_data = load_config()
    save_path = config_data.get("save_path") if config_data else None

    # 获取视频数量
    video_count = get_video_count()

    # 获取视频链接
    video_urls = get_video_urls(video_count)

    # 清空所有旧数据（确保独立性）
    import shutil
    for directory in [config.BILIDANMU_DIR, config.CLEANED_DIR, config.CLUSTER_DIR]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
            print(f"已清空目录: {directory}")

    print("\n" + "=" * 50)
    print(f"开始爬取 {len(video_urls)} 个视频的弹幕...")
    print(f"结果将保存至: {os.path.abspath(config.BILIDANMU_DIR)}")

    # 爬取每个视频的弹幕
    results = []
    for i, video_url in enumerate(video_urls):
        print(f"\n处理视频 {i+1}/{len(video_urls)}: {video_url}")
        result = crawl_single_video(video_url, config.BILIDANMU_DIR)
        if result:
            results.append(result)
        # 视频之间添加延迟，避免请求过于频繁
        time.sleep(1)

    print("\n" + "=" * 50)
    print(f"所有视频弹幕爬取完成！共处理 {len(results)} 个视频") 
    print("\n操作完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()