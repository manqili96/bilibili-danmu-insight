# coding=utf-8
import time
import jieba
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from snownlp import SnowNLP
import matplotlib.font_manager as fm
from matplotlib.gridspec import GridSpec
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# 设置全局绘图样式
plt.style.use('seaborn-whitegrid')
sns.set_palette("Set2")

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


# 解决中文显示问题
wordcloud_font_path = None

def setup_chinese_font():
    """配置中文字体支持"""
    global wordcloud_font_path
    
    try:
        # 1. 查找系统中可用的中文字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong',
                         'Arial Unicode MS', 'Noto Sans CJK SC', 'Source Han Sans SC']

        # 2. 尝试设置Matplotlib全局字体
        for font_name in chinese_fonts:
            if any(font_name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams['font.family'] = font_name
                plt.rcParams['axes.unicode_minus'] = False
                print(f"已设置Matplotlib全局字体: {font_name}")
                break
        else:
            # 如果找不到中文字体，尝试添加字体文件
            print("未找到系统中文字体，尝试添加备用字体")
            try:
                # 添加备用字体文件
                font_path = os.path.join(os.path.dirname(__file__), 'SimHei.ttf')
                if os.path.exists(font_path):
                    fm.fontManager.addfont(font_path)
                    prop = fm.FontProperties(fname=font_path)
                    plt.rcParams['font.family'] = prop.get_name()
                    plt.rcParams['axes.unicode_minus'] = False
                    print(f"已添加备用字体: {font_path}")
            except Exception as e:
                print(f"添加备用字体失败: {e}")

        # 3. 设置WordCloud默认字体路径
        wordcloud_font_path = None
        for font_name in chinese_fonts:
            for f in fm.findSystemFonts():
                if font_name.lower() in os.path.basename(f).lower():
                    wordcloud_font_path = f
                    print(f"已设置WordCloud字体: {wordcloud_font_path}")
                    break
            if wordcloud_font_path:
                break

        # 4. 如果仍然找不到，使用matplotlib的默认字体
        if not wordcloud_font_path:
            wordcloud_font_path = fm.findfont(fm.FontProperties(family='sans-serif'))
            print(f"使用默认字体: {wordcloud_font_path}")

    except Exception as e:
        print(f"字体配置错误: {e}")


# 初始化字体设置
setup_chinese_font()

# 停用词文件路径
stopwords_path = config.STOPWORDS_FILE

# 1. 自动查找最新的清洗后弹幕文件
def find_latest_cleaned_file():
    """查找 cleaned_danmu_results 目录中最新的清洗后弹幕文件"""
    if os.path.exists(config.COMBINED_CLEANED_TXT):
        return config.COMBINED_CLEANED_TXT
    else:
        print("未找到清洗后的弹幕文件，请先运行清洗程序")
        return None


# 2. 加载停用词
def load_stopwords():
    """加载停用词表"""
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except Exception as e:
        print(f"加载停用词失败: {e}")
        return set()


# 3. 分词处理
def segment_text(input_file, stop_words):
    """对文本进行分词处理"""
    if not input_file:
        return [], "", []

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(config.CLEANED_DIR, f"{base_name}_segmented.txt")

    all_words = []
    docs = []

    try:
        with open(output_file, 'w', encoding='utf-8') as f_out, \
                open(input_file, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                if not line:
                    continue

                seg_list = jieba.cut(line, cut_all=False)
                filtered_words = [word for word in seg_list if word not in stop_words and len(word) > 1 and not word.isdigit()]

                if filtered_words:
                    f_out.write(" ".join(filtered_words) + "\n")
                    all_words.extend(filtered_words)
                    docs.append(" ".join(filtered_words))

        print(f"分词完成，共处理 {len(all_words)} 个词语")
        return all_words, output_file, docs
    except Exception as e:
        print(f"分词处理失败: {e}")
        return [], "", []


# 4. 词频统计
def count_word_frequency(words):
    """统计词频并保存结果"""
    if not words:
        return Counter(), ""

    c = Counter(words)
    result_file = os.path.join(config.CLEANED_DIR, "word_frequency.csv")

    try:
        with open(result_file, 'w', encoding='utf-8') as fw:
            fw.write("排名,词语,频次\n")
            for i, (word, freq) in enumerate(c.most_common(), 1):
                fw.write(f"{i},{word},{freq}\n")

        return c, result_file
    except Exception as e:
        print(f"保存词频统计失败: {e}")
        return c, ""


# 5. 生成词云
def generate_wordcloud(counter, top_n=80):
    """生成词云图"""
    if not counter:
        return ""

    word_freq = dict(counter.most_common(top_n))

    try:
        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path=wordcloud_font_path
        ).generate_from_frequencies(word_freq)
    except Exception as e:
        print(f"生成词云失败: {e}")
        return ""

    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title('弹幕高频词云图', fontsize=16)

    output_file = config.WORDCLOUD_IMG

    try:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        return output_file
    except Exception as e:
        print(f"保存词云图失败: {e}")
        return ""


# 6. 聚类分析（简化版）
def cluster_analysis(docs, counter):
    """执行聚类分析"""
    if not docs or not counter:
        return {}, {}

    print("\n开始聚类分析...")

    try:
        # 文本向量化
        vectorizer = TfidfVectorizer(max_features=50)  # 限制特征数量
        X = vectorizer.fit_transform(docs)

        # 确定聚类数（固定为3 - 5个主题）
        n_clusters = min(5, max(3, len(docs) // 20))

        # 执行聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)

        # 提取聚类关键词
        cluster_keywords = {}
        theme_names = []  # 存储主题名称的列表
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

        # 兼容不同版本的sklearn
        if hasattr(vectorizer, 'get_feature_names_out'):
            terms = vectorizer.get_feature_names_out()
        elif hasattr(vectorizer, 'get_feature_names'):
            terms = vectorizer.get_feature_names()
        else:
            terms = []

        for i in range(n_clusters):
            keywords = [terms[ind] for ind in order_centroids[i, :10] if ind < len(terms)]
            # 使用前两个关键词作为主题名称
            theme_name = " ".join(keywords[:2]) if keywords else f"主题{i + 1}"
            cluster_keywords[theme_name] = keywords
            theme_names.append(theme_name)

        # 分析聚类情感
        cluster_sentiment = {}
        cluster_counts = np.bincount(clusters)

        for i in range(n_clusters):
            cluster_docs = [docs[j] for j in range(len(docs)) if clusters[j] == i]
            if not cluster_docs:
                continue

            sentiments = [SnowNLP(doc).sentiments for doc in cluster_docs]

            positive = sum(1 for s in sentiments if s > 0.6) / len(sentiments)
            neutral = sum(1 for s in sentiments if 0.4 <= s <= 0.6) / len(sentiments)
            negative = sum(1 for s in sentiments if s < 0.4) / len(sentiments)

            cluster_sentiment[theme_names[i]] = {
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "count": cluster_counts[i],
                "percentage": cluster_counts[i] / len(docs)
            }

        # 生成可视化结果
        visualize_clusters(cluster_keywords, cluster_sentiment)

        return cluster_keywords, cluster_sentiment
    except Exception as e:
        print(f"聚类分析失败: {e}")
        return {}, {}


# 7. 可视化聚类结果（优化版）
def visualize_clusters(cluster_keywords, cluster_sentiment):
    """生成聚类可视化图表"""
    if not cluster_keywords or not cluster_sentiment:
        return

    os.makedirs(config.CLUSTER_DIR, exist_ok=True)

    try:
        # 创建综合图表
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(2, 2, figure=fig)

        # 1. 主题分布饼图
        ax1 = fig.add_subplot(gs[0, 0])
        theme_names = list(cluster_keywords.keys())
        theme_counts = [cluster_sentiment[theme]['count'] for theme in theme_names]
        wedges, texts, autotexts = ax1.pie(theme_counts, labels=None, autopct='%1.1f%%', startangle=90, pctdistance=0.8, labeldistance=1.2)

        legend_labels = []
        for i, wedge in enumerate(wedges):
            color = wedge.get_facecolor()
            legend_labels.append(f"{theme_names[i]}: {cluster_sentiment[theme_names[i]]['count']}条弹幕 ({cluster_sentiment[theme_names[i]]['percentage']*100:.1f}%)")
            ax1.text(0, 0, '', bbox=dict(facecolor=color, alpha=0.5))
        ax1.legend(legend_labels, loc='center left', bbox_to_anchor=(-0.3, 0))  # 调整图例位置，饼图整体左移
        ax1.set_title('主题分布', fontsize=14)

        # 2. 情感分布柱状图
        ax2 = fig.add_subplot(gs[0, 1])
        bar_width = 0.6
        index = np.arange(len(theme_names))
        positive_heights = [cluster_sentiment[theme]['positive'] for theme in theme_names]
        neutral_heights = [cluster_sentiment[theme]['neutral'] for theme in theme_names]
        negative_heights = [cluster_sentiment[theme]['negative'] for theme in theme_names]

        positive_color = '#4CAF50'  # 绿色
        neutral_color = '#2196F3'  # 蓝色
        negative_color = '#F44336'  # 红色

        p1 = ax2.bar(index, positive_heights, bar_width, color=positive_color, label='积极')
        p2 = ax2.bar(index, neutral_heights, bar_width, bottom=positive_heights, color=neutral_color, label='中性')
        p3 = ax2.bar(index, negative_heights, bar_width,
                    bottom=[i + j for i, j in zip(positive_heights, neutral_heights)],
                    color=negative_color, label='消极')

        ax2.set_xticks(index)
        ax2.set_xticklabels(theme_names, rotation=45, ha='right', fontsize=10)
        ax2.set_title('情感分布', fontsize=14)
        ax2.set_ylabel('情感比例', fontsize=12)
        ax2.legend(loc='upper right', bbox_to_anchor=(1.15, 1))

        # 3. 主题关键词展示
        ax3 = fig.add_subplot(gs[1, :])
        ax3.axis('off')
        table_data = []
        for theme in theme_names:
            table_data.append(cluster_keywords[theme])

        table = ax3.table(cellText=table_data,
                          rowLabels=theme_names,
                          colLabels=[f"关键词{i + 1}" for i in range(10)],
                          loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        for key, cell in table.get_celld().items():
            cell.set_fontsize(10)

        ax3.set_title('主题关键词', fontsize=14, y=0.95)

        # 调整布局，增大图表之间的垂直间距
        plt.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.92, hspace=0.5, wspace=0.3)

        # 固定文件名
        output_file = "D:\\b_zhan_danmu_data\\cluster_results\\cluster_summary.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close(fig)

    except Exception as e:
        print(f"可视化聚类结果失败: {e}")


# 8. 显示统计摘要
def show_summary(counter, cluster_keywords=None, cluster_sentiment=None):
    """显示统计摘要"""
    if not counter:
        return

    print("\n词频统计摘要:")
    print(f"总词语数: {sum(counter.values())}")
    print(f"唯一词语数: {len(counter)}")

    if counter:
        print("高频词TOP10:")
        for rank, (word, freq) in enumerate(counter.most_common(10), 1):
            print(f"{rank}. {word}: {freq}次")

    if cluster_keywords and cluster_sentiment:
        print("\n聚类分析摘要:")
        for theme in cluster_keywords:
            if theme in cluster_sentiment:
                perc = cluster_sentiment[theme]['percentage'] * 100
                print(f"- {theme}: {cluster_sentiment[theme]['count']}条弹幕 ({perc:.1f}%)")
                print(f"  关键词: {', '.join(cluster_keywords[theme][:5])}...")
                print(f"  情感: 积极{cluster_sentiment[theme]['positive'] * 100:.1f}% | " +
                      f"中性{cluster_sentiment[theme]['neutral'] * 100:.1f}% | " +
                      f"消极{cluster_sentiment[theme]['negative'] * 100:.1f}%")


# 8.5. 时间序列分析
def analyze_time_series():
    """分析弹幕密度和情感随时间的变化"""
    import pandas as pd
    
    if not os.path.exists(config.COMBINED_CLEANED_CSV):
        print("未找到清洗后的CSV文件，跳过时间序列分析")
        return
    
    try:
        df = pd.read_csv(config.COMBINED_CLEANED_CSV)
        
        if 'time' not in df.columns:
            print("CSV中缺少time字段，跳过时间序列分析")
            return
        
        # 弹幕密度分析
        time_bins = pd.cut(df['time'], bins=60, labels=False)
        density = df.groupby(time_bins).size()
        
        # 情感分析（如果需要）
        sentiments = []
        if 'cleaned' in df.columns:
            from snownlp import SnowNLP
            for text in df['cleaned'].head(1000):
                try:
                    sentiments.append(SnowNLP(str(text)).sentiments)
                except:
                    sentiments.append(0.5)
        
        # 可视化
        fig, ax1 = plt.subplots(figsize=(14, 6))
        
        # 弹幕密度
        x = range(len(density))
        ax1.fill_between(x, density.values, alpha=0.3, color='#4ECDC4', label='弹幕密度')
        ax1.plot(x, density.values, color='#4ECDC4', linewidth=2)
        ax1.set_xlabel('视频进度 (秒)', fontsize=12)
        ax1.set_ylabel('弹幕数量', fontsize=12, color='#4ECDC4')
        ax1.tick_params(axis='y', labelcolor='#4ECDC4')
        
        # 叠加情感趋势（如果有）
        if sentiments:
            ax2 = ax1.twinx()
            sentiment_smooth = np.convolve(sentiments, np.ones(20)/20, mode='valid')
            x_sentiment = np.linspace(0, len(density)-1, len(sentiment_smooth))
            ax2.plot(x_sentiment, sentiment_smooth, color='#FF6B6B', linewidth=2, label='情感趋势')
            ax2.set_ylabel('情感分数', fontsize=12, color='#FF6B6B')
            ax2.tick_params(axis='y', labelcolor='#FF6B6B')
        
        plt.title('弹幕密度与情感趋势分析', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        if sentiments:
            ax2.legend(loc='upper right')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_file = config.TIME_SERIES_IMG
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"时间序列分析图已保存: {output_file}")
        
    except Exception as e:
        print(f"时间序列分析失败: {e}")


def compare_videos():
    """对比多个视频的主题分布"""
    import pandas as pd
    import traceback
    
    if not os.path.exists(config.COMBINED_CLEANED_CSV):
        print("未找到清洗后的CSV文件，跳过视频对比")
        return
    
    try:
        df = pd.read_csv(config.COMBINED_CLEANED_CSV)
        
        if 'video_title' not in df.columns or df['video_title'].nunique() < 2:
            print(f"视频数量不足，跳过视频对比")
            return
        
        videos = df['video_title'].unique()
        
        if len(videos) > 5:
            print(f"\n⚠️ 输入视频超过 5 个，系统自动截取前 5 个")
            videos = videos[:5]
        else:
            print(f"\n开始视频对比分析：共 {len(videos)} 个视频")
        
        # 加载停用词
        stop_words = load_stopwords()
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        video_results = {}
        for video in videos:
            video_df = df[df['video_title'] == video]
            # 新增：分词时过滤停用词
            video_docs = []
            for text in video_df['cleaned']:
                if len(str(text)) > 1:
                    words = [w for w in jieba.cut(str(text)) if w not in stop_words and len(w) > 1 and not w.isdigit()]
                    if words:
                        video_docs.append(' '.join(words))
            
            if len(video_docs) < 10: continue
            
            vectorizer = TfidfVectorizer(max_features=30)
            X = vectorizer.fit_transform(video_docs)
            
            n_clusters = min(5, max(3, len(video_docs) // 10))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
            
            terms = vectorizer.get_feature_names_out() if hasattr(vectorizer, 'get_feature_names_out') else vectorizer.get_feature_names()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            theme_names, theme_counts = [], []
            for i in range(n_clusters):
                keywords = [terms[ind] for ind in order_centroids[i, :3] if ind < len(terms)]
                theme_names.append(" ".join(keywords) if keywords else f"主题{i+1}")
                theme_counts.append(int(np.sum(clusters == i)))
            
            video_results[video] = {'themes': theme_names, 'counts': theme_counts}
        
        if len(video_results) < 2: return

        n = len(video_results)
        if n == 2:
            fig, axes = plt.subplots(2, 1, figsize=(10, 12))
        elif n == 3:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        elif n == 4:
            fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        else:
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            axes[1, 2].axis('off')
            axes = axes.flatten()
        
        axes = [axes] if n == 1 else (axes.flatten() if n > 2 else axes)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for idx, (video, res) in enumerate(video_results.items()):
            ax = axes[idx]
            ax.pie(res['counts'], labels=None, autopct='%1.1f%%', startangle=90, colors=colors[:len(res['themes'])])
            
            legend = [f"{res['themes'][i]}: {res['counts'][i]}条" for i in range(len(res['themes']))]
            ax.legend(legend, loc='center left', bbox_to_anchor=(-0.1, 0.5), fontsize=9)
            ax.set_title(f'视频 {idx+1}: {video[:20]}...', fontsize=12, fontweight='bold')
        
        plt.suptitle('视频主题分布对比', fontsize=16, fontweight='bold', y=1.05)
        plt.tight_layout()
        
        output_file = os.path.join(config.CLUSTER_DIR, "video_comparison.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"对比图已保存: {output_file}")
        
    except Exception as e:
        print(f"视频对比分析失败: {e}")
        traceback.print_exc()


def main():
    print("=" * 50)
    print("弹幕文本分析与聚类工具")
    print("=" * 50)

    input_file = find_latest_cleaned_file()
    if not input_file:
        return

    stop_words = load_stopwords()
    all_words, segmented_file, docs = segment_text(input_file, stop_words)
    word_counter, freq_file = count_word_frequency(all_words)

    wordcloud_file = generate_wordcloud(word_counter)
    if wordcloud_file:
        print(f"词云已保存至: {wordcloud_file}")

    analyze_time_series()
    compare_videos()

    if len(docs) >= 20:
        cluster_keywords, cluster_sentiment = cluster_analysis(docs, word_counter)
    else:
        print("\n弹幕数量不足，跳过聚类分析")
        cluster_keywords = cluster_sentiment = None

    show_summary(word_counter, cluster_keywords, cluster_sentiment)
    print("\n处理完成!")


if __name__ == "__main__":
    jieba.initialize()
    main()