import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


driver = webdriver.Chrome()
driver.get("https://indexiq.ru/")
time.sleep(5)

cookie_button = driver.find_element(By.XPATH,'/html/body/div[1]/div')
cookie_button.click()
time.sleep(1)

search_field = driver.find_element(By.XPATH,'//*[@id="query_box"]/form/div/input')
search_field.send_keys("iphone 16")
search_field.send_keys(Keys.RETURN)
time.sleep(5)
all_data = []
all_names,all_prices,all_availability,all_links = [],[],[],[]
while True:
    products = driver.find_elements(By.XPATH,"//div[contains(@class, 'product-item') and contains(@class, 'rs-product-item')]")
    for product in products:
        name = product.find_element(By.XPATH,'.//a[@class ="product-item__link"]/span')
        name = name.text.strip()
        all_names.append(name)
        try:
            price = product.find_element(By.XPATH, './/div[@class="product-item__price-visible"]/span[1]').text.strip()
        except Exception:
            price = "N/A"
        all_prices.append(price)
        availability = product.find_element(By.CSS_SELECTOR, '.product-item__available span')
        script = """
        const element = arguments[0];
        const style = window.getComputedStyle(element, '::before');
        return style.content;
        """
        content = driver.execute_script(script, availability)
        all_availability.append(content)
        link = product.find_element(By.XPATH,'.//a[@class="product-item__link"]')
        link = link.get_attribute('href')   
        all_links.append(link)

    try:
        active_page = driver.find_element(By.XPATH, '//span[@class="pagination-item pagination-item-active"]')
        current_page_number = int(active_page.text)
        next_page_number = current_page_number + 1
        next_page_link = driver.find_element(By.XPATH, f'//a[@data-page="{next_page_number}"]')
        next_page_link.click()
        time.sleep(5) 
    except:
        break
driver.quit()

all_data = list(zip(all_names,all_prices,all_availability,all_links))
with open('Seti\seti_2\products.csv',mode = 'w',encoding='utf-8') as w_file:
    write = csv.writer(w_file,lineterminator='\r')
    write.writerow(["Name","Price","Availability","URL"])
    write.writerows(all_data)
