from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
from utils import HTML, days_since_date, is_after_next_monday, extract_content

def lib(doc):
    """提取图书馆信息"""
    from utils import create_browser
    
    URL_LIB = 'https://lib.tsinghua.edu.cn/tzgg.htm'

    NO_CONSIDER = []

    browser = create_browser()
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

    browser.quit()
    
    # 获取讲座信息
    URL_LIB = 'https://lib.tsinghua.edu.cn/hdrl.htm'
    CONSIDER = ["信息•资源•研究"]

    browser = create_browser()
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

    from utils import save_content
    save_content(titles, full_texts, doc)