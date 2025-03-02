import asyncio
from playwright.async_api import async_playwright
from datetime import datetime as dt
import pandas as pd
import time
import os

BASE_URL = "https://www.lenovo.com"

IS_TEST = False
SHOW_DETAILED_LOGS = False

async def start_scraper():
    print(f"SCRAPER - START - {dt.now().strftime("%H:%M:%S")}")
    print("==========================")
    start_time = dt.now()
    available_products = await get_products()
    configurator_options = []
    failed_products = []
    for p in available_products.itertuples():
        get_product_config = await get_config_by_product_number(product_number=p.product_number)
        
        if get_product_config["is_success"]:
            configurator_options.append(get_product_config["data"])
        elif get_product_config["data"] is not None:
            failed_products.append(get_product_config["data"]["product_number"])
            
    print(f"RETRY FOR FAILED PRODUCTS - {failed_products}")
    print("==========================")
       
    for p in failed_products:
        get_product_config = await get_config_by_product_number(product_number=p)
        
        if get_product_config["is_success"]:
            configurator_options.append(get_product_config["data"])
            
    config_options_df = pd.DataFrame(configurator_options)
    
    final_result = pd.merge(
        left=available_products,
        right=config_options_df,
        how="inner",
        on="product_number"
    )    
    
    export_to_excel(final_result)
    
    execution_time = dt.now() - start_time
    print("==========================")
    print(f"SCRAPER - END")
    print(f"TOTAL TIME - {round(execution_time.total_seconds() / 60, 0)} min")
    print("==========================")
    
    return final_result
    
def export_to_excel(data:pd.DataFrame, filename:str = None):
    current_dt = dt.now().strftime("%Y%m%d_%H%M%S")
    EXPORT_FOLDER = os.path.join(os.getcwd(), "data")
    if filename is None:
        filename = f"data_{current_dt}.xlsx"

    try:
        if not os.path.exists(EXPORT_FOLDER):
            os.makedirs(EXPORT_FOLDER)
    except:
        print("Cannot create folder!")
        return
    
    EXPORT_FILE = os.path.join(EXPORT_FOLDER, filename)
    
    data.to_excel(EXPORT_FILE, index=False, header=True)
    
    return True
            
async def get_products():
    AVAILABLE_PRODUCTS_URL = f"{BASE_URL}/us/en/servers-storage/servers/#servers"

    available_products_list = []
        
    async with async_playwright() as p:
        print("START - get_products")
        print("------------------------")
        browser = await p.chromium.launch(
            headless=True
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(AVAILABLE_PRODUCTS_URL)

        server_categories = await page.query_selector_all(
            selector="#servers .card-grid .cards .cards__title a"
        )
        server_categories = [
            {"name": await s.inner_text(), "url": await s.get_attribute("href")}
            for s in server_categories
        ]

        for i in range(4):
            sc = server_categories[i]
            if IS_TEST == True and sc["name"] != "Tower Servers":
                continue
            await page.goto(url=sc["url"], wait_until="networkidle")
            
            product_list = await page.query_selector(selector=".product_list")
            await product_list.scroll_into_view_if_needed()
            
            product_groups = []
            
            while True:
                current_product_groups = await page.query_selector_all(
                    selector=".pc_product_list .product_item a.cta-button_subseries",
                )
                
                await current_product_groups[-1].scroll_into_view_if_needed()
                
                if len(product_groups) == len(current_product_groups):
                    product_groups = current_product_groups
                    break

                product_groups = current_product_groups
                time.sleep(2)
            
            if SHOW_DETAILED_LOGS:    
                print(f"CATEGORY URL - {sc["url"]}")
                print(f"PRODUCT GROUPS FOUND - {len(product_groups)}")
                print("---------------------------------------------")

            pg_url = None
            try:
                for pg in product_groups:
                    pg_page = await context.new_page()
                    pg_url = await pg.get_attribute("href")
                    pg_url = f"{BASE_URL}{pg_url}"

                    await pg_page.goto(url=pg_url, wait_until="load")
                    
                    available_products = await pg_page.query_selector_all(
                        selector=".product_list .product_item[data-product-code]"
                    )

                    for ap in available_products:
                        server_name = await ap.query_selector(".product_title span")
                        server_number = await ap.query_selector(
                            ".product-number span:last-child"
                        )
                        
                        available_products_list.append({
                            "product_number": await server_number.inner_text(),
                            "name": await server_name.inner_text(),
                            "url": pg_url,
                            "category": sc["name"],
                            "category_url": sc["url"]
                        })
                        
                    
                    await pg_page.close()
                                                
                        # server = {
                        #     "name": await server_name.inner_text(),
                        #     "url": pg_url,
                        #     "productNumber": await server_number.inner_text(),
                        #     "category": sc,
                        #     "features": {},
                        #     "basic_configuration": {},
                        #     "additional_configuration": []
                        # }

                        # server_features = await ap.query_selector_all(".features ul li")
                        # for f in server_features:
                        #     feature = await f.text_content()
                        #     if isNullOrEmpty(feature.strip()):
                        #         continue
                        #     feature = [e.strip() for e in feature.split(":")]
                        #     if len(feature)>1:
                        #         server["features"][feature[0]] = feature[1]

                        # server_basic_config = await ap.query_selector_all(
                        #     ".key_details ul li"
                        # )
                        # for bc in server_basic_config:
                        #     basic_config = await bc.text_content()
                        #     if isNullOrEmpty(basic_config.strip()):
                        #         continue
                        #     basic_config = [e.strip() for e in basic_config.split(":")]
                        #     if len(basic_config)>1:
                        #         server["basic_configuration"][basic_config[0]] = basic_config[1]

                        # servers.append(server)
                    if IS_TEST:
                        break
            except Exception as e:
                print("Failed at: ", pg_url)
                print("--------------------------------")
                print(e)
            if IS_TEST:
                break

        print(f"PRODUCTS FOUND - {len(available_products_list)}")
        print("------------------------")
        print("END - get_products")
        print("==========================")
        await browser.close()
        return pd.DataFrame(available_products_list)

async def get_config_by_product_number(product_number:str):
    NEW_CONFIGURATOR_URL = f"https://www.lenovo.com/us/en/configurator/dcg/index.html?lfo={product_number}"
    result = {
        "is_success": False,
        "data": None           
    }

    async with async_playwright() as p:
        print(f"START - get_config_by_product_number - {product_number}")
        print("===========================")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        configuration_options = {
            "product_number": product_number
        } 
        try:
            await page.goto(url=NEW_CONFIGURATOR_URL)
            config_iframe = await page.query_selector(selector="iframe")   
            await page.goto(url=await config_iframe.get_attribute("src"), wait_until="networkidle")
                    
            if SHOW_DETAILED_LOGS:
                print("PAGE LOADED")
                print()
            
            pop_ups = await page.query_selector_all(".ant-modal")
            
            if pop_ups is not None and len(pop_ups) > 0:
                for pop in pop_ups:
                    close_btn = await pop.query_selector(".ant-modal-close")
                    try:
                        if close_btn is not None:
                            await close_btn.click()
                    except:
                        continue
                
            configurator_tabs = await page.query_selector_all(selector=".configurator-tabs .slick-track .slick-slide")

            if len(configurator_tabs) == 0:
                await browser.close()
                configuration_options = await old_configurator(product_number=product_number)
                
                if configuration_options is None:
                    raise Exception()
                else:
                    result["is_success"] = True
                    result["data"] = configuration_options
                    return result  
        except:
            result["data"] = configuration_options
            print(f"CONFIGURATOR NOT AVAILABLE FOR PRODUCT NUMBER: {product_number}")
            print("===========================")
            print("END")
            return result
        
        if SHOW_DETAILED_LOGS:
            print("TABS: ", [await e.text_content() for e in configurator_tabs])
            print()

        configurator = await page.query_selector(".configurator")
           
        for tab_index, tab in enumerate(configurator_tabs):
            await tab.click()
              
            if SHOW_DETAILED_LOGS:                    
                print(f"TAB {tab_index+1} {await tab.text_content()}")
                print("-------------------------------------------------")
            
            try:
                await configurator.wait_for_selector(selector=".ant-collapse .ant-collapse-item", timeout=5000)
            except:
                if SHOW_DETAILED_LOGS:
                    print(f"SKIPPED")
                    print("-------------------------------------------------")
                continue
            
            config_items = await configurator.query_selector_all(selector=".ant-collapse .ant-collapse-item")       
            
            if SHOW_DETAILED_LOGS:
                print("CONFIG ITEMS FOUND")
                        
            for ci in config_items:   
                show_more_btns = await ci.query_selector_all(selector=".section-panel-body .showMore a")

                if show_more_btns is not None and len(show_more_btns) > 0:
                    for btn in show_more_btns:
                        try:
                            await btn.click(timeout=1000)
                        except:
                            continue
                        
                attr_name = f"temp_{product_number}"
                            
                section_name = await ci.query_selector(selector=".section-panel-header__item__title span.disableSelection")
                section_items = await ci.query_selector_all(selector=".section-panel-body__feature__description span")
                                
                if section_name is not None:
                    section_name = await section_name.text_content()
                else:
                    section_name = await ci.query_selector(selector=".section-panel-header__empty-item span.disableSelection")
                    if section_name is not None:
                        section_name = await section_name.text_content()
                        
                attr_name = (attr_name if section_name is None else section_name).lower().replace(" ", "_")
                
                if attr_name.startswith("value_added_option"):
                    continue
                
                configuration_options[attr_name] = []
                for i in section_items:
                    sec_item = await i.text_content()
                    sec_item = sec_item.replace('"', "").replace(r"\xa0", "").replace(r"\x", "")
                    configuration_options[attr_name].append(sec_item)
            
            if SHOW_DETAILED_LOGS:                  
                print("-------------------------------------------------")

        print("===========================")
        print("END - get_config_by_product_number")
        print("==========================")
        print(configuration_options)
        await browser.close()
        result["is_success"] = True
        result["data"] = configuration_options
        return result
    
async def old_configurator(product_number:str):
    OLD_CONFIGURATOR_URL = f"https://www.lenovo.com/us/en/configurator/dcg/configurator?lfo={product_number}"
        
    async with async_playwright() as p:
        print(f"START - old_configurator - {product_number}")
        print("===========================")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(url=OLD_CONFIGURATOR_URL, wait_until="load")
        
        configuration_options = {
            "product_number": product_number
        } 
        
        included_items_container = await page.query_selector(selector="#summary .divider + .LeWidget-Dropdown")
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
                item = item[3:].replace(r"\xa0", "").strip()
                configuration_options[section_title].append(item)
        
        configuration_sections = await page.query_selector_all(selector=".section")
        for s in configuration_sections:
            section_title = await s.query_selector(selector="h4.sectionTitle")
            if section_title is None:
                continue
            section_title = await section_title.text_content()
            section_title = section_title.lower().replace(" ", "_")
            
            configuration_options[section_title] = [] 
            
            section_items = await s.query_selector_all(selector=".features .feature .info h5")
            
            for si in section_items:
                item = await si.text_content()
                item = item.replace(r"\xa0", "").strip()
                configuration_options[section_title].append(item)
                
            # section_items = [await si.text_content() for si in section_items]                
            # configuration_options[section_title] = section_items 
        
        print("===========================")
        print("END - old_configurator")
        return configuration_options
    
if __name__ == "__main__":
    #asyncio.run(start_scraper())
    asyncio.run(get_config_by_product_number("7D9EA012NA"))