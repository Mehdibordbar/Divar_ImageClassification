import time
import requests
import os

from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from lxml import etree

urls = {"MG":"https://divar.ir/s/tehran/car/mg/",
       "peugeot_206":"https://divar.ir/s/tehran/car/peugeot/206/5/",
       "Quick":"https://divar.ir/s/tehran/car/quick/",
       "Samand_LX":"https://divar.ir/s/tehran/car/samand/lx/",
       "Dena_Plus":"https://divar.ir/s/tehran/car/dena/plus/",
       "Tiba_Hatchback":"https://divar.ir/s/tehran/car/tiba/hatchback/ex"}


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_images(url):
    """
    Returns all image URLs on a single `url`
    """
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(5)
    # driver.find_element_by_tag_name('body').send_keys(Keys.End)# Implicit wait, actually does not need 5 seconds, when to load the page, when to proceed to the next step
    driver.maximize_window()  # window maximizing
    # driver.implicitly_wait(5)
    # driver.find_element_by_tag_name('body').send_keys(Keys.END)
    time.sleep(5)
    s_num = 1
    f_num = 0
    urls = []
    for i in range(30):
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        source = driver.page_source
        soup = bs(source, 'lxml')
        imgs = soup.find_all('img')

        # f_num = len(elements)  # Number of starting elements
        # driver.find_element_by_tag_name('body').click()
        # # Turn the page for a while, here I define 50 times
        # for i in range(50) :
        #     driver.find_element_by_tag_name('body').send_keys(Keys.END)
        #     time.sleep(0.5)
        # # time.sleep(0.1)
        # source = driver.page_source
        # soup = bs(source, "lxml")
        # time.sleep(2)
        # elements = soup.find_all('img')
        # s_num = len(elements)
    # time.sleep(15)
    # driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_UP)
    # driver.find_element_by_tag_name('body').click()
    # driver.find_element_by_tag_name('body').send_keys(Keys.END)
    # source = driver.page_source
    # soup = bs(source, "lxml")
    # imgs = soup.find_all('img')
    # results = soup.select('.kt-post-card__image-wrapper')
    # i = 0
    # links_to_product = list()
    # while i < len(results) :
    #     links_to_product.append(results[i].select(
    #         '.kt-image-block__image')[0].get('src'))
    #     i += 1
    #

        for img in tqdm(imgs, "Extracting images") :
            img_url = img.attrs.get("src")
            if not img_url :
                # if img does not contain src attribute, just skip
                continue
            # make the URL absolute by joining domain with the URL that is just extracted
            img_url = urljoin(url, img_url)
            try :
                pos = img_url.index("?")
                img_url = img_url[:pos]
            except ValueError :
                pass
            # finally, if the url is valid
            if is_valid(img_url) :
                urls.append(img_url)
    print(len(urls))
    return urls

def download(url, pathname):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)
    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))
    # get the file name
    filename = os.path.join(pathname, url.split("/")[-1])
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))



def main(url, path):
    # get all images
    imgs = get_all_images(url)
    for img in imgs:
        # for each image, download it
        download(img, path)



for key, value in urls.items():
    main(value,"Dataset\\" + key + "\\")
