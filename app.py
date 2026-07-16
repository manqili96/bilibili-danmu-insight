import streamlit as st
import pandas as pd
import os
import subprocess
import sys
import config
import ai_insight

from datetime import datetime

st.set_page_config(
    page_title="B 站弹幕舆情分析看板", 
    page_icon="📊",
    layout="wide"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<p class="main-header">📊 B 站弹幕舆情分析系统</p>', unsafe_allow_html=True)
st.markdown("---")

# 强制刷新图片的辅助函数
def get_local_image(path):
    """读取本地图片二进制，绕过 Streamlit 的文件路径缓存"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

def check_files_exist():
    """检查所有生成的文件是否存在"""
    files = {
        '数据质量报告': config.DATA_QUALITY_IMG,
        '情感分布直方图': config.SENTIMENT_HISTOGRAM,
        '时间序列分析': config.TIME_SERIES_IMG,
        '词云图': config.WORDCLOUD_IMG,
        '聚类主题图': config.CLUSTER_SUMMARY,
        '视频对比图': config.VIDEO_COMPARISON_IMG
    }
    return {name: os.path.exists(path) for name, path in files.items()}

# 侧边栏
with st.sidebar:
    st.sidebar.empty() # ✅ 新增：每次运行前清空侧边栏，防止重复显示
    st.header("🚀 任务启动")
    
    num_videos = st.number_input("爬取视频数量 (1-10)", min_value=1, max_value=10, value=3)
    video_urls = st.text_area("输入视频链接 (每行一个)", height=150, 
                              placeholder="https://www.bilibili.com/video/BV1xxx...\nhttps://www.bilibili.com/video/BV1yyy...")
    
    if st.button("开始全流程分析", type="primary", use_container_width=True):
        if video_urls:
            urls_list = [url.strip() for url in video_urls.split('\n') if url.strip()]
            if len(urls_list) >= num_videos:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 1. 运行爬虫
                    status_text.text("⏳ 步骤 1/4: 正在爬取弹幕...")
                    input_data = f"{num_videos}\n" + "\n".join(urls_list) + "\n"
                    result = subprocess.run(
                        [sys.executable, os.path.join(config.PROJECT_ROOT, "danmu_crawler.py")],
                        input=input_data, capture_output=True, text=True, encoding='utf-8',
                        errors='replace'
                    )
                    if result.returncode != 0:
                        st.error(f"❌ 爬虫执行失败:\n{result.stderr}")
                        st.stop()
                    progress_bar.progress(25)
                    
                    # 2. 运行清洗
                    status_text.text("⏳ 步骤 2/4: 正在清洗数据...")
                    result = subprocess.run(
                        [sys.executable, os.path.join(config.PROJECT_ROOT, "danmu_cleaner.py")],
                        capture_output=True, text=True, encoding='utf-8',
                        errors='replace'
                    )
                    if result.returncode != 0:
                        st.error(f"❌ 数据清洗失败:\n{result.stderr}")
                        st.stop()
                    progress_bar.progress(50)
                    
                    # 3. 运行词频
                    status_text.text("⏳ 步骤 3/4: 正在分析词频与聚类...")
                    result = subprocess.run(
                        [sys.executable, os.path.join(config.PROJECT_ROOT, "word_frequency_analysis.py")],
                        capture_output=True, text=True, encoding='utf-8',
                        errors='replace'
                    )
                    if result.returncode != 0:
                        st.error(f"❌ 词频分析失败:\n{result.stderr}")
                        st.stop()
                    progress_bar.progress(75)
                    
                    # 4. 运行情感
                    status_text.text("⏳ 步骤 4/4: 正在分析情感倾向...")
                    result = subprocess.run(
                        [sys.executable, os.path.join(config.PROJECT_ROOT, "sentiment_analysis.py")],
                        capture_output=True, text=True, encoding='utf-8',
                        errors='replace'
                    )
                    if result.returncode != 0:
                        st.error(f"❌ 情感分析失败:\n{result.stderr}")
                        st.stop()
                    progress_bar.progress(100)
                    
                    status_text.success("✅ 全流程分析完成！")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ 执行过程中出现错误: {str(e)}")
            else:
                st.error(f"⚠️ 你只输入了 {len(urls_list)} 个链接，需要 {num_videos} 个。")
        else:
            st.error("⚠️ 请输入视频链接！")
    
    st.markdown("---")
    st.info("💡 **使用提示**：\n1. 输入 1-10 个同分区视频链接\n2. 点击'开始全流程分析'\n3. 在下方查看可视化结果")

# 检查文件状态
files_status = check_files_exist()
all_files_exist = all(files_status.values())

if not all_files_exist:
    st.warning("⚠️ 部分图表文件尚未生成，请先运行'全流程分析'。")
    missing = [name for name, exists in files_status.items() if not exists]
    st.info(f"缺失的文件: {', '.join(missing)}")

# 主内容区 - 使用标签页
tabs = st.tabs([
    "📈 数据质量报告", 
    "😊 情感分析", 
    "📅 时间序列", 
    "☁️ 词云分析", 
    "🔍 聚类主题",
    "📊 视频对比",
    "📂 原始数据"
])

# Tab 1: 数据质量报告
with tabs[0]:
    st.header("📈 数据质量报告")
    st.markdown("展示数据清洗前后的对比，以及各清洗规则的执行情况。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        img_data = get_local_image(config.DATA_QUALITY_IMG)
        if img_data:
            st.image(img_data, caption="数据清洗效果对比 & 清洗规则执行分布", use_container_width=True)
        else:
            st.info("数据质量报告尚未生成")
    
    with col2:
        if os.path.exists(config.COMBINED_CLEANED_CSV):
            df = pd.read_csv(config.COMBINED_CLEANED_CSV)
            st.subheader("📊 数据概览")
            st.metric("清洗后弹幕总数", len(df))
            
            if 'category' in df.columns:
                st.metric("涉及视频数", df['category'].nunique())
            
            if 'sentiment_score' in df.columns:
                avg_sentiment = df['sentiment_score'].mean()
                st.metric("平均情感分", f"{avg_sentiment:.3f}")

# Tab 2: 情感分析
with tabs[1]:
    st.header("😊 情感倾向分析")
    st.markdown("展示弹幕情感分数分布，以及各主题的情感构成。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        img_data = get_local_image(config.SENTIMENT_HISTOGRAM)
        if img_data:
            st.image(img_data, caption="弹幕情感分数分布（0=负面，1=正面）", use_container_width=True)
        else:
            st.info("情感分布直方图尚未生成")
    
    with col2:
        sentiment_bar_path = os.path.join(config.CLEANED_DIR, "sentiment_bar_chart.png")
        img_data = get_local_image(sentiment_bar_path)
        if img_data:
            st.image(img_data, caption="各主题情感分布对比", use_container_width=True)
        else:
            st.info("情感柱状图尚未生成")

    # ================= AI 舆情洞察模块 =================
    st.markdown("---")
    st.subheader("🤖 AI 舆情洞察")
    
    if st.button("生成 AI 深度诊断报告", type="primary"):
        if os.path.exists(config.COMBINED_CLEANED_CSV):
            try:
                df_temp = pd.read_csv(config.COMBINED_CLEANED_CSV)
                if 'cleaned' in df_temp.columns:
                    with st.spinner("AI 正在计算情感并分析中，请稍候..."):
                        # 动态计算情感分
                        from snownlp import SnowNLP
                        bad_comments = []
                        
                        for text in df_temp['cleaned']:
                            try:
                                score = SnowNLP(str(text)).sentiments
                                if score < 0.5: # 提取负面/中性
                                    bad_comments.append(str(text))
                            except:
                                pass
                        
                        if bad_comments:
                            # 只取前 30 条给 AI，避免等待太久
                            result = ai_insight.get_ai_insight(bad_comments[:30])
                            st.success("分析完成！")
                            st.markdown(result.replace('\n', '<br>'), unsafe_allow_html=True)
                        else:
                            st.info("未发现明显的负面弹幕，无需 AI 分析。")
                else:
                    st.warning("数据格式不完整，请重新运行分析流程。")
            except Exception as e:
                st.error(f"AI 分析失败: {str(e)}")
        else:
            st.warning("请先运行分析流程加载数据。")
    # ===================================================

# Tab 3: 时间序列分析
with tabs[2]:
    st.header("📅 时间序列分析")
    st.markdown("分析弹幕密度与情感趋势随视频进度的变化，定位高光/争议时刻。")
    
    # 新增：根据视频数量动态提示
    if os.path.exists(config.COMBINED_CLEANED_CSV):
        try:
            df_check = pd.read_csv(config.COMBINED_CLEANED_CSV)
            if 'video_title' in df_check.columns:
                count = df_check['video_title'].nunique()
                if count > 1:
                    st.info("💡 **提示**：当前包含多个视频，该图展示了**综合节奏趋势**。若需查看各视频细节差异，请移步**「📊 视频对比」**Tab。")
                else:
                    st.info("💡 **提示**：当前仅 1 个视频，该图展示了**完整情感演变**过程。")
        except Exception:
            pass

    img_data = get_local_image(config.TIME_SERIES_IMG)
    if img_data:
        st.image(img_data, caption="弹幕密度与情感趋势叠加图（青色=弹幕密度，红色=情感趋势）", use_container_width=True)
        
        st.markdown("""
        **💡 解读指南**：
        - **弹幕密度高峰**：视频精彩片段或争议点
        - **情感低谷**：可能引发负面讨论的内容
        - **情感高峰**：观众共鸣或赞赏的时刻
        """)
    else:
        st.info("时间序列分析图尚未生成")

# Tab 4: 词云分析
with tabs[3]:
    st.header("☁️ 高频词云图")
    st.markdown("基于 TF-IDF 算法提取的高频关键词，反映弹幕核心议题。")
    
    img_data = get_local_image(config.WORDCLOUD_IMG)
    if img_data:
        st.image(img_data, caption="弹幕高频词云图（字体越大表示频率越高）", use_container_width=True)
    else:
        st.info("词云图尚未生成")

# Tab 5: 聚类主题
with tabs[4]:
    st.header("🔍 聚类主题分析")
    st.markdown("通过 K-Means 算法将弹幕聚类，识别不同的讨论主题。")
    
    img_data = get_local_image(config.CLUSTER_SUMMARY)
    if img_data:
        st.image(img_data, caption="K-Means 聚类主题分布 & 关键词", use_container_width=True)
    else:
        st.info("聚类主题图尚未生成")

# Tab 6: 视频对比（新增）
with tabs[5]:
    st.header("📊 视频对比分析")
    st.markdown("并排对比不同视频的主题分布，直观展示讨论焦点差异。")
    
    img_data = get_local_image(config.VIDEO_COMPARISON_IMG)
    if img_data:
        st.image(img_data, caption="视频主题分布对比（左 vs 右）", use_container_width=True)
        
        st.markdown("""
        **💡 解读指南**：
        - 对比视频的**主题分布比例**，发现观众关注点差异
        - 如果主题相似但比例不同，说明同一话题在不同视频中热度不同
        - 如果主题完全不同，说明视频内容定位差异明显
        """)
    else:
        st.info("视频对比图尚未生成（需输入至少2个视频链接）")

# Tab 7: 原始数据
with tabs[6]:
    st.header("📂 数据预览")
    
    if os.path.exists(config.COMBINED_CLEANED_CSV):
        df = pd.read_csv(config.COMBINED_CLEANED_CSV)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("总弹幕数", len(df))
        
        if 'video_title' in df.columns:
            col2.metric("视频数量", df['video_title'].nunique())
            st.subheader("视频列表")
            for i, title in enumerate(df['video_title'].unique(), 1):
                count = len(df[df['video_title'] == title])
                st.write(f"{i}. {title[:40]}... ({count}条弹幕)")
        else:
            col2.metric("视频数量", "N/A")
        
        if 'sentiment_score' in df.columns:
            avg_sentiment = df['sentiment_score'].mean()
            col3.metric("平均情感分", f"{avg_sentiment:.3f}")
        
        st.markdown("---")
        
        st.subheader("数据表头")
        st.dataframe(df.head(50), use_container_width=True)
        
        st.download_button(
            label="📥 下载完整数据 (CSV)",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name="cleaned_danmu_data.csv",
            mime="text/csv"
        )
    else:
        st.info("清洗后的数据文件尚未生成")

# 页脚
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>🔧 技术栈：Python | Streamlit  | SnowNLP | Scikit-learn | Matplotlib | 大模型API(通义千问)</p>",
    unsafe_allow_html=True
)
