import difflib as dl
import textdistance as td
import re
import time
import uuid
from dataclasses import dataclass
import traceback
from itertools import combinations
from collections import defaultdict
#import itertools
#import pandas as pd
#import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor
#import teste
from bs4 import BeautifulSoup
from neo4j import GraphDatabase


@dataclass
class work:
    title: str
    references: []		#type: ignore

def read_csv(data, user_id, project_id):
    lenght = len(data)
    tudo = []
    refs = []
    
    i = 0
    while i < lenght:
        row = 1
        k = i+1
        while (row != ''):
            if (k >= lenght): 
                break
            row = data[k][0] 
            if (row == ''):
                continue
            refs.append(row)
            k += 1
        
        principal = data[i][0]
        k += 1
        i = k
        w = work(principal,refs)
        tudo.append(w)
        refs = []

    status = save_scraper_data(tudo, user_id, project_id)
    if status == 'ok':
        return status
	

def scrape_sbc_event(url, user_id, project_id):
	urls = []

	try:
		response = requests.head(url)
	except requests.exceptions.RequestException as e:
		return ("invalid_url")
	
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	try:
		with driver.session() as session: 
			tx = session.begin_transaction()
			query = "MATCH (u:user_url {url:$url, user_id:$user_id, project_id:$project_id}) return count (u) as co"
			co = tx.run (query, url=url, user_id=user_id, project_id=project_id)
			url_already_used = co.single().value()
			#print (url_already_used)
			if (url_already_used != 0):
				return ("url_already_used")
			else:
				query = "CREATE (u:user_url {url:$url, user_id:$user_id, project_id:$project_id})"
				tx.run(query, url=url, user_id=user_id, project_id=project_id)
				tx.commit()
	except Exception as e:
		traceback.print_exc()
		return ("error")
	req=requests.get(url)
	content=req.text
	soup=BeautifulSoup(content, "html.parser")
	try:
		for elem in soup.findAll(attrs={'class':'title'}):	#pega a url do trabalho
			link=elem.find('a')
			urls.append(link['href'])		
	except: pass
	#return urls

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

		'''
		no corpo da página não tem o titulo em forma de citação, mas felizmente existe um campo chamado ApaCitationPlugin
		com o link da citação do trabalho , onde ele retorna exclusivamente a citação do mesmo
		'''
		sbc_id = soup.find(attrs={'class':'ApaCitationPlugin'})
		work_citation_url = sbc_id.a['href']
		#print("i = ",i, "id= ",sbc_id)
					
		work_citation_req = requests.get(work_citation_url)
		work_soup = BeautifulSoup(work_citation_req.text, 'html.parser')

		# 'get_text' function will extract all the text without tags
		work_citation = work_soup.get_text(separator=' ')

		# Remove any additional white space
		work_citation = ' '.join(work_citation.split())
		#print("i = ",i, " ", work_citation)

		work_title = work_citation
		
		todas_referencias = soup.find(attrs={'class':'item references'})
		
		if todas_referencias == None:		#se nao tem referencias, pula o trabalho
			#w = work(work_title, [])
			w = work(work_title, [])
			trabalhos.append(w)
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
	nothing_done
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

					q = f"""MATCH (t:trabalho {{id:'{work_id}'}}) MATCH (r:trabalho{{id:'{ref_id}'}}) CREATE (t)-[a:referencia]->(r)"""
					tx.run(q)
			tx.commit()
			return ("ok")
		
	except Exception as e:
		tx.rollback()
		traceback.print_exc()
		return(e)
	
def string_similarity(str1, str2):
    #result =  dl.SequenceMatcher(a=str1.lower(), b=str2.lower())
	s = td.damerau_levenshtein.normalized_similarity(str1.lower(), str2.lower())
	return s

def compare_refs(user_id, project_id):
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	try:
		with driver.session() as session: 
			'''
			caso o usuario inclua um novo evento na base, eh necessario recomecar
			todo o trabalho de similaridade, portanto e deletado os relacionamentos anteriores
			'''
			q = f"""MATCH (t:trabalho{{user_id:'{user_id}', project_id:'{project_id}'}}) 
					WITH t.title AS title, COLLECT(t) AS nodes 
					WHERE SIZE(nodes) > 1 
					UNWIND nodes AS node
					RETURN node.title AS title, node.tipo AS tipo, node.id AS id;"""
			result = session.run(q)
			repeated_titles = []
			for record in result:
				repeated_titles.append(record.values())

			q = f"""MATCH ({{user_id:'{user_id}', project_id:'{project_id}'}})-[s:similar_to]->({{user_id:'{user_id}', project_id:'{project_id}'}}) DELETE s"""
			result = session.run(q)

			#update da flag
			q= f"""MATCH (f:simil_flag {{user_id:'{user_id}', project_id:'{project_id}'}}) set f.status = 'similarity_done' """
			result = session.run(q)

	except Exception as e:
		traceback.print_exc()
		return(e)
	
	title_dict = defaultdict(list)
	for item in repeated_titles:		#cria um dicionario com os trabalhos que tem o mesmo titulo
		title, tipo, id = item
		title_dict[title].append((title, tipo, id))

	# Get the values where there are duplicates
	#todo esse processo é necessário pois o processo de combinações não trata os casos onde 2 publicações tem exatamente o mesmo titulo,
	#pois tem o mesmo titulo mas ids diferentes
	duplicates = [values for key, values in title_dict.items() if len(values) > 1]

	simil = []
	with driver.session() as session: 
		for entry in duplicates:
			main_ref = entry[0][2]
			for i in range(1, len(entry)):
				to_alter = entry[i][2]
				
				query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id"
				id_work_to_alter = session.run(query, ref_id=to_alter, user_id=user_id, project_id=project_id)
				id_work_to_alter = id_work_to_alter.single().value()
				#print("para alterar", id_work_to_alter)

				#3 deletar a ref antiga propriamente com seus relacionamentos
				query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
				result1 = session.run(query, ref_id=to_alter, user_id=user_id, project_id=project_id)
				#print("deletado", to_alter)

				#4 criar o novo relacionamento de referencia
				query = "MATCH (t:trabalho{id:$id_work_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
				result2 = session.run(query, id_work_to_alter=id_work_to_alter, main_ref=main_ref, user_id=user_id, project_id=project_id)
				#print(id_work_to_alter, "referencia", main_ref)

		
		q = f"""MATCH (t:trabalho{{user_id:'{user_id}', project_id:'{project_id}'}}) return t.title as title, t.tipo as tipo, t.id as id"""
		result = session.run(q)
		lista_trabalhos = []
		for record in result:
			lista_trabalhos.append(record.values())

	
	strings_dict = {}
	for lst in lista_trabalhos:
		#strings_dict[lst[0]] = {'tipo': lst[1]}
		strings_dict[lst[0]] = (lst[1], lst[2])
		#salva as informacoes pertinentes a cada referencia

	st = time.time()		
	for str1, str2 in combinations(strings_dict.keys(), 2):
		similarity = (string_similarity(str1,str2))
		similarity = round(similarity,3)
		if similarity > 0.45:
			if (strings_dict[str1][0] == 'primario' and strings_dict[str2][0] == 'primario'): continue
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
	except Exception as e:
		traceback.print_exc()
		return(e)


def return_simil(user_id, project_id):
	driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
	with driver.session() as session: 
		try:
			q = f"""MATCH (f:simil_flag {{user_id:'{user_id}', project_id:'{project_id}'}}) return f.status"""
			result = session.run(q).single().value()
			if result == 'no_similarity_done': 
				compare_refs(user_id, project_id)

			q=f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}})-[s:similar_to]->(r:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.id as a_ref_id, t.title as a_title, r.id as b_ref, r.title as b_title, s.value as similarity order by toLower(t.title)""" 
			result = session.run(q)
			ref_list=[]
			ref_dict={}
			for record in result:
				#ref_list.append(record.values())  
				a_ref_id = record['a_ref_id']
				data = {
					'a_title': record['a_title'],
					'b_ref': record['b_ref'],
					'b_title': record['b_title'],
					'similarity': round(float(record['similarity']), 3)
				}
				ref_dict[a_ref_id] = data
					
			#for index,element in enumerate(ref_list):
			#	simil = round(float(element[4]),3)
			#	ref_list[index][4] = simil
			
			return ref_dict
		except Exception as e:
			traceback.print_exc()
			ref_list = []
			return ref_list
		