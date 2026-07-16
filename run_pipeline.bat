@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo ========================================
echo 开始执行 B 站弹幕分析全流程
echo ========================================

echo.
echo [1/4] 正在启动弹幕爬取工具...
echo 请输入视频数量和链接，完成后自动进行下一步。
echo ========================================
python danmu_crawler.py
if errorlevel 1 (
    echo [错误] 爬取阶段失败，请检查。
    pause
    exit /b 1
)

echo.
echo [2/4] 正在清洗数据...
python danmu_cleaner.py
if errorlevel 1 (
    echo [错误] 数据清洗失败，请检查。
    pause
    exit /b 1
)

echo.
echo [3/4] 正在分析词频与聚类...
python word_frequency_analysis.py
if errorlevel 1 (
    echo [错误] 词频分析失败，请检查。
    pause
    exit /b 1
)

echo.
echo [4/4] 正在分析情感倾向...
python sentiment_analysis.py
if errorlevel 1 (
    echo [错误] 情感分析失败，请检查。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 全流程执行完毕！结果已输出至 D 盘
echo ========================================
pause
