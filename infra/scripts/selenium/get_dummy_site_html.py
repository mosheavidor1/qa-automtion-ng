"""
This script is packed to exe 'get_dummy_site_html.exe' in shared folder qa\automation_ng\scripts\selenium
It was packed via this command:
Activate virtual env: .\activate.ps1
pip install pyinstaller
pyinstaller --onefile --add-binary="chromedriver.exe;." main.py

"""

"""
from selenium import webdriver
import os


def print_html():
    html = None
    dirpath = os.path.dirname(__file__)
    chrome_driver_path = os.path.join(dirpath, 'chromedriver.exe')
    try:
        driver = webdriver.Chrome(chrome_driver_path)
        driver.get("http://example.com/")
        html = driver.page_source
    except Exception as e:
        print(e)
    finally:
        driver.close()
        if html is not None:
            print(html)


if __name__ == '__main__':
    print_html()
"""