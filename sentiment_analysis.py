# coding=utf-8
"""
弹幕情感分析工具
功能：自动分析清洗后的弹幕情感倾向，生成可视化图表
"""
import os
import glob
import time
from snownlp import SnowNLP
from pyecharts.charts import Bar
from pyecharts import options as opts
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def find_latest_cleaned_file():
    """查找cleaned_danmu_results目录中最新的清洗后弹幕文件"""
    if os.path.exists(config.COMBINED_CLEANED_TXT):
        print(f"使用清洗文件: {os.path.basename(config.COMBINED_CLEANED_TXT)}")
        return config.COMBINED_CLEANED_TXT
    else:
        print("未找到清洗后的弹幕文件，请先运行清洗程序")
        return None

def analyze_sentiment(input_file):
    """分析弹幕情感并生成可视化结果"""
    print("\n开始情感分析...")

    # 读取弹幕内容
    with open(input_file, 'r', encoding='utf-8') as f:
        danmakus = [line.strip() for line in f if line.strip()]

    print(f"共读取 {len(danmakus)} 条弹幕")

    # 情感分析
    sentiments = []
    print("正在分析弹幕情感...")
    for danmu in tqdm(danmakus, desc="情感分析进度"):
        try:
            s = SnowNLP(danmu)
            sentiments.append(s.sentiments)
        except:
            sentiments.append(0.5)  # 分析失败时使用中性值

    # 计算平均情感分数
    avg_sentiment = sum(sentiments) / len(sentiments)
    print(f"\n平均情感分数: {avg_sentiment:.4f} (范围: 0-1, 1表示最积极)")

    # 情感分布统计
    sentiment_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    sentiment_labels = ['非常负面', '负面', '中性', '正面', '非常正面']
    sentiment_counts = [0] * (len(sentiment_bins) - 1)

    for score in sentiments:
        for i in range(len(sentiment_bins) - 1):
            if sentiment_bins[i] <= score < sentiment_bins[i + 1]:
                sentiment_counts[i] += 1
                break

    # 显示情感分布摘要
    print("\n情感分布:")
    for i, category in enumerate(sentiment_labels):
        print(f"{category}: {sentiment_counts[i]}条弹幕 ({sentiment_counts[i]/len(sentiments)*100:.1f}%)")

    # 生成情感分布柱状图
    generate_sentiment_bar_chart(sentiment_labels, sentiment_counts, avg_sentiment)

    # 生成情感分数分布直方图
    generate_sentiment_histogram(sentiments, avg_sentiment)

    # 返回情感分析结果
    return {
        'average_sentiment': avg_sentiment,
        'sentiment_distribution': dict(zip(sentiment_labels, sentiment_counts))
    }

def generate_sentiment_bar_chart(labels, counts, avg_score):
    """生成情感分布柱状图（matplotlib 版本，避免 CDN 问题）"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    plt.figure(figsize=(10, 6))
    
    colors = ['#FF6B6B', '#FFA07A', '#FFD700', '#90EE90', '#4ECDC4']
    bars = plt.bar(labels, counts, color=colors, edgecolor='black', alpha=0.8)
    
    # 在柱子上方显示数值
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 5,
                str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.title(f'弹幕情感分布柱状图\n平均情感分: {avg_score:.4f} (共{sum(counts)}条弹幕)', 
              fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('情感类别', fontsize=12)
    plt.ylabel('弹幕数量', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # 添加颜色图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[i], label=labels[i]) for i in range(len(labels))]
    plt.legend(handles=legend_elements, loc='upper right')
    
    bar_file = os.path.join(config.CLEANED_DIR, "sentiment_bar_chart.png")
    plt.savefig(bar_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"情感分布柱状图已保存至: {bar_file}")
    return bar_file

def generate_sentiment_histogram(sentiments, avg_score):
    """生成情感分数分布直方图"""
    # 配置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    plt.figure(figsize=(12, 7))

    n, bins, patches = plt.hist(sentiments, bins=20, color='skyblue', edgecolor='black', alpha=0.7)

    plt.axvline(x=avg_score, color='red', linestyle='--', linewidth=2, 
                label=f'平均情感分: {avg_score:.4f}')

    plt.title('弹幕情感分数分布', fontsize=14)
    plt.xlabel('情感分数 (0=负面, 1=正面)', fontsize=12)
    plt.ylabel('弹幕数量', fontsize=12)

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.gca().set_facecolor('#f5f5f5')

    plt.legend(fontsize=12)

    plt.axvspan(0, 0.2, color='red', alpha=0.1)
    plt.axvspan(0.2, 0.4, color='orange', alpha=0.1)
    plt.axvspan(0.4, 0.6, color='yellow', alpha=0.1)
    plt.axvspan(0.6, 0.8, color='lightgreen', alpha=0.1)
    plt.axvspan(0.8, 1.0, color='green', alpha=0.1)

    plt.text(0.1, max(n)*0.9, '非常负面', ha='center', fontsize=10)
    plt.text(0.3, max(n)*0.9, '负面', ha='center', fontsize=10)
    plt.text(0.5, max(n)*0.9, '中性', ha='center', fontsize=10)
    plt.text(0.7, max(n)*0.9, '正面', ha='center', fontsize=10)
    plt.text(0.9, max(n)*0.9, '非常正面', ha='center', fontsize=10)

    hist_file = config.SENTIMENT_HISTOGRAM
    plt.savefig(hist_file, dpi=300, bbox_inches='tight')
    print(f"情感分数分布直方图已保存至: {hist_file}")
    return hist_file

def main():
    print("=" * 50)
    print("弹幕情感分析工具")
    print("=" * 50)

    # 步骤 1: 查找最新的清洗后弹幕文件
    input_file = find_latest_cleaned_file()
    if not input_file:
        return

    # 步骤 2: 进行情感分析
    sentiment_result = analyze_sentiment(input_file)

    # 注释掉容易出错的 HTML 生成，直接使用 PNG 直方图
    # generate_sentiment_bar_chart(sentiment_labels, sentiment_counts, avg_sentiment)

    print("\n分析完成！情感分布直方图 (PNG) 已保存至 cleaned_danmu_results 目录")


if __name__ == "__main__":
    main()