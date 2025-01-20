from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from emoji import replace_emoji
from utils import round_to_nearest_5,get_lat_long
import re
import os 
import sys 

sys.path.insert (0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



def utmb_extract_page(url):
    print("Extracting data from...",url)
    options = webdriver.ChromeOptions()
    remote_webdriver = 'remote_chromedriver'
    options.headless = True
    options.page_load_strategy = 'normal'
    #driver = webdriver.Chrome(options=options)
    driver = webdriver.Remote(f'{remote_webdriver}:4444/wd/hub', options=options) 
    driver.get(url)
    
    # Wait for dynamic content to load
    wait = WebDriverWait(driver, timeout=2000)
    wait2 = WebDriverWait(driver, timeout=2000)
    #wait.until(EC.presence_of_element_located((By.CLASS_NAME,"grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4")))
    
    page_source = driver.page_source
    driver.quit()
    return page_source
    
def utmb_extract_data(html):
    soup = BeautifulSoup(html,'html5lib')
    events = soup.find_all("a",{'class':"style_EventPreview__kWm7L group no-link-underline"})
    
    return events


def utmb_transform_data(data):
    data_cleaned = []
    for i in range(0,len(data)):

        row = data[i]
        values= {
            "name": row.find("div",{"class":"typo-h4 leading-tight mb-1"}).text,
            "distances":row.find('div',{'class':'styles_Distances__GLSe1'}).text,
            "date":row.find('div',{'class':'flex flex-row items-center style_Date__UbJPv py-1'}).text,
            "date_confirmed":True if row.find('span',{'class':'styles_Chip__5DJ6w styles_Confirmed__talWF'}) else False,
            'country': row.find("div",{"class":"style_City__mrIOD"}).find("img").get("title"),
            'city': row.find('div',{'class':'style_City__mrIOD'}).text,
            "styles":row.find('div',{'class':'style_Tags__1wVj6 nice-scrollbar'}).text,
            "disipline":row.find('div',{'class':'style_Disciplines__KoinH'}).text,
            "image":row.find("img").get("src") if row.find("img") else "NO IMAGE",
            "link":"https://www.finishers.com" + row.get("href")
        }
        data_cleaned.append(values)
    return data_cleaned

def utmb_clean_data(data):
    data = pd.DataFrame(data)
    #remove  "by UTMB®" in name 
    data.loc[:,"name"] = data["name"].str.replace("by UTMB®","")
    
    #in distances remove "km" and split by " " and make dummies
    data['distances']= data["distances"].str.replace("km","").str.strip().str.split("\xa0")
    unique_distances =data['distances'].explode().astype(float).apply(round_to_nearest_5).unique()
    data['distances'] = data['distances'].apply(lambda d: [round_to_nearest_5(x) for x in d])
    #print(unique_distances)
    for dist in sorted(unique_distances):
        data['distance_'+ str(dist)] = data['distances'].apply(lambda x: float(dist) in x)


    #in date remove "Date confirmed" and split by into year, month, day and duration (days)
    data['date'] = data['date'].str.replace("Date confirmed","").str.strip()
    ## To finish 

    #in styles remove emojis, +X and create dummies split by emoji (?)
    data['styles'] = data['styles'].apply(lambda d:re.sub(r"\+\d+",'',d)).str.strip()
    data['styles'] = data['styles'].str.replace("®","")
    data['styles'] = data['styles'].apply(lambda d: replace_emoji(d,replace='\xa0')).str.replace(" ",'').str.strip().str.split("\xa0")
    styles_unique = data['styles'].explode().unique()
    for style in sorted(styles_unique):
        data['style_'+str(style)] = data['styles'].apply(lambda x: style in x)
    
    # in disipline create dummies split on +X
    data['disipline'] = data['disipline'].apply(lambda d:re.sub(r"\+\d+",'\xa0',d)).str.strip().str.split("\xa0")
    disipline_unique = data['disipline'].explode().unique()
    for disip in sorted(disipline_unique):
        data['disipline_'+str(disip)] = data['disipline'].apply(lambda x: disip in x)

    #for each city find lat and long
    data[['latitude','longitude']] = data['city'].apply(lambda x: pd.Series(get_lat_long(x)))


    # drop the columns 
    data.drop(columns=['distances','styles','disipline'],axis=1,inplace=True)

    return data 



    



if __name__ == "__main__":
    data_complete = []
    for p in range(1,4): #there are 3 pages with races
        page = utmb_extract_page(f"https://www.finishers.com/en/events?page={p}&tags=utmbevent")
        data = utmb_extract_data(page)
        data_complete.extend(data)
    print(len(data_complete))
    data_cleaned = utmb_transform_data(data_complete)
    print(data_cleaned)
    #df.to_csv("data/utmb_data.csv",index=False)'''
    #df = pd.read_csv("data/utmb_data.csv",)
    data = utmb_clean_data(data_cleaned)
    data.to_csv("data/utmb_data_clean.csv",index=False)


    
