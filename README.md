# Image Server Project

## Overview

This project is designed to scrape menu images from Google Images for restaurants, perform OCR (Optical Character Recognition) on these images to read items and prices, and store the extracted information in a database. The application is built using Flask for the web interface and backend logic, SQLite for the database, and various Python libraries for image processing and OCR.

## Assumptions

1. **Image Quality**: The menu images downloaded from Google Images are assumed to be of sufficient quality and resolution for OCR processing.
2. **Text Legibility**: The text on the menu images is assumed to be clear and legible for the Tesseract OCR tool to accurately extract information.
3. **Menu Format**: The menu items and prices follow a consistent format that matches the regular expression used in the code. Specifically, it is assumed that:
   - Item names consist of alphabetic characters, spaces, dots, slashes, pipes, or colons.
   - Prices are numeric and may include commas, periods, or dashes.
4. **Compliance**: The scraping process is assumed to be compliant with legal requirements and Google’s terms of service.

## Features

- **Image Scraping**: Scrape images from Google Images based on a search query.
- **Image Preprocessing**: Preprocess images to enhance text recognition.
- **OCR Processing**: Extract text from images using Tesseract OCR.
- **Data Extraction**: Extract menu items and prices using regular expressions.
- **Database Storage**: Store extracted items and prices in an SQLite database.
- **Web Interface**: Provide a web interface for querying, viewing images, and displaying OCR results.

## Requirements

- Python 3.10+
- Flask
- Selenium
- Tesseract OCR
- OpenCV
- Pillow
- SQLite

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mohammad-murasif/imgserver.git
   cd imgserver



2. **Create and activate a virtual environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
3. **Install the required packages**:

    ```bash
    pip install -r requirements.txt
4. **Install Tesseract OCR**:
    Follow the instructions for your operating system: Tesseract Installation
    Set up the database:

    ```bash
    flask shell
    from app import db
    db.create_all()
    exit()
## Usage
**Run the Flask application**:

    ```bash
        python app.py
    ```

**Access the web interface**:

Open your browser and go to http://0.0.0.0:8000.

**Scrape images**:

Enter a search query (e.g., "restaurant menu") and the number of images to scrape.
Click "Submit" to start the scraping process.
View images:

Scraped images will be displayed on the result page.
Apply OCR:

Click the "Apply OCR" button to extract text from the images.
The extracted items and prices will be displayed and stored in the database.
View OCR results:

Go to the OCR results page to view the extracted items and prices.
Cleaning Up
To delete the scraped images:

    ```bash
    curl -X POST http://0.0.0.0:8000/delete_images
    ```

**Project Structure**:  

    ```bash 
        
        .
        ├── app.py                # Main application file with routes and functions
        ├── templates/            # HTML templates for the web interface
        │   ├── index.html
        │   ├── result.html
        │   ├── result_with_ocr.html
        ├── static/               # Directory for static files like scraped images
        │   ├── scrappedimgs/
        ├── scrapper.log          # Log file for scraping activities
        ├── mydb.db               # SQLite database file
        ├── requirements.txt      # List of required Python packages
        ├── README.md             # Project documentation
    ```
**Regular Expressions for OCR Extraction**:

The code uses the following regular expression to extract menu items and prices:

    ```bash
        pattern = re.compile(r'([a-zA-Z\s\./|:]+)\s*(\d+(?:[\.,]\d+)?(?:/-)?)')
    ```
Item Names: Consist of alphabetic characters, spaces, dots, slashes, pipes, or colons.
Prices: Numeric values that may include commas, periods, or dashes.


## Acknowledgements
- Flask
- Tesseract OCR
- Selenium
- OpenCV
- Pillow