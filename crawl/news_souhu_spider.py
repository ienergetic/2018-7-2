from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import pymysql

def get_news(browser,root):
    time.sleep(1)
    browser.get(root)
    time.sleep(2)
    browser.execute_script('window.scrollTo(0,500)')
    time.sleep(2)
    for i in range(1, 100):
        browser.execute_script('window.scrollTo(500+500*%d,500*%d)' % (i, i))
        time.sleep(1)
        print(i)
    news_titles = []
    news_urls = []
    # 获取详细新闻的链接和标题

    news_link = browser.find_elements_by_xpath('//*[@id="main-news"]/div/div[@class="news-wrapper"]/div[@data-role="news-item"]/h4/a')
    for ii in range(0, len(news_link)):
            news_urls.append(news_link[ii].get_attribute('href'))
    for j in range(0, len(news_urls)):
        print(news_urls[j])
        print(j)
    return news_urls


def get_content(browser, news_urls, news_tag):
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count', charset='utf8')
    cur = conn.cursor()
    id = 0
    for news_url in news_urls:
        browser.get(news_url)
        time.sleep(1)
        try:
            news_title = pymysql.escape_string(browser.find_element_by_xpath('//*[@id="article-container"]/div[2]/div[1]/div[1]/h1').text)
        except NoSuchElementException:
            continue
        news_date = browser.find_element_by_xpath('//*[@id="news-time"]').text
        news_body = pymysql.escape_string(browser.find_element_by_xpath('//*[@id="mp-editor"]').text)
        print(id, news_url, news_title, news_date)
        sql = "insert into news_table VALUES ('%d', '%s', '%s', '%s', '%s', '%s')" %(id, news_date, news_url, news_title, news_body, news_tag)
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()


def main(root, news_tag):
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    #chrome_options.add_argument('headless')
    browser = webdriver.Chrome(chrome_options=chrome_options)
    news_url = get_news(browser, root)
    get_content(browser,news_url, news_tag)
    browser.close()


if __name__ == '__main__':
    root = ['http://www.sohu.com/c/8/1461','http://www.sohu.com/c/8/1463']
    news_tag = ['国际','财经']
    main(root[1],news_tag[1])
