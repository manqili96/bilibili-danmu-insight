import dashscope
from dashscope import Generation

# 你自己的 Key
dashscope.api_key = ""

def get_ai_insight(comments_list):
    """AI 分析负面/中性弹幕痛点"""
    if not comments_list or len(comments_list) == 0:
        return "数据量不足，无法分析。"

    # 取前 30 条做分析
    sample_text = "\n".join(comments_list[:30])

    prompt = f"""
    你是一名资深的数据分析师。以下是一组 B 站视频弹幕中的【负面/中性】评论：
    ---
    {sample_text}
    ---
    请完成以下任务：
    1. 【痛点总结】：归纳出观众不满的 3 个核心原因（每点不超过 15 字）。
    2. 【运营建议】：给出 1 条具体的优化建议。
    请保持语气客观专业，直接输出结果，不要包含"好的"、"分析如下"等废话。
    """

    try:
        response = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt}]
        )
        if response.status_code == 200:
            return response.output.text
        else:
            return f"分析失败: {response.message}"
    except Exception as e:
        return f"异常: {e}"
