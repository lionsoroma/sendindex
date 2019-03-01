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
from selenium.common.exceptions import WebDriverException
from itertools import zip_longest


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
    errors_status = []
    base_path = os.path.dirname(os.path.abspath(__file__))
    filename_path = os.path.join(base_path, filename)
    if os.path.exists(filename_path):
        if os.stat(filename_path).st_size > 0:
            with codecs.open(filename_path, mode='r', encoding='utf-8') as data_index_file:
                for data_index in data_index_file:
                    words = data_index.split(' ')
                    key_words = list(filter(None, words[::2]))
                    value_words = list(filter(None, words[1::2]))
                    quantity_keys = len(key_words)
                    quantity_values = len(value_words)
                    index_of_counter = dict(zip_longest(key_words, value_words, fillvalue=None))
                    if quantity_keys == quantity_values:
                        return errors_status, index_of_counter
                    else:
                        errors_status.append("Невірна кількість записів 'ключ:значення' у файлі: " + filename + " !")
                        errors_status.append("Ключів: " + str(quantity_keys) + " ,значень: " + str(quantity_values))
                        errors_status.append(data_index)
                        return errors_status, index_of_counter
        else:
            errors_status.append("Файл '" + filename + "' пустий!")
            return errors_status, index_of_counter
    else:
        errors_status.append("Помилка: файл '" + filename + "' не знайдено!")
        return errors_status, index_of_counter


def send_email(event_stack):
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
    msg = MIMEText('\n'.join(event_stack), 'plain', 'utf-8')
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
    no_errors = False
    event_stack = []
    if len(indexes) == 0:
        pass
    else:
        try:
            driver = webdriver.Chrome()
            event_stack.append('WebDriver ініціалізовано успішно!')
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
                            int_value = reading.get_attribute('value')
                            event_stack.append('Показник: ' + int_value + ' м.куб/кВт*год. для ' + meter_id_lit(temp) +
                                               '(номер лічильника: ' + temp + ') введений успішно!')
                        except WebDriverException as e:
                            reload(sys)
                            event_stack.append('Виникла помилка при введені даних для ' + meter_id_lit(temp) +
                                               '(номер лічильника: ' + temp + '): ' + e.msg)
                        else:
                            no_errors = True
            if no_errors:
                try:
                    button_first = driver.find_element_by_xpath("//button[@id='set_meter_readings']")
                    driver.execute_script("arguments[0].click();", button_first)
                    event_stack.append("Кнопка 'передати показники' натиснута успішно! ")
                except WebDriverException as e:
                    event_stack.append("При натисканні кнопки 'передати показники' виникла помилка: " + e.msg)
                else:
                    try:
                        driver.find_element_by_xpath("//button[@id='confirm_yes_button']").click()
                        event_stack.append("Кнопка підтвердження натиснута успішно! ")
                    except WebDriverException as e:
                        reload(sys)
                        event_stack.append("При натисканні кнопки підтвердження виникла помилка: " + e.msg)
                    else:
                        reload(sys)
            driver.close()
            if no_errors:
                event_stack.append('Всі дані передано успішно!')
        except WebDriverException as e:
            event_stack.append('Помилка при ініціалізації WebDriver (дані не передано!): ' + e.msg)
        event_stack.append(private_link)
        return event_stack


def get_private_link():
    load_dotenv()
    return os.environ.get('PRIVATE_LINK')


def main():
    errors, indexes = get_data_index(get_filename())
    if indexes and not errors:
        event_stack = set_data_indexes(indexes, get_private_link())
        send_email(event_stack)
    else:
        send_email(errors)


if __name__ == '__main__':
    main()








