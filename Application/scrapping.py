from Utilities import Web, By, progressBar
import json
from Constants import OUTPUT_JSON_FILE_PATH, OUTPUT_EXCEL_FILE_PATH, OUTPUT_CSV_FILE_PATH
import colorama
import pandas as pd
import time

df = pd.DataFrame(columns=["name", "link", "cat_1", "cat_2", "cat_3", "cat_4", "cat_5", "cat_6", "cat_7", "cat_8", "cat_9", "cat_10"])

def _retrieve_main_categories(client) :

    browser = client

    main_url = "https://www.migros.com.tr/"

    browser.openWebPage(main_url)

    dummy = browser.createElement("//*[@id=\"header-money-discounts\"]")
    browser.clickOnElement(dummy)

    dummy = browser.createElement("/html/body/sm-root/div/fe-product-cookie-indicator/div/div/button[1]")
    browser.clickOnElement(dummy)

    catagories_element = browser.createElement("//*[@id=\"header-wrapper\"]/div[3]/div/div")
    browser.clickOnElement(catagories_element)

    all_category_elements = browser.createElement("//*[@id=\"header-wrapper\"]/div[3]/div[1]/div[2]/div[1]").find_elements(By.TAG_NAME, "a")

    category_link_map = {}
    exceptions = ("Tüm İndirimli Ürünler", "Sadece Migros'ta")
    for current_catogory_element in all_category_elements :
        category_name = current_catogory_element.text
        category_link = current_catogory_element.get_attribute("href")

        if category_name not in exceptions :
            category_link_map[category_name] = category_link

    return category_link_map

def _retrieve_sub_category_list(name, link, client) :
    global df

    catalog = {}
    
    def update_catalog(lst):
        current_dict = catalog
        for item in lst:
            if item not in current_dict:
                current_dict[item] = {}
            current_dict = current_dict[item]

    def _get_products(cats, main_link, product_count) :
        global df

        browser = Web(isHidden=True)
        browser.openWebPage(main_link)

        cats = cats + [None] * (10 - len(cats))

        if product_count > 30 :
            button = browser.createElement("//*[@id=\"pagination-button-last\"]/span[2]")
            browser.clickOnElement(button)
            time.sleep(1)

            last_page = browser.browser.current_url.split("=")[-1]

            browser.openWebPage(main_link)
        else :
            last_page = 1

        for i in range(1, int(last_page)+1):
            products = browser.createElement("/html/body/sm-root/div/main/sm-product/article/sm-list/div/div[4]/div[2]/div[4]").find_elements(By.TAG_NAME, "sm-list-page-item")

            for product in products:
                splitted_name = product.text.split("\n")
                name = splitted_name[0] if not splitted_name[0].startswith("%") else splitted_name[2]
                link = product.find_element(By.TAG_NAME, "a").get_attribute("href")
                df = pd.concat([df, pd.DataFrame([[name, link, *cats]], columns=["name", "link", "cat_1", "cat_2", "cat_3", "cat_4", "cat_5", "cat_6", "cat_7", "cat_8", "cat_9", "cat_10"])], ignore_index=True)
                    
            if product_count > 30 and i != int(last_page):
                button = browser.createElement("//*[@id=\"pagination-button-next\"]")
                browser.clickOnElement(button)

        browser.terminate()

    temp = []
    def top_down_research(name, browser) :

        temp.append(name)

        category_list = browser.createElement("/html/body/sm-root/div/main/sm-product/article/sm-list/div/div[4]/div[1]/sm-product-filters-desktop/div/div[2]/div[2]").find_elements(By.TAG_NAME, "div")
        if len(category_list) == 1:

            last_element_name = category_list[0].text[0:category_list[0].text.find("(")].strip()
            owner_name = name
            if last_element_name == owner_name :
                current_path = temp
            else :
                current_path = temp + [last_element_name]
            last_elements_procudt_count = category_list[0].text[category_list[0].text.find("(")+1:category_list[0].text.find(")")]
            #print(colorama.Fore.GREEN, "Found: ", colorama.Fore.RESET, current_path)

            update_catalog(current_path)

            last_elements_link = category_list[0].find_element(By.TAG_NAME, "a").get_attribute("href")

            try :
                _get_products(current_path, last_elements_link, int(last_elements_procudt_count))
            except :
                print(colorama.Fore.BLACK, colorama.Back.RED, f"Error occured while getting products from: _get_products({current_path}{last_elements_link}{int(last_elements_procudt_count)})", colorama.Fore.RESET, current_path)
            return

        counter = 0

        while counter < len(category_list) : 

            try :
                current_sub_category = browser.createElement("/html/body/sm-root/div/main/sm-product/article/sm-list/div/div[4]/div[1]/sm-product-filters-desktop/div/div[2]/div[2]").find_elements(By.TAG_NAME, "div")[counter]

                sub_catagory_name = current_sub_category.text[0:current_sub_category.text.find("(")].strip()
                sub_catagory_link = current_sub_category.find_element(By.TAG_NAME, "a").get_attribute("href")
                sub_category_product_count = current_sub_category.text[current_sub_category.text.find("(")+1:current_sub_category.text.find(")")]
            except :
                #print(colorama.Fore.BLACK, colorama.Back.RED, f"***ERROR: Couldn't resolve the element of {name}, {category_list[counter]}", colorama.Fore.RESET, colorama.Back.RESET)
                counter = counter + 1
                continue
            
            browser.openWebPage(sub_catagory_link)

            top_down_research(sub_catagory_name, browser)

            counter = counter + 1

            browser.browser.back()
            temp.pop()
        
    browser = client
    browser.openWebPage(link)

    top_down_research(name, browser)

    with open(OUTPUT_JSON_FILE_PATH, "r", encoding="utf-8") as file :
        data = json.load(file)
    with open(OUTPUT_JSON_FILE_PATH, "w", encoding="utf-8") as file :
        json.dump({**data, **catalog}, file, indent=4, ensure_ascii=False)

def scrapper() :
    global df

    client = Web(isHidden=True)

    category_link_map = _retrieve_main_categories(client)

    iterable = category_link_map.items()
    print(colorama.Fore.CYAN)
    
    for name, link in progressBar(iterable, "Scrapping Progress", length=40) :
        _retrieve_sub_category_list(name, link, client)
        
    df.to_excel(OUTPUT_EXCEL_FILE_PATH, index=False)
    df.to_csv(OUTPUT_CSV_FILE_PATH, index=False)

    print(colorama.Fore.RESET)

    client.terminate()
