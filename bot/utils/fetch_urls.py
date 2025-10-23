from bot.config import BROWSERLESS_TOKEN
from selenium import webdriver
from selenium.webdriver.common.by import By
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Create a single-threaded executor
executor = ThreadPoolExecutor(max_workers=1)

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


def get_jar_amount(url: str, previous_amount: str) -> str:
    driver = None
    amount = previous_amount
    try:
        driver = webdriver.Remote(
            command_executor="https://browserless-production-dadb.up.railway.app/webdriver",
            options=chrome_options
        )
        driver.get(url)
        driver.implicitly_wait(10)
        elements = driver.find_elements(By.CLASS_NAME, "stats-data-value")
        if len(elements) == 2:
            amount = elements[0].text.replace(' ', '')
        elif len(elements) == 1:
            jar_is_closed = len(driver.find_elements(By.CLASS_NAME, "done-jar-status-subtext")) > 0
            if jar_is_closed:
                amount = elements[0].text.replace(' ', '')
    except Exception:
        amount = previous_amount
    finally:
        if driver:
            driver.quit()
    return amount


# async wrapper
async def get_jar_amount_async(url: str, previous_amount="0₴") -> str:
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(executor, get_jar_amount, url, previous_amount),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        return previous_amount