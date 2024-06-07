import os
from flask import Flask, render_template, request, redirect, url_for
import requests
from urllib.request import urlopen as uReq
import logging
import time
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image
import cv2
import pytesseract
from pytesseract import Output
import re
from flask_sqlalchemy import SQLAlchemy
logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
db = SQLAlchemy(app)
app.app_context().push()

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.String(20)) 
    def __repr__(self):
        return '<name %r>' % self.id


def store_item_price_in_database(item_name, price):
    # Create a new Item object
    new_item = Item(name=item_name, price=price)
    db.session.add(new_item)
    db.session.commit()

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

def get_images_from_google(driver, delay, max_images):
    print('IN GET IMAGES')    
    def scroll_down(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

    image_urls = set()
    results_start = 0

    while len(image_urls)  < max_images:                         
        thumbnails = driver.find_elements(By.CSS_SELECTOR, ".mNsIhb")
        scroll_down(driver)
        for img in thumbnails[results_start:len(thumbnails)]:
            try:
                driver.execute_script("arguments[0].click();", img)
                time.sleep(delay)
            except:
                continue 

            images =  driver.find_elements(By.CSS_SELECTOR, ".iPVvYb")
            print(len(images))
            for image in images:
                print(image.get_attribute('src'))
            
                if image.get_attribute('src') in image_urls:
                    break

                if image.get_attribute('src') and 'http' in image.get_attribute('src'):
                    image_urls.add(image.get_attribute('src'))
                    print(f"Found {len(image_urls)}")
            if len(image_urls) >= max_images:
                break

    return image_urls

def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return image

def perform_ocr(image):
    custom_config = r'--oem 3 --psm 12'
    ocr_result = pytesseract.image_to_data(image, lang='eng', config=custom_config, output_type=Output.DICT)
    return ocr_result

def extract_items_prices(ocr_result):
    items_prices = []
    n_boxes = len(ocr_result['text'])

    current_line = []
    previous_top = -1

    for i in range(n_boxes):
        if int(ocr_result['conf'][i]) > 75:
            text = ocr_result['text'][i].strip()
            top = ocr_result['top'][i]

            if text:
                # If the vertical distance between current box and previous box is large, it's a new line
                if previous_top != -1 and abs(top - previous_top) > 10:
                    combined_text = ' '.join(current_line)
                    pattern = re.compile(r'([a-zA-Z\s\./|:]+)\s*(\d+(?:[\.,]\d+)?(?:/-)?)')
                    matches = pattern.findall(combined_text)
                    if matches:
                        items_prices.extend(matches)
                    current_line = []

                current_line.append(text)
                previous_top = top

    # Check the last accumulated line
    if current_line:
        combined_text = ' '.join(current_line)
        pattern = re.compile(r'([a-zA-Z\s\./|:]+)\s*(\d+(?:[\.,]\d+)?(?:/-)?)')
        matches = pattern.findall(combined_text)
        if matches:
            items_prices.extend(matches)

    # Filter out invalid items
    filtered_items_prices = [(item.strip(), price) for item, price in items_prices if len(item.strip()) > 2]

    return filtered_items_prices

def clean_price(price):
    clean_price = re.sub(r'[^\d.]', '', price)
    return clean_price

def download_image(download_path, url, file_name):
    try:
        image_content = requests.get(url).content
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file)

        if image.format not in ["JPEG", "PNG"]:
            print(f"Skipping image with unsupported format: {url}")
            return

        file_path = os.path.join(download_path, file_name)

        with open(file_path, "wb") as f:
            image.save(f, "JPEG")

        print("Success")
    except Exception as e:
        print('FAILED -', e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form.get('url')
        count = request.form.get('count')
        if query:
            return redirect(url_for('show_images', query=query,count=int(count)))
    return render_template('index.html')

@app.route('/images')
def show_images():
    query = request.args.get('query')
    count=int(request.args.get('count'))
    print(query)
    if not query:
        return redirect(url_for('index'))

    download_path = os.path.join("static", "scrappedimgs")
    os.makedirs(download_path, exist_ok=True)

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        driver.get(search_url)
        print("OK")
        urls = get_images_from_google(driver, 1, count)

        for i, url in enumerate(urls):
            download_image(download_path, url, f"{query}-{i}.jpg")
    finally:
        driver.quit()

    image_files = os.listdir(download_path)
    image_urls = [os.path.join("static", "scrappedimgs", img) for img in image_files if not img.endswith('_ocr.txt')]

    return render_template('result.html', image_urls=image_urls)

@app.route('/apply_ocr', methods=['POST'])
def apply_ocr():
    download_path = os.path.join("static", "scrappedimgs")
    image_files = [img for img in os.listdir(download_path) if not img.endswith('_ocr.txt')]

    ocr_results = {}
    for image_file in image_files:
        file_path = os.path.join(download_path, image_file)
        preprocessed_image = preprocess_image(file_path)
        ocr_result = perform_ocr(preprocessed_image)
        items_prices = extract_items_prices(ocr_result)
        ocr_results[image_file] = items_prices

        ocr_results_path = os.path.join(download_path, f"{image_file}_ocr.txt")
        with open(ocr_results_path, "w") as f:
            for item, price in items_prices:
                cleaned_price = clean_price(price)
                f.write(f"Item: {item.strip()}, Price: {cleaned_price}\n")

    return redirect(url_for('show_images_with_ocr'))



@app.route('/show_images_with_ocr')
def show_images_with_ocr():
    download_path = os.path.join("static", "scrappedimgs")
    image_files = os.listdir(download_path)
    image_urls = [os.path.join("static", "scrappedimgs", img) for img in image_files if not img.endswith('_ocr.txt')]

    ocr_files = [os.path.join("static", "scrappedimgs", img) for img in image_files if img.endswith('_ocr.txt')]
    ocr_results = {}
    for ocr_file in ocr_files:
        with open(ocr_file, "r") as f:
            ocr_text = f.read().splitlines()
            if len(ocr_text) > 3:  # Filter out OCR results with less than 4 items
                ocr_results[ocr_file] = ocr_text
                                # Extract items and prices from OCR results and store them in the database
                items_prices = []
                for line in ocr_text:
                    # Extract item name and price from each line
                    # Assuming the line format is "Item: [item_name], Price: [price]"
                    match = re.match(r'Item: (.+), Price: (.+)', line)
                    if match:
                        item_name = match.group(1)
                        price = match.group(2)
                        items_prices.append((item_name.strip(), price.strip()))
                
                # Store items and prices in the database
                for item_name, price in items_prices:
                    store_item_price_in_database(item_name, price)
    delete_images()
    return render_template('result_with_ocr.html', image_urls=image_urls, ocr_results=ocr_results)


@app.route('/delete_images', methods=['POST'])
def delete_images():
    download_path = os.path.join("static", "scrappedimgs")
    for file in os.listdir(download_path):
        os.remove(os.path.join(download_path, file))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
