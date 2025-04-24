from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin
import time
import datetime
import re
import os
import requests
import html2text

def extract_content(text):
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
    """保存网站内容到word"""

    for title, full_text in zip(titles, full_texts):
        # 添加标题（可选）
        title0 = doc.write(f"## {title}\n")

        doc.write(full_text)

def info(doc):
    """提取info上的教务信息"""
    
    URL_INFO = 'https://info.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all'

    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Edge(options=options)

    browser.get(URL_INFO)

    button = browser.find_element(By.ID, 'LM_JWGG')
    button.click()

    notice_blocks = browser.find_elements(By.CSS_SELECTOR, 'div.you')
    seen_urls = set()
    web = browser.window_handles[0]

    titles = []
    full_texts = []

    for block in notice_blocks:  # 用索引遍历，避免引用失效
        try:
            link = block.find_element(By.CSS_SELECTOR, 'div.title > a')
            url = link.get_attribute('href')

            # 去重判断
            if url not in seen_urls:
                seen_urls, browser = tabs(url, seen_urls, browser, web)

                time.sleep(0.3)
                time_label = browser.find_element(By.ID, "timeFlag")
                time_span = time_label.find_element(By.TAG_NAME, "span")
                date = time_span.text[:10]

                # 一周内的信息
                if days_since_date(date) > 6: break

                title = browser.find_element(By.CLASS_NAME, "title").text
                if input('是否拷贝"'+title+'"的信息\n') != "否":
                    container = WebDriverWait(browser, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "xiangqingchakan")))
                    titles.append(title)
                    full_texts.append(HTML(container))

                # 关闭当前标签页并切回原页面
                browser.close()
                browser.switch_to.window(web)

        except Exception as e:
            print(f"处理区块时出错：{str(e)}")

    # 关闭页面
    browser.quit()
    doc.write("# 教务通知\n")

    save_content(titles, full_texts, doc)

def myhome(doc):
    """提取家园网信息"""

    URL_MYHOME = 'http://myhome.tsinghua.edu.cn/web_Netweb_List/News_notice.aspx'

    NO_CONSIDER = ["学生社区中心信息周报", "学生区室外大型活动信息"]

    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Edge(options=options)

    browser.get(URL_MYHOME)

    notice_blocks = browser.find_elements(By.XPATH, 
        "//a[contains(@href, 'News_notice_Detail.aspx') and @target='_blank']")
    seen_urls = set()
    web = browser.window_handles[0]

    titles = []
    full_texts = []

    for block in notice_blocks:  # 用索引遍历，避免引用失效
        try:
            url = block.get_attribute('href')

            # 去重判断
            if url not in seen_urls:
                seen_urls, browser = tabs(url, seen_urls, browser, web)

                time_label = browser.find_element(By.ID, "News_notice_DetailCtrl1_lbladd_time")
                date = time_label.text
                date = date[-17:-13]+"-"+date[-12:-10]+"-"+date[-9:-7]

                # 一周内的信息
                if days_since_date(date) > 6: break

                title = browser.find_element(By.ID, "News_notice_DetailCtrl1_lblTitle").text
                if all((not(sub in title)) for sub in NO_CONSIDER):
                    if input('是否拷贝"'+title+'"的信息\n') != "否":
                        container = WebDriverWait(browser, 15).until(
                            EC.presence_of_element_located((By.XPATH, 
                            "//td[@class='content1 content2' and @colspan='2' and contains(@style, 'text-align: left')]")))
                        titles.append(title)
                        full_texts.append(HTML(container))

                # 关闭当前标签页并切回原页面
                browser.close()
                browser.switch_to.window(web)

        except Exception as e:
            print(f"处理区块时出错：{str(e)}")

    # 关闭页面
    browser.quit()
    doc.write("# 家园网信息\n")

    save_content(titles, full_texts, doc)

def lib(doc):
    """提取图书馆信息"""

    URL_LIB = 'https://lib.tsinghua.edu.cn/tzgg.htm'

    NO_CONSIDER = []

    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Edge(options=options)

    browser.get(URL_LIB)

    notice_labels = browser.find_elements(By.CSS_SELECTOR, 'div.notice-label.color1')
    notice_blocks = browser.find_elements(By.CLASS_NAME, "notice-list-tt")
    seen_urls = set()

    titles = []
    full_texts = []

    for label, block in zip(notice_labels, notice_blocks):
        if (label.text != "开馆通知"): continue
        try:
            title = block.text
            notice_link = block.find_element(By.TAG_NAME, "a")
            notice_link.click()

            class_info = browser.find_element(By.CLASS_NAME, "info")
            time_label = class_info.find_element(By.CLASS_NAME, "date")
            date = time_label.text
            date = date[-11:-7]+"-"+date[-6:-4]+"-"+date[-3:-1]

            # 一周内的信息
            if days_since_date(date) > 6:
                browser.back()
                continue

            if all((not(sub in title)) for sub in NO_CONSIDER):
                if input('是否拷贝"'+title+'"的信息\n') != "否":
                    container = WebDriverWait(browser, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "concon")))
                    titles.append(title)
                    full_texts.append(HTML(container))

            # 回到上个页面
            browser.back()

        except Exception as e:
            print(f"处理区块时出错：{str(e)}")

    URL_LIB = 'https://lib.tsinghua.edu.cn/hdrl.htm'

    CONSIDER = ["信息•资源•研究"]

    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Edge(options=options)

    browser.get(URL_LIB)

    notice_blocks = browser.find_elements(By.CSS_SELECTOR, 'div.rl-title.txt-elise a')
    seen_urls = set()

    for block in notice_blocks:  # 用索引遍历，避免引用失效
        try:
            url = block.get_attribute('href')

            # 去重判断
            if url not in seen_urls:
                title = block.text
                block.click()

                time_label = browser.find_element(By.CLASS_NAME, "infoBarsList-value")
                date = time_label.text
                year = datetime.datetime.now().strftime("%Y")
                date = year+"-"+date.split("月")[0]+"-"+date.split("月")[1].split("日")[0]
                if days_since_date(date) > 350:
                    year = str(int(year) + 1)
                    date = year+"-"+date.split("月")[0]+"-"+date.split("月")[1].split("日")[0]

                # 下周一后的讲座
                if not is_after_next_monday(date):
                    browser.back()
                    continue

                if any((sub in title) for sub in CONSIDER):
                    if input('是否拷贝"'+title+'"的信息\n') != "否":
                        container = WebDriverWait(browser, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.material-value.editor-width")))
                        titles.append(title)
                        full_texts.append(extract_content(HTML(container)))

                # 回到上个页面
                browser.back()

        except Exception as e:
            print(f"处理区块时出错：{str(e)}")

    # 关闭页面
    browser.quit()
    doc.write("# 图书馆信息\n")

    save_content(titles, full_texts, doc)

def hall(doc, filename_jpg):
    """提取新清华学堂信息"""

    URL_MYHOME = 'https://www.hall.tsinghua.edu.cn/columnEx/pwzx_hdap/yc-dy-px-zl-jz/1'

    NO_CONSIDER = []

    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Edge(options=options)

    browser.get(URL_MYHOME)

    # 提取所有演出块
    events = browser.find_elements(By.CSS_SELECTOR, 'div.timemain_a')

    result = []
    for event in events:
        # ------------------------- 提取日期 -------------------------
        try:
            # 提取日（例如 "08"）
            day_element = event.find_element(By.CSS_SELECTOR, 'b.size_40')
            day = day_element.text.strip()
            
            # 通过JavaScript提取年月（例如 "2025-06"）
            year_month_script = """
            var node = arguments[0].nextSibling;
            while (node) {
                if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '') {
                    return node.textContent.trim();
                }
                node = node.nextSibling;
            }
            return '';
            """
            year_month = browser.execute_script(year_month_script, day_element)
            
            # 提取时间（例如 "14:00"）
            time_element = event.find_element(By.CSS_SELECTOR, 'b.size_bg')
            time = time_element.text.strip()
            
            # 组合完整日期
            full_date = f"{year_month}-{day} {time}"
        except NoSuchElementException:
            full_date = "N/A"

        # ------------------------- 提取标题 -------------------------
        try:
            title_element = event.find_element(By.CSS_SELECTOR, 'h3.yahei a')
            title = title_element.text.strip()
        except NoSuchElementException:
            title = "N/A"

        # ------------------------- 提取地点 -------------------------
        try:
            location_element = event.find_element(By.CSS_SELECTOR, 'li.add')
            location = location_element.text.strip().replace('<br>', '')
        except NoSuchElementException:
            location = "N/A"

        # ------------------------- 提取票价 -------------------------
        try:
            price_element = event.find_element(By.CLASS_NAME, 'money')
            price = price_element.text.strip().replace('<br>', '')
        except NoSuchElementException:
            price = "N/A"

        # ------------------------- 提取图片网址 -------------------------
        img = event.find_element(By.TAG_NAME, 'img')
    
        # 获取属性
        relative_src = img.get_attribute('src')
        absolute_src = urljoin(browser.current_url, relative_src)

        # 保存结果
        result.append({
            "date": full_date,
            "title": title,
            "location": location,
            "price": price,
            "absolute_src": absolute_src
        })
    
    result_refined = []
    titles = []

    for item in result[::-1]:
        if (item["title"] not in titles) & (item["title"] not in NO_CONSIDER):
            if input('是否拷贝"'+item["title"]+'"的信息\n') == "否":
                NO_CONSIDER.append(item["title"])
                continue

            headers={
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3861.400 QQBrowser/10.7.4313.400'}
            re=requests.get(item["absolute_src"], headers=headers)
            path = filename_jpg + item["title"] + ".jpg"
            with open(path, 'wb') as f:
                for chunk in re.iter_content(chunk_size=128):
                    f.write(chunk)

            titles.append(item["title"])
            result_refined.append({
            "date": [item["date"],],
            "title": item["title"],
            "location": item["location"],
            "price": item["price"],
            "path": item["title"] + ".jpg"
            })

        else:
            for item_refined in result_refined:
                if item_refined["title"] == item["title"]:
                    item_refined["date"].append(item["date"])

    browser.quit()
    doc.write("# 新清华学堂\n")

    for item in result_refined:
        doc.write(f"## {item['title']}\n")
        if len(item['date']) == 1:
            doc.write(f"日期: {(item['date'])[0]}\n")
        else:
            doc.write(f"日期: \n")
            for date in item['date']:
                doc.write(f"{date}\n")
        doc.write(f"地点: {item['location']}\n")
        doc.write(f"票价: {item['price']}\n")

def main():
    # 创建 log 目录（如果不存在）
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建时间戳子目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    report_dir = os.path.join(log_dir, f"万有预报_{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    
    # 设置文件路径
    filename = os.path.join(report_dir, "main.md")
    filename_jpg = report_dir + os.sep  # 使用os.sep确保跨平台兼容
    
    # 打开文档
    doc = open(filename, "w")

    # 执行各个爬虫模块
    info(doc)
    myhome(doc)
    lib(doc)
    hall(doc, filename_jpg)

    # 关闭文件
    doc.close()
    
    # 输出保存路径
    print(f"文件已保存至：{filename}")

if __name__ == "__main__":
    main()
