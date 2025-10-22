from bot.config import BROWSERLESS_TOKEN
from selenium import webdriver
from selenium.webdriver.common.by import By
import asyncio

chrome_options = webdriver.ChromeOptions()
chrome_options.set_capability('browserless:token', BROWSERLESS_TOKEN)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-background-timer-throttling")
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--disable-breakpad")
chrome_options.add_argument("--disable-component-extensions-with-background-pages")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
chrome_options.add_argument("--disable-ipc-flooding-protection")
chrome_options.add_argument("--disable-renderer-backgrounding")
chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
chrome_options.add_argument("--force-color-profile=srgb")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--metrics-recording-only")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

def get_jar_amount(url: str) -> str:
    driver = webdriver.Remote(
        command_executor="https://browserless-production-dadb.up.railway.app/webdriver",
        options=chrome_options
    )

    driver.get(url)
    driver.implicitly_wait(5)
    try:
        amount = driver.find_element(By.CLASS_NAME, "stats-data-value").text.replace(' ', '')
    except:
        amount = "0₴"

    driver.quit()
    return amount

# async wrapper
async def get_jar_amount_async(url: str) -> str:
    return await asyncio.to_thread(get_jar_amount, url)


    