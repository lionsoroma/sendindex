#!/usr/bin/python
# coding: utf-8
# -*- coding: utf-8 -*-
import sys
import os
import smtplib
import configparser
import codecs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from importlib import reload
from email.mime.text import MIMEText
from email.header import Header

no_errors = False


def get_contacts(filename):
    names = []
    emails = []
    with codecs.open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def get_data_index(filename):
    index_of_counter = {}
    base_path = os.path.dirname(os.path.abspath(__file__))
    filename_path = os.path.join(base_path, filename)
    with codecs.open(filename_path, mode='r', encoding='utf-8') as data_index_file:
        for data_index in data_index_file:
            key_words = data_index.split(' ')
            index_of_counter = zip(key_words[::2], key_words[1::2])
    return dict(index_of_counter)


def send_email(body_text):
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "email.ini")
    if os.path.exists(config_path):
        cfg = configparser.RawConfigParser()
        cfg.read(config_path)
    else:
        sys.exit(1)
    contacts_path = os.path.join(base_path, 'mycontacts.txt')
    names, emails = get_contacts(contacts_path)
    host = cfg.get("smtp", "server")
    from_addr = cfg.get("smtp", "from_addr")
    passwords = cfg.get("smtp", "passwords")
    ports = cfg.get("smtp", "ports")
    subject = 'BOT eps.te.ua'
    msg = MIMEText(body_text, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = from_addr
    msg['To'] = ', '.join(emails)
    s = smtplib.SMTP(host, ports)
    s.set_debuglevel(1)
    try:
        s.ehlo()
        s.starttls()
        s.login(from_addr, passwords)
        s.sendmail(msg['From'], ', '.join(emails), msg.as_string())
    finally:
        s.quit()


def get_filename():
    filename = sys.argv[-1]
    return filename


def meter_id_lit(x):
    return {
        '11119837': 'gas',
        '14091149': 'hotwater',
        '415380':   'coldwater1',
        '17189320': 'coldwater2',
        '50510':    'elec'
    }.get(x, 0)


def set_data_indexes(indexes, private_link):
    if len(indexes) == 0:
        pass
    else:
        driver = webdriver.Firefox()
        driver.get(private_link)
        table = driver.find_element_by_xpath("//table[@class='meters-table']")
        rows = table.find_elements_by_tag_name("tr")
        for row in rows:
            col = row.find_elements_by_tag_name("td")
            if len(col) > 0:
                meter_id = col[1].find_element_by_id('meter_id')
                temp = meter_id.get_attribute('value')
                if meter_id_lit(temp) in indexes.keys():
                    try:
                        consumption = str(round(float(indexes[meter_id_lit(temp)])))
                        reading = col[4].find_element_by_id('reading')
                        reading.send_keys(consumption)
                        reading.send_keys(Keys.RETURN)
                        intvalue = reading.get_attribute('value')
                    except Exception:
                        error = sys.exc_info()[0]
                        reload(sys)
                        body_text = 'Виникла помилка при введені даних!'

                        send_email(body_text)
                    else:
                        no_errors = True
        if no_errors:
            try:
                button_first = driver.find_element_by_xpath("//button[@id='set_meter_readings']")
                driver.execute_script("arguments[0].click();", button_first)
            except Exception:
                error = sys.exc_info()[0]
            else:
                try:
                    driver.find_element_by_xpath("//button[@id='confirm_yes_button']").click()
                except Exception:
                    error = sys.exc_info()[0]
                    reload(sys)
                    body_text = 'Виникла помилка при введені даних!'

                    send_email(body_text)
                else:
                    reload(sys)
                    body_text = 'Всі дані передано успішно! ' + private_link

                    send_email(body_text)
        driver.close()


def get_private_link():
    load_dotenv()
    return os.environ.get('PRIVATE_LINK')


def main():
    indexes = get_data_index(get_filename())
    if indexes:
        set_data_indexes(indexes, get_private_link())


if __name__ == '__main__':
    main()







