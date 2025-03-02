import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import time
from enum import Enum
import random

class LoginCredentials():
    def __init__(self, username, password):
        self.username = username
        self.password = password

class OPERATOR(Enum):
    EVN_LOGIN = "https://evnonline.mk/auth/login"
    VODOVOD_LOGIN = "https://e.vodovod-skopje.com.mk/Login"
    EVN_LOGIN_CREDENTIALS = LoginCredentials(username="stankovski.n@hotmail.com", password="stankovski98")
    VODOVOD_LOGIN_CREDENTIALS = LoginCredentials(username="stankovski.n@hotmail.com", password="55yxnkHo5!&#L?6f") 

async def pay():
    await pay_evn()    
    
async def pay_evn():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )
        context = await browser.new_context(viewport={ "width": 1600, "height": 800 })
        page = await context.new_page()
        #await stealth_async(page=page)
        await page.goto(url=OPERATOR.EVN_LOGIN.value, wait_until="networkidle")
                            
        await page.fill(selector='input[name="UsernameEmail"]', value=OPERATOR.EVN_LOGIN_CREDENTIALS.value.username)
        await page.fill(selector='input[name="password"]', value=OPERATOR.EVN_LOGIN_CREDENTIALS.value.password)
        await page.click(selector='button.buttonNext')
                        
        iframes = await page.query_selector_all(selector="iframe")
        recaptcha_iframes = [
            iframe for iframe in iframes
            if 'recaptcha' in (await iframe.get_attribute('title') or '').lower() and await iframe.is_visible()
        ]
        
        if recaptcha_iframes is not None and len(recaptcha_iframes) > 0:
            await page.pause()
        
        #await context.storage_state(path="session_state.json")

        await page.click(selector="#mobilemainmenu #billcheck a")
        
        invoice_tables = await page.query_selector_all(selector="mat-expansion-panel")
        
        print("TEST")
        print(invoice_tables)
        
        # for it in invoice_tables:
        #     panel_title = await it.query_selector("mat-panel-title")
        #     print(await panel_title.inner_text())
    
        await browser.close()
    
# async def pay_vodovod():
#     print("vod")
    
if __name__ == "__main__":
    asyncio.run(pay())

