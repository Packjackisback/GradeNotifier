import os
import json
import difflib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from parse_grades import parse_grades
from dotenv import load_dotenv
import contiguity
import requests
#TODO Explain each import for future me


load_dotenv()

def fetch_grades(username, password):
    firefox_path = os.path.expanduser('/usr/bin/firefox')
    geckodriver_path = os.path.expanduser('./geckodriver')
    options = FirefoxOptions()
    options.binary_location = firefox_path
    options.add_argument("--headless")
    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)

    print("[LOG] Firefox Driver loaded")
    try:
        driver.get('https://homeaccess.katyisd.org/HomeAccess/Account/LogOn?ReturnUrl=%2fHomeAccess%2f')
        driver.find_element(By.ID, 'LogOnDetails_UserName').send_keys(username)
        driver.find_element(By.ID, 'LogOnDetails_Password').send_keys(password)
        driver.find_element(By.ID, 'login').click()
        print("[LOG] Logon page loaded")
        driver.get('https://homeaccess.katyisd.org/HomeAccess/Content/Student/Assignments.aspx')
        grades_html = driver.page_source
        print("[LOG] Grades Fetched")
    finally:
        driver.quit()
    return grades_html

def save_grades_to_file(grades):
    with open('grades.json', 'w') as f:
        json.dump(grades, f, indent=4)

def load_grades_from_file():
    if os.path.exists('grades.json'):
        with open('grades.json', 'r') as f:
            return json.load(f)
    return []

def detect_changes(prev_grades, current_grades):
    prev_grades_dict = {item['assignment']: item for item in prev_grades}
    current_grades_dict = {item['assignment']: item for item in current_grades}
    added = [item for key, item in current_grades_dict.items() if key not in prev_grades_dict]
    removed = [item for key, item in prev_grades_dict.items() if key not in current_grades_dict]
    changed = []
    for key, current_item in current_grades_dict.items():
        if key in prev_grades_dict and current_item != prev_grades_dict[key]:
            changed.append(current_item)
    print("[LOG] Grades Changed")
    return added, removed, changed

def format_changes(added, removed, changed):
    formatted_changes = []
    for item in added:
        formatted_changes.append(f"New {item['category']} Grade Assignment in class {item['assignment']}: {item['assignment']} {item.get('score', 'No grade yet')}")
    for item in changed:
        formatted_changes.append(f"Updated {item['category']} Grade Assignment in class {item['assignment']}: {item['assignment']} {item.get('score', 'No grade yet')}")
    print("[LOG] Formatted Changes")
    return formatted_changes

def send_message(string):
        if(len(string)!=0):
            print("[LOG] Sending message: " + string) 
            api_key = os.getenv('CONTIGUITY_KEY')
            if api_key:
                phone = contiguity.login(api_key)
                number = os.getenv('PHONE_NUMBER')
                if number:
                    try:
                        phone.send.text(number, string)
                        print("[LOG] Text sent successfully")
                    except:
                        print("[Error] Text probably not sent")
                else:
                    print("[Warning] Environment variable PHONE_NUMBER not set")
            else:
                print("[Warning] Environment variable CONTIGUITY_KEY not set")
            webhook_url = os.getenv('WEBHOOK')
            if webhook_url:
                try:
                    name = os.getenv('NAME')
                    string = (f"📢 New Grade for {name} 📢\n\n" if name else "") + string

                    response = requests.post(webhook_url, json={"content": string})
                    if response.status_code == 200 or response.status_code == 204:
                        print("[LOG] Webhook message sent successfully.")
                    else:
                        print(f"[Error] Failed to send webhook message. Status code: {response.status_code}")
                except Exception as e:
                    print(f"[Error] Exception occurred while sending webhook: {e}")
            else:
                print("[Warning] WEBHOOK environment variable not set.")

if __name__ == "__main__":
    username = os.getenv('GRADES_USERNAME')
    password = os.getenv('GRADES_PASSWORD')
    if not username or not password:
        print("[Error] Environment variables for username and/or password are not set.")
        exit(1)
    else:
        print("[LOG] Keys loaded")
    previous_grades = load_grades_from_file()
    grades_html = fetch_grades(username, password)
    parsed_grades = parse_grades(grades_html)
    added, removed, changed = detect_changes(previous_grades, parsed_grades)
    changes = format_changes(added, removed, changed)
    changelog = ""
    for change in changes:
        changelog +=  (change + "\n")
    print(changelog)
    send_message(changelog)
    save_grades_to_file(parsed_grades)

    
