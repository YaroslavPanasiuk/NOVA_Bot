import requests
import re
from bot.config import BROWSERLESS_TOKEN

def get_jar_amount(url: str) -> list[str]:
    html = get_rendered_html(url)

    pattern = r'<div class="stats-data-value">(.*?)</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    result = matches[0].replace('&nbsp;', '')
    return result.replace(' ', '')

def get_rendered_html(url: str) -> str:
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

    response = requests.post(
        f"{endpoint}?token={BROWSERLESS_TOKEN}",
        json={"query": query, "variables": variables}
    )
    data = response.json()
    html_content = data.get("data", {}).get("html", "")
    return html_content['html']
