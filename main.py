import time
from TikTokApi.exceptions import TikTokNotFoundError
from selenium.webdriver.chrome import options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.opera.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from time import sleep
from TikTokApi import TikTokApi
import pandas as pd
import os
import atexit
import sys
import pathlib
import threading
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

cur_path = str(pathlib.Path().resolve())

def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r", description = ''):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix} ({description})', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def init_web_driver():
    global firefox_driver
    options = Options() 
    # options.headless = True
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    profile = webdriver.FirefoxProfile()
    ext_adblock_path = cur_path + r'\adguard_adblocker-3.6.6-an+fx.xpi'
    download_dir = cur_path + r"\videos"
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_dir)
    profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
    profile.set_preference("browser.download.manager.closeWhenDone", False)
    profile.set_preference("browser.download.manager.focusWhenStarting", False)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "video/mp4")
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    desired = DesiredCapabilities.FIREFOX

    firefox_driver = webdriver.Firefox(firefox_options=options, firefox_profile=profile, executable_path=r"geckodriver.exe", desired_capabilities=desired, service_log_path='my-app.log')
    # chrome_driver = webdriver.Chrome(chrome_options=options, executable_path=cur_path + r'\chromedriver.exe')

    # options = webdriver.ChromeOptions()
    # options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    # chrome_driver_binary = "/usr/local/bin/chromedriver"
    # driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)

    firefox_driver.install_addon(ext_adblock_path, temporary=True)
    time.sleep(5)

def filter_data_received(tiktok_item):
    to_return = {}
    to_return['user_id'] = tiktok_item['author']['id']
    to_return['user_name'] = tiktok_item['author']['uniqueId']
    to_return['video_id'] = tiktok_item['id']
    to_return['video_desc'] = tiktok_item['desc']
    to_return['video_time'] = tiktok_item['createTime']
    to_return['video_length'] = tiktok_item['video']['duration']
    to_return['video_link'] = 'https://www.tiktok.com/@{}/video/{}?lang=en'.format(to_return['user_name'], to_return['video_id'])
    to_return['n_likes'] = tiktok_item['stats']['diggCount']
    to_return['n_shares'] = tiktok_item['stats']['shareCount']
    to_return['n_comments'] = tiktok_item['stats']['commentCount']
    to_return['n_plays'] = tiktok_item['stats']['playCount']
    return to_return

def check_dowload(data_video):
    firefox_driver.get("about:downloads")
    while(True):
        total = int(WebDriverWait(firefox_driver,2).until(
            EC.presence_of_element_located((By.TAG_NAME, "progress"))).get_attribute('max'))
        value = int(WebDriverWait(firefox_driver,2).until(
                EC.presence_of_element_located((By.TAG_NAME, "progress"))).get_attribute('value'))
        des = WebDriverWait(firefox_driver,2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'description[class="downloadDetails downloadDetailsNormal"]'))).get_attribute('value')
        print_progress_bar(value, total, prefix = 'Progress:', suffix = 'Complete', length = 50, description = des)
        if int(value) == int(total):
            file_name = WebDriverWait(firefox_driver,2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'description[class="downloadTarget"]'))).get_attribute('value')
            if os.path.isfile(cur_path + r'\videos\{}'.format(file_name)):
                print('Dowload successs video {}'.format(data_video['video_id']))
            else:
                print('Dowload failed video {}'.format(data_video['video_id']))
            break
        

def download_video_no_watermark(data_video):
    firefox_driver.get("https://snaptik.app")
    firefox_driver.implicitly_wait(5000)
    try:
        url_input_element = WebDriverWait(firefox_driver, 10).until(
            EC.presence_of_element_located((By.ID, 'url')))
        url_input_element.send_keys(data_video['video_link'])

        submit_btn_element = WebDriverWait(firefox_driver,10).until(
            EC.element_to_be_clickable((By.ID, 'submiturl')))
        submit_btn_element.click()
        download_btns_element = WebDriverWait(firefox_driver,10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class,'abutton')]"))
        )
        if(download_btns_element):
            download_btns_element[0].click()
        check_dowload(data_video)
        time.sleep(5)
    except TimeoutException:
        print("Trying to find the given element but unfortunately no element is found")
    return True

def get_videos_by_username():
    videos = []
    # print("Nhập username tiktok cần lấy video", end =": ")
    # username = input("Nhập username tiktok cần lấy video: ")
    # print("Nhập số lượng cần lấy", end =": ")
    # num_of_get = int(input("Nhập số lượng cần lấy: "))

    # define input
    username = 'tuannda.98'
    num_of_get = 1
    api = TikTokApi.get_instance()
    # api = TikTokApi.get_instance(use_selenium=True, custom_verifyFp="verify_ksfnbuzc_MvINgKPd_PjT8_4TqY_9ry2_9KLIv86LRinC")
    if(username.strip() != ""):
        try:
            get_videos = api.by_username(username, count=num_of_get, custom_verifyFp="verify_ksfnbuzc_MvINgKPd_PjT8_4TqY_9ry2_9KLIv86LRinC")
            videos = [filter_data_received(item) for item in get_videos]
        except TikTokNotFoundError as error:
            print(error)
    if(len(videos) > 0):
        for video in videos:
            download_video_no_watermark(video)

@atexit.register 
def end_app(): 
    try:
        firefox_driver.quit()
        print("Exiting Python Script!")
    except Exception:
        print("Exiting Python Script!")

def main():
    init_web_driver()
    get_videos_by_username()

if __name__ == '__main__':
    main()
    