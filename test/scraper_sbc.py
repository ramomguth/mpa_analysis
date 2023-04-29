import difflib as dl
import re
import time
from dataclasses import dataclass

#from selenium import webdriver
import pandas as pd
import requests
#import teste
from bs4 import BeautifulSoup
from neo4j import GraphDatabase


@dataclass
class work:
    title: str
    authors: [] 		#type: ignore
    references: []		#type: ignore
    ref_properties: []	#type: ignore
    num_ref: int


#Variaveis globais
'''
urls=[]
titles=[]
references=[]
authors=[]
trabalhos=[]
simil=[]
ref_id=0
num_trabalhos = 0
ano=0

def batata():
    print("batata")
    
def string_similarity(str1, str2):
    result =  dl.SequenceMatcher(a=str1.lower(), b=str2.lower())
    return result.ratio()


def read_work(name):
	df=pd.read_csv(name,sep='|')

	t=df['Titulo'].tolist()
	a=df['Autores'].tolist()
	r=df['Referencias'].to_dict()
	rp=df['Properties'].tolist()
	rn=df['Num_ref'].tolist()

	num_trabalhos = len(t)
	pattern = '\|(.*?)\|'

	for i in range(num_trabalhos):
		aut_list = re.findall(pattern, a[i])
		
		ref_list = re.findall(pattern, r[i]) 

		ref_prop = re.findall(pattern, rp[i]) 
		for k in range(len(ref_prop)):
			ref_prop[k] = eval(ref_prop[k])

		w = work(t[i],aut_list,ref_list,ref_prop,rn[i])
		trabalhos.append(w)
	
def check_last_ref_id(name):
	df=pd.read_csv(name,sep='|')

	num=df['Titulo'].tolist()
	num_trabalhos = len(num)
	global ref_id 
	ref_id = num_trabalhos - 1

def save_work(name):
	a=[]
	t=[]
	r=[]
	rp=[]
	nr=[]
	num_trabalhos = len(trabalhos)
	for i in range(num_trabalhos):
		a.append(trabalhos[i].authors)
		t.append(trabalhos[i].title)
		r.append(trabalhos[i].references)
		rp.append(trabalhos[i].ref_properties)
		nr.append(trabalhos[i].num_ref)

	for i in range(len(a)):
		for k in range(len(a[i])):
			a[i][k] = '|' + a[i][k] + '|'

	for i in range(len(r)):
		for k in range(len(r[i])):
			r[i][k] = '|' + r[i][k] + '|'

	for i in range(len(rp)):
		for k in range(len(rp[i])):
			rp[i][k] = '|' + str(rp[i][k]) + '|'

	df = pd.DataFrame({'Titulo':t, 'Autores':a, 'Referencias':r, 'Properties':rp, 'Num_ref':nr}) 
	df.to_csv(name, index=False, encoding='utf-8', sep='|')

def append_work(name):
	a=[]
	t=[]
	r=[]
	rp=[]
	nr=[]
	num_trabalhos = len(trabalhos)
	for i in range(num_trabalhos):
		a.append(trabalhos[i].authors)
		t.append(trabalhos[i].title)
		r.append(trabalhos[i].references)
		rp.append(trabalhos[i].ref_properties)
		nr.append(trabalhos[i].num_ref)

	for i in range(len(a)):
		for k in range(len(a[i])):
			a[i][k] = '|' + a[i][k] + '|'

	for i in range(len(r)):
		for k in range(len(r[i])):
			r[i][k] = '|' + r[i][k] + '|'

	for i in range(len(rp)):
		for k in range(len(rp[i])):
			rp[i][k] = '|' + str(rp[i][k]) + '|'

	df = pd.DataFrame({'Titulo':t, 'Autores':a, 'Referencias':r, 'Properties':rp, 'Num_ref':nr}) 
	df.to_csv(name, mode='a', index=False, header=False, sep='|')

'''
def scrape_sbc_event(url):
	urls = []

	try:
		response = requests.head(url)
	except requests.exceptions.RequestException as e:
		return ("invalid_url")
	
	req=requests.get(url)
	content=req.text
	soup=BeautifulSoup(content, "html.parser")
	try:
		for elem in soup.findAll(attrs={'class':'title'}):	#pega a url do trabalho
			ll=elem.find('a')
			urls.append(ll['href'])		
	except: pass
	#return urls

	ref_id = 0
	next_ref = ref_id * 1000 
	references=[]
	authors=[]
	for element in urls: #range(len(urls))
		req=requests.get(element)
		content=req.text
		soup=BeautifulSoup(content, "html.parser")

		names = soup.findAll(attrs={'class':'name'}) #pega os autores ou instituicao
		for span in names:
			authors.append(span.text)

		#ref = soup.findAll(attrs={'class':'item references'}) #pega os autores ou instituicao
		#for i in ref:
		#	references.append(i.text)
		h=soup.findAll('h3')		#remove h3 inutil
		for match in h:
			match.decompose()

		ref = soup.findAll(attrs={'class':'item references'}) #pega as referencias e limpa elas
		for k in ref:
			r = re.sub('\t','',k.text)
			r = re.sub('\n','',r)
			#r = re.sub('\r','',r)
			s=r.split('\r')
			ref_id += 1
			next_ref = 1000 * ref_id
			for j in range(len(s)): 			#as referencias le tudo como uma so, precisa separar
				references.append(s[j])
				num_ref += 1
				#print (num_ref)		
				#rf = 'ref_id=' + ref_id + 'status=' + 0
				#ref_properties.append((ref_id,0,0,ano))

			#w = work(title2, authors, references, ref_properties, num_ref)
			#trabalhos.append(w)
		#print(references[0])
		num_ref = next_ref
	return references
'''
def save_stuff(authors, references):
	for i in authors:
		
		title = re.sub('\"', '', title)
		title = re.sub('\'', '', title)
		#num_ref=str(trabalhos[i].num_ref)
		q=f"""CREATE (:Trabalho {{title:'{title}', num_ref:'{num_ref}', id:'{i+1}'}})"""
	
	

	for j in range(int(num_ref)):
		ref_title = trabalhos[i].references[j]
		ref_title = re.sub('\"', '', ref_title)
		ref_title = re.sub('\'', '', ref_title)
		ref_id = trabalhos[i].ref_properties[j][0]

		q2=f"""CREATE (:Reference {{title:'{ref_title}', ref_id:'{ref_id}'}})"""
		result=add_work(driver,q2)

		q2 = f"""MATCH (t:Trabalho {{title:'{title}'}}), (r:Reference{{ref_id:'{ref_id}'}}) CREATE (t)-[a:Referencia]->(r)"""
		result=add_work(driver,q2)

		#q3 = f"""MATCH (t:Trabalho {{title:'{title}'}}), (r:Reference{{title:'{ref_title}'}}) CREATE (t)-[a:Referencia]->(r)"""
		#c=conn.query(q2)
		#for row in c: print(row)



def scrape_sbc_event_works(urls):
	#try:
	global ref_id 
	next_ref = ref_id * 1000 
	for i in range(len(urls)): #range(len(urls))
		references=[]
		authors=[]
		num_ref=0
		ref_properties = []
		ref_id = next_ref + 1000 * i

		req=requests.get(urls[i])
		content=req.text
		soup2=BeautifulSoup(content, "html.parser")
		title=soup2.find(attrs={'class':'page_title'})
		title2 = re.sub('\s+',' ',title.text)
			
		spans = soup2.findAll(attrs={'class':'name'}) #pega os autores ou instituicao
		for span in spans:
			at= re.sub('\t','',span.text)
			at= re.sub('\n','',at)
			authors.append(at)


		h=soup2.findAll('h3')		#remove h3 inutil
		for match in h:
			match.decompose()

		ref = soup2.findAll(attrs={'class':'item references'}) #pega as referencias e limpa elas
		for k in ref:
			r = re.sub('\t','',k.text)
			r = re.sub('\n','',r)
			#r = re.sub('\r','',r)
			s=r.split('\r')
			for j in range(len(s)): 			#as referencias le tudo como uma so, precisa separar
				references.append(s[j])
				num_ref+=1
				ref_id+=1
				#rf = 'ref_id=' + ref_id + 'status=' + 0
				ref_properties.append((ref_id,0,0,ano))

			w = work(title2, authors, references, ref_properties, num_ref)
			trabalhos.append(w)	
	#except: pass

	#del trabalhos[0]		#tem coisa inutil na linha 0
	num_trabalhos = len(trabalhos)

def compare_refs():
	st = time.time()
	num_trabalhos = len(trabalhos)
	io=0
	for i in range(num_trabalhos):
		#loop do vetor de trabalhos
		#print('i=',i,'num',trabalhos[i].num_ref)
		for j in range(trabalhos[i].num_ref):

			#loop do vetor de referencias
			for k in range (num_trabalhos):
				
				#e necessario comparar cada referencia com todos
				#os outros trabalhos e suas referencias

				current_work_pos = i
				next_work_pos = k+1
				if (next_work_pos >= num_trabalhos): 
					next_work_pos = num_trabalhos - next_work_pos
				
				# se i=k eh o mesmo trabalho,logo nao precisa comparar
				if (next_work_pos == i): break	
				
				next_work = trabalhos[next_work_pos]
				for w in range( next_work.num_ref ):

					#compara com cada referencia do proximo trabalho
					str1 = trabalhos[i].references[j]  
					str2 = next_work.references[w]
					#print('trabalho=',i,'ref=',j,'comp com trabalho=',next_work_pos,'ref=',w)

					similarity = (string_similarity(str1,str2))
					str1_id = trabalhos[i].ref_properties[j][0]
					str2_id = next_work.ref_properties[w][0]
					#if (similarity>0.75): print(similarity,str1,str2)
					if (similarity>0.75): 
						tup = (similarity,str1_id,str1,str2_id,str2,0)
						simil.append(tup)
					io+=1
	et = time.time()
	print('time=',et-st)
	print('io=',io)
 
				

def create_global_ref_list():
	for i in range(len(trabalhos)):
		for k in range(len(trabalhos[i].references)):
			global references
			references.append(trabalhos[i].references[k])
			#print(i,' ',k, ' ', trabalhos[i].references[k])




url_2016='https://sol.sbc.org.br/index.php/wit/issue/view/509'
url_2017='https://sol.sbc.org.br/index.php/wit/issue/view/211'
url_2019='https://sol.sbc.org.br/index.php/wit/issue/view/402'

while (True):
	inp = input('Action= ')
	print('read | save | new | append | exit')
	if (inp == 'read'): 
		name = input('nome? ')
		read_work(name)
		create_global_ref_list()
		#compare_refs()
		#print(len(simil))
	elif (inp == 'save'):
		inp = input('save name= ')
		save_work(inp)
	elif (inp == 'append'):		#if append -> checar ultima ref_id
		name = input('qual trabalho? ')
		ano = input('qual o ano? ')
		check_last_ref_id(name)
		#url = input('url ')
		urls=[]
		titles=[]
		references=[]
		authors=[]
		trabalhos=[]
		simil=[]
		num_trabalhos = 0

		scrape_event(url_2019)
		scrape_work_urls()
		append_work(name)
	elif (inp == 'new'):
		#url = input('qual a url?')
		url= url_2016
		ano = input('qual o ano? ')
		ano = int(ano)
		name = input('qual o nome? ')
		scrape_event(url)
		scrape_work_urls()
		save_work(name)
	elif (inp == 'exit'):
		break


read_work('ok.csv')
#compare_refs()
print('simil')
#conn = teste.Neo4jConnection(uri="bolt://localhost:7687", user="batman", pwd="superman")

def stuffi(tx):
    ts = tx.run("match n)-->((Reference) where id(n) = 213 return Reference as rt").value()
    return ts

def add_person(driver):
    with driver.session() as session:
        return session.execute_write(stuffi)

def add_work(driver, query):
    with driver.session() as session:
        return session.run(query)

def add_ref(driver):
    with driver.session() as session:
        return session.execute_write(stuffi)



driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
result=add_person(driver)
print(result[0]['title'])
driver.close()

for i in range(len(trabalhos)):
	title=trabalhos[i].title
	title = re.sub('\"', '', title)
	title = re.sub('\'', '', title)
	num_ref=str(trabalhos[i].num_ref)
	q=f"""CREATE (:Trabalho {{title:'{title}', num_ref:'{num_ref}', id:'{i+1}'}})"""
	
	result=add_work(driver,q)

	for j in range(int(num_ref)):
		ref_title = trabalhos[i].references[j]
		ref_title = re.sub('\"', '', ref_title)
		ref_title = re.sub('\'', '', ref_title)
		ref_id = trabalhos[i].ref_properties[j][0]

		q2=f"""CREATE (:Reference {{title:'{ref_title}', ref_id:'{ref_id}'}})"""
		result=add_work(driver,q2)

		q2 = f"""MATCH (t:Trabalho {{title:'{title}'}}), (r:Reference{{ref_id:'{ref_id}'}}) CREATE (t)-[a:Referencia]->(r)"""
		result=add_work(driver,q2)

		#q3 = f"""MATCH (t:Trabalho {{title:'{title}'}}), (r:Reference{{title:'{ref_title}'}}) CREATE (t)-[a:Referencia]->(r)"""
		#c=conn.query(q2)
		#for row in c: print(row)

driver.close()
'''

