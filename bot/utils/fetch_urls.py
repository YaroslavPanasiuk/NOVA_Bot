import requests
import re
from bot.config import BROWSERLESS_TOKEN
import aiohttp

async def get_jar_amount(url: str) -> list[str]:
    html = await get_rendered_html(url)

    pattern = r'<div class="stats-data-value">(.*?)</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    if len(matches) == 2 or (len(matches) == 1 and "has been reached" in html):
        result = matches[0].replace('&nbsp;', '')
        return result.replace(' ', '')
    return "0₴"

async def get_rendered_html(url: str) -> str:
    endpoint = "https://production-sfo.browserless.io/chromium/bql"

    query = """
    mutation GetHtml($url: String!) {
        goto(url: $url waitUntil: interactiveTime) {
            status
        }

        
        html(selector: "body") {
            html
        }
    }
    """

    variables = {
        "url": f"{url}"
    }

    data = await send_post_async(
        f"{endpoint}?token={BROWSERLESS_TOKEN}",
        json={"query": query, "variables": variables}
    )
    html_content = data.get("data", {}).get("html", "")
    return html_content['html']


async def send_post_async(url, json):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            return await response.json()