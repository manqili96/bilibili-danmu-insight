import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据目录（强制使用 D 盘）
DATA_DIR = "D:\\b_zhan_danmu_data"
BILIDANMU_DIR = os.path.join(DATA_DIR, "bili_danmu_results")
CLEANED_DIR = os.path.join(DATA_DIR, "cleaned_danmu_results")
CLUSTER_DIR = os.path.join(DATA_DIR, "cluster_results")

# 确保目录存在
for directory in [DATA_DIR, BILIDANMU_DIR, CLEANED_DIR, CLUSTER_DIR]:
    os.makedirs(directory, exist_ok=True)

# 文件路径常量
COMBINED_CLEANED_TXT = os.path.join(CLEANED_DIR, "combined_cleaned_danmu.txt")
COMBINED_CLEANED_CSV = os.path.join(CLEANED_DIR, "combined_cleaned_danmu.csv")
WORDCLOUD_IMG = os.path.join(CLEANED_DIR, "wordcloud.png")
SENTIMENT_HISTOGRAM = os.path.join(CLEANED_DIR, "sentiment_histogram.png")
CLUSTER_SUMMARY = os.path.join(CLUSTER_DIR, "cluster_summary.png")
TIME_SERIES_IMG = os.path.join(CLEANED_DIR, "time_series_analysis.png")
DATA_QUALITY_IMG = os.path.join(CLEANED_DIR, "data_quality_report.png")
VIDEO_COMPARISON_IMG = os.path.join(CLUSTER_DIR, "video_comparison.png")
STOPWORDS_FILE = os.path.join(PROJECT_ROOT, "cn_stopwords.txt")
