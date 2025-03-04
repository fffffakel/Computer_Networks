import csv
import time

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import DictCursor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


app = Flask(__name__)

DB_CONFIG = {
    "dbname": "parser_task2",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "1717"
}

def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price TEXT,
            availability TEXT,
            url TEXT NOT NULL
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

create_table()

def save_to_database(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    for item in data:
        name, price, availability, url = item
        cursor.execute("""
            INSERT INTO products (name, price, availability, url) 
            VALUES (%s, %s, %s, %s);
        """, (name, price, availability, url))
    conn.commit()
    cursor.close()
    conn.close()

def fetch_data_from_database():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM products;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]

@app.route('/parse', methods=['GET'])
def parse():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(5)

        cookie_button = driver.find_element(By.XPATH, '/html/body/div[1]/div')
        cookie_button.click()
        time.sleep(1)

        search_field = driver.find_element(By.XPATH, '//*[@id="query_box"]/form/div/input')
        search_field.send_keys("iphone 16")
        search_field.send_keys(Keys.RETURN)
        time.sleep(5)

        all_data = []
        while True:
            products = driver.find_elements(By.XPATH, "//div[contains(@class, 'product-item') and contains(@class, 'rs-product-item')]")
            for product in products:
                name = product.find_element(By.XPATH, './/a[@class ="product-item__link"]/span').text.strip()
                try:
                    price = product.find_element(By.XPATH, './/div[@class="product-item__price-visible"]/span[1]').text.strip()
                except Exception:
                    price = "N/A"
                availability = product.find_element(By.CSS_SELECTOR, '.product-item__available span')
                script = """
                const element = arguments[0];
                const style = window.getComputedStyle(element, '::before');
                return style.content;
                """
                content = driver.execute_script(script, availability)
                link = product.find_element(By.XPATH, './/a[@class="product-item__link"]').get_attribute('href')
                all_data.append((name, price, content, link))

            try:
                active_page = driver.find_element(By.XPATH, '//span[@class="pagination-item pagination-item-active"]')
                current_page_number = int(active_page.text)
                next_page_number = current_page_number + 1
                next_page_link = driver.find_element(By.XPATH, f'//a[@data-page="{next_page_number}"]')
                next_page_link.click()
                time.sleep(5)
            except Exception:
                break

        driver.quit()

        save_to_database(all_data)
        return jsonify(), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch', methods=['GET'])
def fetch():
    try:
        data = fetch_data_from_database()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)