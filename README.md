一、项目介绍
1、核心功能
| 模块 | 技术方案 | 效果 |
| 自动采集 | B站API爬虫，支持多视频批量输入 | 1.5w+ 弹幕累计处理 |
| 语料清洗 | 自定义800+垂直领域停用词库 | 有效去除短文本噪声 |
| 情感分析 | SnowNLP 细粒度情感评分 | 量化观众情绪倾向 |
| 主题聚类 | TF-IDF + K-Means（3-5个核心议题） | 自动归纳讨论焦点 |
| 时序分析 | 时间序列定位高光/争议节点 | 精准捕捉剧情爆点 |
| AI归因 | 通义千问API 智能诊断 | 舆情诊断秒级响应 |
| 视频对比 | 跨视频关注点偏移量化 | 竞品/系列对比分析 |

 2、技术栈
- 前端：Streamlit（交互式看板）
- 后端：Python 3.9+
- NLP工具：SnowNLP、TF-IDF、K-Means
- 大模型：通义千问 API
- 数据采集：Requests、B站API
- 可视化：Plotly、WordCloud

3、项目结构
├── app.py # Streamlit 主界面
├── danmu_crawler.py # B站弹幕爬虫
├── danmu_cleaner.py # 弹幕清洗
├── sentiment_analysis.py # SnowNLP情感分析
├── word_frequency_analysis.py # TF-IDF词频 + K-Means聚类
├── ai_insight.py # 通义千问API归因诊断
├── config_example.py # 配置文件示例（需自行填写API Key）
├── cn_stopwords.txt # 800+中文停用词库
├── run_pipeline.bat # Windows一键运行脚本
└── requirements.txt # 依赖清单


二、快速开始
1. 克隆项目
git clone https://github.com/manqili96/bilibili-danmu-insight.git

2. 安装依赖
pip install -r requirements.txt

3. 配置 API Key（复制并重命名）
用自己的替换放进ai_insight.py 里面对应的位置

4. 启动应用
streamlit run app.py
