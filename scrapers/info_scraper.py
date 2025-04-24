from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import tabs, HTML, days_since_date

def info(doc):
    """提取info上的教务信息"""
    from utils import create_browser
    
    URL_INFO = 'https://info.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all'

    browser = create_browser()
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

    from utils import save_content
    save_content(titles, full_texts, doc)