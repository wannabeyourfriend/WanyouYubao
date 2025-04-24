from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin
import requests

def hall(doc, filename_jpg):
    """提取新清华学堂信息"""
    from utils import create_browser
    
    URL_MYHOME = 'https://www.hall.tsinghua.edu.cn/columnEx/pwzx_hdap/yc-dy-px-zl-jz/1'

    NO_CONSIDER = []

    browser = create_browser()
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