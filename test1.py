import requests
from lxml import etree
import os
import re
import threading

# 定义一个函数用于获取指定 XPath 的所有链接和标题
def get_links_and_titles_from_xpath(url, xpath):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        tree = etree.HTML(response.text)
        elements = tree.xpath(xpath)
        links = []
        titles = []
        for element in elements:
            link = element.get('href')
            title = element.get('title')
            if link and title:
                links.append(link)
                titles.append(title)
        return links, titles
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return [], []

# 定义一个函数用于处理网站主页的分页链接
def get_index_page_links(base_index_url, max_page):
    all_index_links = [base_index_url]
    for i in range(2, max_page + 1):
        index_url = re.sub(r'(\.html)$', f'_{i}\\1', base_index_url)
        all_index_links.append(index_url)
    return all_index_links

# 定义一个函数用于处理具体内容页的分页链接
def get_all_page_links(base_url):
    all_links = [base_url]
    page_num = 2
    while True:
        page_url = re.sub(r'(\.html)$', f'_{page_num}\\1', base_url)
        try:
            response = requests.get(page_url)
            if response.status_code == 200:
                all_links.append(page_url)
                page_num += 1
            else:
                break
        except requests.RequestException as e:
            print(f"请求分页链接时出错: {e}")
            break
    return all_links

# 定义一个函数用于下载图片
def download_images(url, save_folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        tree = etree.HTML(response.text)
        # 处理图片 XPath 中编号不确定的情况
        img_xpath = '/html/body/div[1]/div[2]/div/article/div[3]/p[2]/img'
        img_links = tree.xpath(img_xpath + '/@src')
        for img_link in img_links:
            if img_link.startswith('//'):
                img_link = 'https:' + img_link
            elif not img_link.startswith('http'):
                # 如果是相对链接，拼接成完整链接
                base = url.rsplit('/', 1)[0]
                img_link = base + '/' + img_link.lstrip('/')
            try:
                img_response = requests.get(img_link)
                img_response.raise_for_status()
                img_name = os.path.join(save_folder, img_link.rsplit('/', 1)[-1])
                with open(img_name, 'wb') as f:
                    f.write(img_response.content)
                print(f"下载成功: {img_link}")
            except requests.RequestException as e:
                print(f"下载图片时出错: {e}")
    except requests.RequestException as e:
        print(f"请求页面时出错: {e}")

# 定义一个函数用于处理单个链接及其分页的图片下载
def process_link(link, title, base_index_url):
    # 过滤非法字符
    illegal_chars = r'[\\/*?:"<>|]'
    title = re.sub(illegal_chars, '_', title)

    if not link.startswith('http'):
        # 如果是相对链接，拼接成完整链接
        base = base_index_url.rsplit('/', 1)[0]
        link = base + '/' + link.lstrip('/')
    save_folder = os.path.join('downloaded_images', title)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    all_page_links = get_all_page_links(link)
    for page_link in all_page_links:
        download_images(page_link, save_folder)

# 主函数
def main():
    base_index_url = 'https://www.lolili.net/index.html'
    max_index_page = 5  # 可根据实际情况修改主页最大页数
    item_xpath = '/html/body/div[1]/div[2]/div/div[2]/div[1]/ul/li/h2/a'

    # 获取所有主页分页链接
    all_index_links = get_index_page_links(base_index_url, max_index_page)
    threads = []
    for index_link in all_index_links:
        # 获取当前主页上的所有具体内容页链接和标题
        item_links, item_titles = get_links_and_titles_from_xpath(index_link, item_xpath)
        for link, title in zip(item_links, item_titles):
            thread = threading.Thread(target=process_link, args=(link, title, base_index_url))
            threads.append(thread)
            thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()