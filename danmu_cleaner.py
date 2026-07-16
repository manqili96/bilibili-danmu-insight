import re
import pandas as pd
import os
import unicodedata
import glob
import datetime
import sys

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


# ======================
# 数据清洗模块
# ======================
def clean_danmu_content(danmakus):
    """
    弹幕内容清洗，专注于文本处理

    :param danmakus: 弹幕数据列表（字典格式）
    :return: 清洗后的弹幕内容列表
    """
    cleaned_danmakus = []

    # 预编译正则表达式，提高效率
    html_tags = re.compile(r'<[^>]+>')
    urls = re.compile(r'https?://\S+')
    special_chars = re.compile(r'[^\w\u4e00-\u9fa5，。！？、；："\'()【】《》]')
    extra_spaces = re.compile(r'\s+')

    for danmu in danmakus:
        content = danmu['content']
        original_content = content  # 保存原始内容用于展示

        # 记录清洗步骤
        cleaning_steps = []

        # 1. 基本清洗
        # 去除HTML标签
        if html_tags.search(content):
            content = html_tags.sub('', content)
            cleaning_steps.append("移除HTML标签")

        # 去除URL
        if urls.search(content):
            content = urls.sub('', content)
            cleaning_steps.append("移除URL")

        # 2. 特殊字符处理
        # 保留中文、数字、字母和常用标点
        if special_chars.search(content):
            content = special_chars.sub(' ', content)
            cleaning_steps.append("移除特殊字符")

        # 3. 标准化处理
        # 全角转半角
        normalized = unicodedata.normalize('NFKC', content)
        if normalized != content:
            content = normalized
            cleaning_steps.append("全角转半角")

        # 去除多余空格
        if extra_spaces.search(content):
            content = extra_spaces.sub(' ', content).strip()
            cleaning_steps.append("移除多余空格")

        # 4. 长度过滤（放宽限制）
        # 保留长度在1-100个字符之间的弹幕
        if 1 <= len(content) <= 100:
            cleaned_danmakus.append({
                'original': original_content,
                'cleaned': content,
                'video_title': danmu.get('video_title', '未知视频'),
                'time': danmu.get('time', 0),
                'timestamp': danmu.get('timestamp', ''),
                'cleaning_steps': ', '.join(cleaning_steps) if cleaning_steps else "无变化"
            })

    return cleaned_danmakus


# ======================
# 文件处理模块
# ======================
def find_danmu_files(directory):
    """
    在指定目录中查找所有弹幕CSV文件

    :param directory: 要搜索的目录
    :return: 找到的文件路径列表
    """
    # 查找所有CSV文件
    csv_files = glob.glob(os.path.join(directory, '*.csv'))

    # 过滤掉清洗后的文件
    danmu_files = [f for f in csv_files if not f.endswith('_cleaned.csv')]

    return danmu_files


def read_danmu_files(file_paths):
    """
    读取多个弹幕文件并合并数据

    :param file_paths: 文件路径列表
    :return: 合并后的弹幕数据列表
    """
    all_danmakus = []

    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            print(f"成功读取文件: {os.path.basename(file_path)}")
            print(f"包含 {len(df)} 条弹幕")

            # 转换为字典列表
            danmakus = df.to_dict('records')
            all_danmakus.extend(danmakus)
        except Exception as e:
            print(f"读取文件失败: {file_path} - {e}")

    print(f"\n总共读取 {len(all_danmakus)} 条弹幕")
    return all_danmakus


def save_cleaned_danmu(cleaned_danmakus, output_dir=None):
    """
    保存清洗后的弹幕内容
    """
    if output_dir is None:
        output_dir = config.CLEANED_DIR
    
    try:
        # 保存清洗后的文本（固定文件名，每次覆盖）
        cleaned_file = config.COMBINED_CLEANED_TXT
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            for item in cleaned_danmakus:
                f.write(item['cleaned'] + '\n')

        # 保存结构化数据（固定文件名，每次覆盖）
        structured_file = config.COMBINED_CLEANED_CSV
        df = pd.DataFrame(cleaned_danmakus)
        df.to_csv(structured_file, index=False, encoding='utf-8-sig')

        print(f"\n清洗后的弹幕已保存至: {cleaned_file}")
        print(f"结构化数据已保存至: {structured_file}")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False


# ======================
# 清洗效果展示
# ======================
def show_cleaning_samples(cleaned_danmakus, sample_size=10):
    """
    展示清洗效果样本，突出显示被处理过的弹幕

    :param cleaned_danmakus: 清洗后的弹幕内容列表
    :param sample_size: 展示样本数量
    """
    if not cleaned_danmakus:
        print("没有可展示的样本")
        return

    print("\n清洗效果样本 (突出显示被处理过的弹幕):")
    print("-" * 120)
    print(f"{'原始弹幕':<40} | {'清洗后弹幕':<40} | {'处理步骤':<20} | {'视频标题'}")
    print("-" * 120)

    # 优先选择被处理过的弹幕
    modified_danmakus = [
        d for d in cleaned_danmakus if d['cleaning_steps'] != "无变化"
    ]
    unmodified_danmakus = [
        d for d in cleaned_danmakus if d['cleaning_steps'] == "无变化"
    ]

    # 确保样本中包含被处理过的弹幕
    samples = modified_danmakus[:min(sample_size, len(modified_danmakus))]
    if len(samples) < sample_size:
        samples.extend(unmodified_danmakus[:sample_size - len(samples)])

    for item in samples:
        original = item['original'][:38] + '...' if len(
            item['original']) > 40 else item['original']
        cleaned = item['cleaned'][:38] + '...' if len(
            item['cleaned']) > 40 else item['cleaned']
        steps = item['cleaning_steps']
        video_title = item['video_title'][:20] + '...' if len(
            item['video_title']) > 23 else item['video_title']

        # 突出显示被处理过的弹幕
        if steps != "无变化":
            original = f"\033[91m{original}\033[0m"  # 红色显示原始弹幕
            cleaned = f"\033[92m{cleaned}\033[0m"  # 绿色显示清洗后弹幕
            steps = f"\033[93m{steps}\033[0m"  # 黄色显示处理步骤

        print(f"{original:<40} | {cleaned:<40} | {steps:<20} | {video_title}")

    print("-" * 120)
    print(
        "颜色说明: \033[91m红色\033[0m = 原始弹幕, \033[92m绿色\033[0m = 清洗后弹幕, \033[93m黄色\033[0m = 处理步骤"
    )

    # 显示一些统计信息
    modified_count = len(modified_danmakus)
    total_count = len(cleaned_danmakus)
    print(
        f"\n清洗统计: {modified_count}/{total_count} 条弹幕被处理过 ({modified_count/total_count*100:.1f}%)"
    )


# ======================
# 主处理流程
# ======================
def process_all_danmu_files():
    """
    处理所有弹幕文件
    """
    # 1. 查找所有弹幕文件
    print("\n" + "=" * 40)
    print("步骤1: 查找弹幕文件")
    print("=" * 40)
    danmu_files = find_danmu_files(config.BILIDANMU_DIR)

    if not danmu_files:
        print(f"在目录 {config.BILIDANMU_DIR} 中未找到弹幕文件")
        return

    print(f"找到 {len(danmu_files)} 个弹幕文件:")
    for file in danmu_files:
        print(f"- {os.path.basename(file)}")

    # 2. 读取所有弹幕文件
    print("\n" + "=" * 40)
    print("步骤2: 读取弹幕文件")
    print("=" * 40)
    all_danmakus = read_danmu_files(danmu_files)

    if not all_danmakus:
        print("没有可处理的弹幕数据")
        return

    original_count = len(all_danmakus)

    # 3. 清洗弹幕内容
    print("\n" + "=" * 40)
    print("步骤3: 清洗弹幕内容")
    print("=" * 40)
    cleaned_danmakus = clean_danmu_content(all_danmakus)
    cleaned_count = len(cleaned_danmakus)
    print(
        f"清洗后保留 {cleaned_count} 条弹幕 ({cleaned_count/original_count*100:.1f}%)"
    )

    # 统计清洗规则
    cleaning_stats = {}
    for item in cleaned_danmakus:
        steps = item['cleaning_steps'].split(', ')
        for step in steps:
            if step != "无变化":
                cleaning_stats[step] = cleaning_stats.get(step, 0) + 1

    # 4. 保存清洗结果
    save_cleaned_danmu(cleaned_danmakus)

    # 5. 生成数据质量报告
    generate_data_quality_report(original_count, cleaned_count, cleaning_stats)

    # 6. 展示清洗效果
    show_cleaning_samples(cleaned_danmakus)

    print("\n弹幕数据清洗完成！")


def generate_data_quality_report(original_count, cleaned_count, cleaning_stats):
    """生成数据质量报告"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    
    # 配置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    report = {
        "original_count": original_count,
        "cleaned_count": cleaned_count,
        "removed_count": original_count - cleaned_count,
        "retention_rate": cleaned_count / original_count * 100 if original_count > 0 else 0,
        "cleaning_stats": cleaning_stats
    }
    
    # 打印报告
    print("\n" + "=" * 50)
    print("数据质量报告")
    print("=" * 50)
    print(f"原始弹幕数: {original_count}")
    print(f"清洗后弹幕数: {cleaned_count}")
    print(f"移除弹幕数: {report['removed_count']}")
    print(f"保留率: {report['retention_rate']:.1f}%")
    
    if cleaning_stats:
        print("\n清洗规则执行情况:")
        for rule, count in sorted(cleaning_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {rule}: {count} 条")
    
    # 生成可视化
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # 左图：清洗前后对比
        ax1.bar(['原始弹幕', '清洗后弹幕'], [original_count, cleaned_count], 
                color=['#FF6B6B', '#4ECDC4'], edgecolor='black', alpha=0.7)
        ax1.set_ylabel('弹幕数量', fontsize=12)
        ax1.set_title('数据清洗效果对比', fontsize=14, fontweight='bold')
        
        # 动态设置 Y 轴上限，防止标签溢出
        max_val = max(original_count, cleaned_count)
        ax1.set_ylim(0, max_val * 1.15)
        
        for i, v in enumerate([original_count, cleaned_count]):
            # 标签放在柱子顶端上方一点点
            ax1.text(i, v * 1.02, str(v), ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # 右图：清洗规则分布
        if cleaning_stats:
            rules = list(cleaning_stats.keys())[:8]
            counts = [cleaning_stats[r] for r in rules]
            colors = plt.cm.Set2(np.linspace(0, 1, len(rules)))
            ax2.barh(rules, counts, color=colors, edgecolor='black', alpha=0.7)
            ax2.set_xlabel('处理次数', fontsize=12)
            ax2.set_title('清洗规则执行分布', fontsize=14, fontweight='bold')
            ax2.invert_yaxis()
        
        plt.tight_layout()
        report_file = config.DATA_QUALITY_IMG
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"\n数据质量报告图已保存: {report_file}")
    except Exception as e:
        print(f"生成质量报告图失败: {e}")
    
    return report


# ======================
# 主函数
# ======================
def main():
    print("=" * 50)
    print("B站弹幕批量清洗工具")
    print("=" * 50)
    print("本工具将自动处理bili_danmu_results目录中的所有弹幕文件")

    # 处理所有弹幕文件
    process_all_danmu_files()


if __name__ == "__main__":
    main()