import asyncio
import time
from playwright.async_api import async_playwright, expect

async def configurator_scraper(product_number:str):  
    OLD_CONFIGURATOR_URL = f"https://www.lenovo.com/us/en/configurator/dcg/configurator?lfo={product_number}"
        
    async with async_playwright() as p:
        print(f"START - old_configurator - {product_number}")
        print("===========================")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(url=OLD_CONFIGURATOR_URL, wait_until="networkidle")
        
        configuration_options = {
            "product_number": product_number
        } 
        
        included_items_container = await page.query_selector(selector="#summary .divider + .LeWidget-Dropdown")
        print(included_items_container)
        if included_items_container is None:
            print("===========================")
            print("END - old_configurator")
            return None
        
        included_items_sections = await included_items_container.query_selector_all(".LeWidget-DescList")  
        for s in included_items_sections:
            section_title = await s.query_selector(".LeWidget-DescList-info-content-title")
            section_title = await section_title.text_content()
            section_title = section_title.lower()
            
            configuration_options[section_title] = [] 

            section_items = await s.query_selector_all(".LeWidget-DescList-info-content-desc")
            for si in section_items:
                item = await si.text_content()
                item = item[3:].strip()
                configuration_options[section_title].append(item)
        
        configuration_sections =  await page.query_selector_all(selector=".section")
        for s in configuration_sections:
            section_title = await s.query_selector(selector="h4.sectionTitle")
            if section_title is None:
                continue
            section_title = await section_title.text_content()
            section_title = section_title.lower().replace(" ", "_")
            
            configuration_options[section_title] = [] 
            
            section_items = await s.query_selector_all(selector=".features .feature .info h5")
            section_items = [await si.text_content() for si in section_items]                
            configuration_options[section_title] = section_items 
        
        print("===========================")
        print("END - old_configurator")
        print(configuration_options)

# Run the asyncio event loop
asyncio.run(configurator_scraper(product_number="7D7QA01YNA"))
