import requests
import re
import time
import cairosvg
import PyPDF2
import io
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from dotenv import load_dotenv
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

load_dotenv()

#TO DO:
#-Suppress window opening by Selenium
#-Find out why https://musescore.com/user/30382151/scores/6088047 gives an invalid XPath unlike all the others.

score_url = 'https://musescore.com/user/6480061/scores/6212539'
file_dir = os.getenv('DIRECTORY')
alt_str = None
link = None
score_title = None
max_pages = None

driver = webdriver.Edge()
driver.get(score_url)

driver.maximize_window()

html = driver.page_source

page = requests.get(score_url)

soup = BeautifulSoup(html, "html.parser")


#Get the alt tag and link to the src for the first page of the music sheet
for foo in soup.find_all('img', alt=True):
    if ('pages' in foo['alt']):    
        alt_str = foo['alt']
        link = foo['src']
        break


#Gets the title of the song
m = re.search('.+?(?=by)', alt_str)

if m:
    score_title = m.group(0)   



#Gets the max page count
m = re.search('of\s(.+?)\spages', alt_str)
if m:
    max_pages = int(m.group(1))    

#Setup empty pdf for all data
pdf_document = PyPDF2.PdfWriter()

element = driver.find_element(By.ID, "jmuse-scroller-component")

response = requests.get(link)
with open('score_0.svg', 'wb') as f:
    f.write(response.content)

pdf_data=cairosvg.svg2pdf(url='score_0.svg')
pdf_obj = PyPDF2.PdfReader(io.BytesIO(pdf_data))
for page in range(len(pdf_obj.pages)):
        pdf_document.add_page(pdf_obj.pages[page])
os.remove('score_0.svg')

for page in range(2,max_pages+1):

    driver.execute_script(f"arguments[0].scrollTop = {1190*(page-1)}", element)
    alt_str = re.sub(r"(?<=–\s)(\d+)(?=\sof)", str(page), alt_str,count=1) #Look for the current page number

    img_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@class='EEnGW']/img[@alt='{alt_str}']")))

    time.sleep(0.5) #Needed otherwise src won't load in properly

    driver.get(img_elem.get_attribute("src"))

    time.sleep(0.5)#Needed to wait for svg to download fully

    pdf_data=cairosvg.svg2pdf(url=file_dir + f'score_{page-1}.svg')
    pdf_obj = PyPDF2.PdfReader(io.BytesIO(pdf_data))

    for pg in range(len(pdf_obj.pages)):
        pdf_document.add_page(pdf_obj.pages[pg])

    os.remove(file_dir + f'score_{page-1}.svg')

with open(score_title + '.pdf', "wb") as f:
    pdf_document.write(f)

