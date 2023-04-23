import requests
from math import ceil
from bs4 import BeautifulSoup
#from selenium import webdriver
import pandas as pd
import re


termo = input()
url='https://search.scielo.org/?q=blockchain&lang=pt&count=15&from=1&output=site&sort=&format=summary&fb=&page=1'
req=requests.get(url)
content=req.text

soup=BeautifulSoup(content, "html.parser")
#soup2=BeautifulSoup(req.content, "html.parser")
#stuff = soup.prettify()

hits = soup.find(attrs={'id':'TotalHits'})
total_articles = int(hits.text)
#total_articles = 70
page_count=ceil(total_articles/15)
	
index_from = url.find('from=') + 1 	# a pagina tem um campo from relacionado a contagem de artigos		
index_page = url.find('page=') + 5 	# que precisa ser modificado na url, assim como a pagina em si
page_from = 1
current_page = 1

urls_trabalhos=[]
autores=[]
referencias=[]
titles=[]

for page in range(page_count):
	#if (url[index_from] == '0'): print(0) 
	#if (url[index_from] == '1' and url[index_from+1] == '&'): print('gg')

	for a_href in soup.findAll(attrs={'class':'articleAction shareFacebook'}):	#pega a url do trabalho
		link=a_href["href"]
		urls_trabalhos.append(link)

	page_from += 15
	current_page += 1
	url2 = url[:index_from] + str(page_from) + url[index_from + 2:]		#altera a string da url, colocando o from
	url2 = url2[:index_page] + str(current_page) + url2[index_page + 2:]
	
	req=requests.get(url2)
	content=req.text
	soup=BeautifulSoup(content, "html.parser")
try:
	for i in range(len(urls_trabalhos)):
		req=requests.get(urls_trabalhos[i]) 	#pega o trabalho em si
		content=req.text
		soup=BeautifulSoup(content, "html.parser")

		title=soup.find(attrs={'class':'title'})	#pega titulo
		titles.append(title)
		print(title)
		aut=''
		for a in soup.findAll('span',attrs={'class':'author-name'}):
			aut = aut + a.text + ', '	#como um trabalho pode ter mais de um autor e necessario combinar em uma string so
		autores.append(aut)

		"""
		for r in soup.findAll('p',attrs={'class':'ref'}):
			p=r.text
			y=p.replace("[", '')
			y=y.replace("]", '')
			y=y.replace("Links", '')
			y=y.replace("\n", '')
			#print(y)	#como um trabalho pode ter mais de um autor e necessario combinar em uma string so
		"""
		for r in soup.findAll('p',attrs={'class':'ref'}):
			match=r 	#tem a href inuteis, logo faz um for para cada a href, que
						#o decompose remove
			for match in r:
				r.a.decompose()
			y=r.text
			y=y.replace("[", '')
			y=y.replace("]", '')
			y=y.replace("\n", '')
			
			referencias.append(y)
except BaseException as e:
	print('Failed to do something: ' + str(e))

