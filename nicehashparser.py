# -*- coding: utf-8 -*-
"""
This is a simple script file to check nicehash website for their current offering of the hash power
- Parses HTML page
- Extracts necessary values
- Logs data in a file (entries are in JSON format)
- Sends Email in the predifined case

@vykozlov 2017-11-06
"""

import os
import yaml

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import json

debug = False
logfile = 'nicehash.log'
eth_threshold = 145.0 # GH/BTC
ifEmail = False

def emailsend(recipient,subj, text):
	confpath = os.environ.get('HOME') + '/.secretpath/email.yml'
	conf = yaml.load(open(confpath))
	sender = conf['user']['email']
	mypass = conf['user']['password']
	
	# code below based on: https://docs.python.org/2/library/email-examples.html#id5
	msg = MIMEMultipart()
	msg['From'] = sender
	msg['To'] = recipient
	msg['Subject'] = subj

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(text, 'plain')
	#-part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	#-msg.attach(part2)
	
	server = smtplib.SMTP_SSL('smtp.gmail.com',465) #port 465 or 587
	server.ehlo()
	#server.starttls()
	server.login(sender,mypass)
	server.sendmail(sender,recipient,msg.as_string())
	server.close()

import lxml.html as lh
from lxml.etree import tostring
import requests
url = 'https://www.nicehash.com/buy'
page = requests.get(url)
doc = lh.fromstring(page.content)

div_offers = doc.cssselect('div.offers')

#/html/body/div[3]/div/div/div[1]/div[1]/div[1]
#/html/body/div[3]/div/div/div[1]/div[2]/p[2]
for element in div_offers:
	print(tostring(element, pretty_print=True)) if debug else ''
	coin_name=element.xpath('//div[@class="price_header"]/div[@class="title"]/text()')
	coin_hash=element.xpath('//div[@class="price_header"]/div[@class="price"]/text()')
	coin_price=element.xpath('//div[@class="price_body"]/div[@class="price"]/text()')
	coin_price_fiat=element.xpath('//div[@class="price_body"]/p[2]/text()')

if debug:
	print(coin_name)
	print(coin_hash)
	print(coin_price)
	print(coin_price_fiat)

from datetime import datetime
tstamp = str(datetime.now().timestamp())
humantime = str(datetime.now())

message= { '#timestamp' : tstamp,    # '#' symbol is used that these variables appear on top. matter of taste.
		   '#timehuman' : humantime,
		   '#url'       : url }

for idx in range(len(coin_name)):
	hash = coin_hash[idx].split()
	price = coin_price[idx].split()
	for char in "()":
		coin_price_fiat[idx] = coin_price_fiat[idx].replace(char,"")
	price_fiat = coin_price_fiat[idx].split()
	ratio  = float(hash[0])/float(price[0])
	# set email flag to true if the ratio for ethereum is above threshold:
	if ('Ethereum' in coin_name[idx] or 'ethereum' in coin_name[idx] or 'ETH' in coin_name[idx]) and ratio > eth_threshold :
		ifEmail = True
	message.update({coin_name[idx]: [float(hash[0]), float(price[0]), float(price_fiat[0]), ratio]})
	message.update({coin_name[idx] + '_units': [hash[1], price[1], price_fiat[1], hash[1]+"/"+price[1]]})
	
message_txt = json.dumps(message, sort_keys=True, indent=2) + '\n'  #sort alphabetically

with open(logfile, mode='a') as f:
        f.write(message_txt)

emailsend('youremail@domain.com', 'Subject', message_txt) if ifEmail else ''
print(message_txt) if debug else ''

