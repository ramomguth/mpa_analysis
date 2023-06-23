import difflib as dl
import re
import time
import uuid
from dataclasses import dataclass
import traceback
from itertools import combinations
import itertools
#from selenium import webdriver
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import requests
from concurrent.futures import ThreadPoolExecutor
#import teste
from bs4 import BeautifulSoup
from neo4j import GraphDatabase


@dataclass
class work:
    title: str
    #tipo: str
    references: []		#type: ignore
    #num_ref: int


def scrape_sbc_event(url):
	urls = []

	try:
		response = requests.head(url)
	except requests.exceptions.RequestException as e:
		traceback.print_exc()
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

	#ref_id = 0
	#next_ref = ref_id * 1000 
	trabalhos=[]

	#2 casos
	# 1 que nao tem as refs
	# 2 quanto tem um href no meio da ref

	for i, element in enumerate(urls): #faz o scraping de cada um dos trabalhos e suas referencias
		#element = urls[1]
		#print(i)
		req=requests.get(element)
		content=req.text
		soup=BeautifulSoup(content, "html.parser")

		work_title=soup.find(attrs={'class':'page_title'})
		work_title = re.sub('\s+',' ',work_title.text)
		#print("i=",i,"  ",work_title)

		todas_referencias = soup.find(attrs={'class':'item references'})
		
		if todas_referencias == None:		#se nao tem referencias, pula o trabalho
			#w = work(work_title, [])
			continue
		
		value_div = todas_referencias.find('div', class_='value')
		refs = []
		
		br_tags = value_div.find_all('br')	#as referencias sao separadas por 2 tags <br>, que precisam ser removidas
		i=0
		k= (value_div.get_text())
		#k = re.sub('\n','|',k)
		refe = k.split('\n')
		for i,r in enumerate(refe):
			r = r.replace('\t', '')
			refe[i] = r
			r = re.sub('\r','',r)
			refe[i] = r
			if refe[i] == '': refe.pop(i)

		
		for br_tag in br_tags:
			k= (br_tag.get_text())
			i += 1
			refs.append(k)
			#for a_tag in br_tag.find_all('a'):
			#	a_tag.decompose()
		
		for br_tag in br_tags:		
			if br_tag.previous_sibling:
				ref = br_tag.previous_sibling.get_text()
				ref = re.sub('\n','',ref)
				if ref == '.' or ref == '': continue
				#refs.append(ref)
			
		w = work(work_title, refe)
		trabalhos.append(w)
	return trabalhos	

'''
similarity status: 
	no_similarity_done
	similarity_done
	in_progress
	complete
'''
def save_scraper_data(lista_trabalhos, user_id, project_id):
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	try:
		with driver.session() as session: 
			tx = session.begin_transaction()

			query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) return count (f) as co"
			co = tx.run (query, user_id=user_id, project_id=project_id)
			simil_flag_exists = co.single().value()
			if (simil_flag_exists == 0):
				query = "CREATE (f:simil_flag {status:$status, id:$id, user_id:$user_id, project_id:$project_id})"
				simil_flag_id = str(uuid.uuid4())
				tx.run(query, status='no_similarity_done', id=simil_flag_id, user_id=user_id, project_id=project_id)
			else:
				query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) set f.status = 'no_similarity_done' "
				simil_flag_id = str(uuid.uuid4())
				tx.run(query, id=simil_flag_id, user_id=user_id, project_id=project_id)
			
			for index, element in enumerate(lista_trabalhos):
				#element = lista_trabalhos[0]
				work_title = element.title
				trabalho_ref_list = element.references
				trabalho_num_ref = len(trabalho_ref_list)
				work_id = str(uuid.uuid4())
		
				#q=f"""CREATE (t:trabalho {{title:'{title}', num_ref:'{trabalho_num_ref}', tipo:'primario', id:'{work_id}'}})"""
				query = "CREATE (t:trabalho {title:$title, num_ref:$num_ref, tipo:$tipo, id:$id, user_id:$user_id, project_id:$project_id})"
				tx.run(query,title=work_title, num_ref=trabalho_num_ref, tipo='primario', id=work_id, user_id=user_id, project_id=project_id)
		
				for reference in trabalho_ref_list:
					ref_id = str(uuid.uuid4())
					reference  = reference.replace('\t', '')
					#reference = re.sub('\"', '', reference)
					#reference = re.sub('\'', '', reference)
					query = "CREATE (t:trabalho {title:$title, tipo:$tipo, id:$id, user_id:$user_id, project_id:$project_id})"
					tx.run(query,title=reference, tipo='referencia', id=ref_id, user_id=user_id, project_id=project_id)

					q = f"""MATCH (t:trabalho {{id:'{work_id}'}}), (r:trabalho{{id:'{ref_id}'}}) CREATE (t)-[a:referencia]->(r)"""
					tx.run(q)
			tx.commit()
			return ("ok")
		
	except Exception as e:
		tx.rollback()
		traceback.print_exc()
		return(e)
	
def string_similarity(str1, str2):
    result =  dl.SequenceMatcher(a=str1.lower(), b=str2.lower())
    return result.ratio()

def compare_refs(user_id, project_id):
	q=f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}})-[s:similar_to]->(r:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.id as a_ref_id, t.title as a_title, r.id as b_ref, r.title as b_title, s.value as similarity order by t.title""" 
	#print (q)
	#trabalhos = lista_trabalhos
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	try:
		with driver.session() as session: 
			q = f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.title as title, t.tipo as tipo, t.id as id"""
			result = session.run(q)
			lista_trabalhos = []
			for record in result:
				lista_trabalhos.append(record.values())

	except Exception as e:
		traceback.print_exc()
		return(e)
	
	simil = []
	strings_dict = {}

	st = time.time()
	for lst in lista_trabalhos:
		#strings_dict[lst[0]] = {'tipo': lst[1], 'id': lst[2]}
		strings_dict[lst[0]] = (lst[1], lst[2])
		#salva as informacoes pertinentes a cada referencia
	
	for str1, str2 in combinations(strings_dict.keys(), 2):
		similarity = (string_similarity(str1,str2))
		similarity = round(similarity,3)
		if similarity > 0.7:
			#print(similarity, str1,"|||", str2)
			#print(f"Add info for str1: {strings_dict[str1]}")
			#print(f"Add info for str2: {strings_dict[str2]}")
			tup = (similarity, strings_dict[str1], strings_dict[str2])
			simil.append(tup)
	et = time.time()
	#print ("time = ", et - st)

	try:
		#salva as similaridades
		with driver.session() as session: 
			for index, element in enumerate(simil):
				first_work = element[1][1]
				second_work = element[2][1]
				similarity = element[0]
				#print (element[1][1], element[2][1])
				q = f"""MATCH (t:trabalho {{id:'{first_work}'}}), (r:trabalho{{id:'{second_work}'}}) CREATE (t)-[s:similar_to{{value:'{similarity}'}}]->(r) return s"""
				result = session.run(q)
			
			q= f"""MATCH (f:simil_flag {{user_id:'{user_id}', project_id:'{project_id}'}}) set f.status = 'similarity_done' """
			result = session.run(q)

	except Exception as e:
		traceback.print_exc()
		return(e)


def return_simil(user_id, project_id):
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	with driver.session() as session: 
		q = f"""MATCH (f:simil_flag {{user_id:'{user_id}', project_id:'{project_id}'}}) return f.status"""
		result = session.run(q).single().value()
		if result == 'no_similarity_done': 
			compare_refs(user_id, project_id)

		q=f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}})-[s:similar_to]->(r:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.id as a_ref_id, t.title as a_title, r.id as b_ref, r.title as b_title, s.value as similarity order by t.title""" 
		result = session.run(q)
		ref_list=[]
		for record in result:
			#val1.append(record['a_ref_id'])
			ref_list.append(record.values())  
			    
		for index,element in enumerate(ref_list):
			simil = round(float(element[4]),3)
			ref_list[index][4] = simil
		
		"""strings_dict = {}
		copy = []
		for index,lst in enumerate(ref_list):
			#strings_dict[lst[0]] = {'tipo': lst[1], 'id': lst[2]}
			strings_dict[index] = (lst[1], lst[3])
			stry = (lst[1], lst[3])
			copy.append(stry)
			#salva as informacoes pertinentes a cada referencia
		flat_list = list(itertools.chain.from_iterable(copy))
		#for index, elem in enumerate(flat_list):
			#print( index, elem)
		i=0
		aggregate_list = []
		for str1, str2 in combinations(flat_list, 2):
			i+=1
			similarity = (string_similarity(str1,str2))
			similarity = round(similarity,3)
			if similarity > 0.7:
				#print("i= ",i, "/", similarity, str1,"|||", str2)
				stry = (similarity,str1,str2)
				aggregate_list.append(stry)
		

		similarity_matrix = np.zeros((len(flat_list), len(flat_list)))

		for i in range(len(flat_list)):
			for j in range(len(flat_list)):
				similarity_matrix[i, j] = string_similarity(flat_list[i], flat_list[j])

		# perform hierarchical clustering
		clustering_model = AgglomerativeClustering(affinity='precomputed', linkage='average', distance_threshold=0.3, n_clusters=None)
		clustering_model = clustering_model.fit(1 - similarity_matrix)

		grouped_list = [[] for _ in range(clustering_model.n_clusters_)]

		for idx, label in enumerate(clustering_model.labels_):
			grouped_list[label].append(flat_list[idx])"""
		
		
		return ref_list
	

	
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
'''
	try:
		with driver.session() as session: 
			q = f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.title as title, t.tipo as tipo, id(t) as id"""
			result = session.run(q)
			lista_trabalhos = []
			for record in result:
				lista_trabalhos.append(record.values())

			query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) set f.status = $status"
			result = session.run(query, status='gordo', user_id=user_id, project_id=project_id)
			

	except Exception as e:
		traceback.print_exc()
		return(e)'''
	
"""
	simil = []
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
	print('io=',io)"""


"""for k in ref:
			r = re.sub('\t','',k.text)
			r = re.sub('\n','',r)
			#r = re.sub('\r','',r)
			s=r.split('\r')
			#ref_id += 1
			#next_ref = 1000 * ref_id
			lista_refs_do_trabalho = []
			for j in range(len(s)): 			#as referencias le tudo como uma so, precisa separar
				lista_refs_do_trabalho.append(s[j])
				#trabalhos.append(s[j])
				#print (num_ref)		
				#rf = 'ref_id=' + ref_id + 'status=' + 0
				#ref_properties.append((ref_id,0,0,ano))

			w = work(work_title, lista_refs_do_trabalho)
			
		trabalhos.append(w)"""
	#num_ref = next_ref
	#print(trabalhos[0].references[0])

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

