import time
import datetime
import re
import html2text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_content(text):
    """提取特定格式的内容"""
    # 找到所有"第X讲："的位置
    markers = [m.start() for m in re.finditer(r"第\d+讲：", text)]

    start_index = markers[0]

    # 查找后续的"3－教师"
    end_match = re.search(r"3－教师", text[start_index:])
    if not end_match:
        return "「第X讲：」后无「3－教师」"

    end_index = start_index + end_match.end()  # 结束位置
    
    return text[start_index:end_index]

def days_since_date(date_str, date_format="%Y-%m-%d"):
    """计算给定日期到今天的天数"""
    # 解析输入的日期字符串
    date_struct = time.strptime(date_str, date_format)
    # 转换为时间戳（本地时间）
    timestamp_date = time.mktime(date_struct)
    # 获取当前时间戳（UTC时间）
    timestamp_now = time.time()
    # 计算差异并转为天数
    diff_seconds = (timestamp_now - timestamp_date)
    diff_days = diff_seconds // 86400  # 86400秒=1天
    return diff_days

def is_after_next_monday(target_date) -> bool:
    """判断目标日期是否在下周一之后（不包含下周一当天）到下下周一（包含）"""
    # 获取当前日期
    today = datetime.datetime.today().date()
    # 计算今天是本周的第几天（周一=0，周日=6）
    current_weekday = today.weekday()
    days_until_next_monday = (0 - current_weekday) % 7
    # 判断目标日期是否在下周一之后（不包含下周一当天）到下下周一（包含）
    return -(days_until_next_monday + 7) < days_since_date(target_date) < -days_until_next_monday

def tabs(url, seen_urls, browser, web):
    """打开标签页并切换到新标签页"""
    seen_urls.add(url)

    # 新标签页打开链接
    browser.execute_script("window.open(arguments[0]);", url)

    # 切换到新标签页操作
    web1 = browser.window_handles[0]
    if web1 == web: web1 = browser.window_handles[1]
    browser.switch_to.window(web1)
    
    return seen_urls, browser

def HTML(container):
    """处理HTML信息"""
    # 获取容器内的 HTML
    container_html = container.get_attribute("outerHTML")

    handler = html2text.HTML2Text()
    text = handler.handle(container_html)

    return text

def save_content(titles, full_texts, doc):
    """保存网站内容到文档"""
    for title, full_text in zip(titles, full_texts):
        # 添加标题
        doc.write(f"## {title}\n")
        doc.write(full_text)

def create_browser(headless=True):
    """创建浏览器实例"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    return webdriver.Edge(options=options)