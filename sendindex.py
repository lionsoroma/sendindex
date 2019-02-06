#!/usr/bin/python
# coding: utf-8
# -*- coding: utf-8 -*-
import argparse
import sys
import os
import smtplib
import ConfigParser
import codecs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display


noErrors = False


def get_contacts(filename):
    names = []
    emails = []
    with codecs.open(filename, mode='r', encoding='utf-8') as contacts_file:
		for a_contact in contacts_file:
			names.append(a_contact.split()[0])
			emails.append(a_contact.split()[1])
	return names, emails
def send_email(body_text):
	emails = []
	names = []
	base_path = os.path.dirname(os.path.abspath(__file__))
	config_path = os.path.join(base_path, "email.ini")
	if os.path.exists(config_path):
		cfg = ConfigParser.RawConfigParser()
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
	s = smtplib.SMTP(host, ports)
	s.starttls()
	s.login(from_addr, passwords)
	BODY = "\r\n".join((
		"From: %s" % from_addr,
		"To: %s" % ', '.join(emails),
		"Subject: %s" % subject,
		"",
		body_text
	))
	s.sendmail(from_addr, emails, BODY)
	s.quit()

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-gas', type=float, help='Вик. газ в м. куб. XXX.XX показник на останнє число міс.')
	parser.add_argument('-hotwater',  type=float, help='Вик. гор. вод. в м. куб. XXX.XX показник на останнє число міс.')
	parser.add_argument('-coldwater1', type=float, help='Вик. хол. вод. 1-ий ліч в м. куб. XXX.XX показник на останнє число міс.')
	parser.add_argument('-coldwater2', type=float, help='Вик. хол. вод. 2-ий ліч в м. куб. XXX.XX показник на останнє число міс.')
	parser.add_argument('-elec', type=float, help='Вик. електроенергія в кВт*год. XXX.XX показник на останнє число міс.')
	return {key: value for key, value in vars(parser.parse_args()).items()
			if value is not None}
args = get_args()

def meter_id_lit(x):
    return {
		'11119837': 'gas',
		'14091149': 'hotwater',
		'415380'  : 'coldwater1',
		'17189320': 'coldwater2',
		'50510'	  : 'elec'
	}.get(x, 0)
if (len(args) == 0):
    pass
else:
    display = Display(visible=0, size=(1024, 768))
	display.start()
	driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
	driver.get("https://www.eps.te.ua/ternopil/account/view/JK5__1wWEhKkhOZoukBRnQ")
	table = driver.find_element_by_xpath("//table[@class='meters-table']")
	rows = table.find_elements_by_tag_name("tr")
	for row in rows:
		col = row.find_elements_by_tag_name("td")
		if len(col) > 0:
			meter_id = col[1].find_element_by_id('meter_id')
			temp = meter_id.get_attribute('value')
			if meter_id_lit(temp) in args:
				try:
					consumption = str(int(round(args[meter_id_lit(temp)])))
					reading = col[4].find_element_by_id('reading')
					reading.send_keys(consumption)
					reading.send_keys(Keys.RETURN)
					intvalue = reading.get_attribute('value')
				except Exception:
					error = sys.exc_info()[0]
					reload(sys)
					sys.setdefaultencoding('utf8')
					body_text = 'Виникла помилка при введені даних!'
					body_text = str(body_text).encode('utf-8')
					send_email(body_text)
				else:
					noErrors = True
	if noErrors == True:
		try:
			buttonFirst = driver.find_element_by_xpath("//button[@id='set_meter_readings']")
			driver.execute_script("arguments[0].click();", buttonFirst)
		except Exception:
			error = sys.exc_info()[0]
		else:
			try:
				buttonFinally = driver.find_element_by_xpath("//button[@id='confirm_yes_button']").click()
			except Exception:
				error = sys.exc_info()[0]
				reload(sys)
				sys.setdefaultencoding('utf8')
				body_text = 'Виникла помилка при введені даних!'
				body_text = str(body_text).encode('utf-8')
				send_email(body_text)
			else:
				reload(sys)
				sys.setdefaultencoding('utf8')
				body_text = 'Всі дані передано успішно!\r\nhttps://www.eps.te.ua/ternopil/account/view/JK5__1wWEhKkhOZoukBRnQ'
				body_text = str(body_text).encode('utf-8')
				send_email(body_text)
	driver.close()
	display.stop()






