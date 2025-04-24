from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import tabs, HTML, days_since_date

def myhome(doc):
    """提取家园网信息"""
    from utils import create_browser
    
    URL_MYHOME = 'http://myhome.tsinghua.edu.cn/web_Netweb_List/News_notice.aspx'

    NO_CONSIDER = ["学生社区中心信息周报", "学生区室外大型活动信息"]

    browser = create_browser()
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

    from utils import save_content
    save_content(titles, full_texts, doc)