from selenium.webdriver.chrome.options import Options
from selenium import webdriver

url = 'https://github.com/'

options = Options()
options.add_argument("--headless")
options.add_argument("window-size=1400,1500")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# Navigate to github.com
driver.get(url)

# Extract the top heading from github.com

print('success')