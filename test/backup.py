# MPA

def main_search(g):
    linegraph = g.linegraph()
    #linegraph.vs["spc"] = spc(g)

    source_edges = [v for v in linegraph.vs if v.degree(mode="in") == 0]
    sink_edges = [v for v in linegraph.vs if v.degree(mode="out") == 0]

    paths = [path for source in source_edges for path in linegraph.get_all_simple_paths(source, to=sink_edges, mode="out")]
    path_lengths = [sum(linegraph.vs[path]["spc"]) for path in paths]

    linegraph.vs["main_path"] = 0
    main_path_index = path_lengths.index(max(path_lengths))
    main_path = paths[main_path_index]
    linegraph.vs[main_path]["main_path"] = 1

    return linegraph.vs["main_path"]



def simplequery(driver):
    with driver.session() as session: 
        result1 = session.run("MATCH (t:Trabalho) return t.id, t.title, t.num_ref limit 1")
        list_trabalhos = []
        list_trab_id = []
        list_trab_title = []
        list_trab_num_ref = []
        nodes = []
        edges = []
        for record in result1:
            #list_trab_id = record["t.id"]
            #list_trab_title = record["t.title"]
            #list_trab_num_ref = record["t.num_ref"]
            list_trabalhos.append(record.values())
        edge_id = 0
        for index,element in enumerate(list_trabalhos):
            node = {
                "data": {
                    "id": "n" + str(element[0]),  # the string representation of the unique node ID
                    "idInt": int(element[0]),  # the numeric representation of the unique node ID
                    "name": element[1],  # the name of the node used for printing
                    "query": True,
                    "iswork": True,
                },
                "group": "nodes",  # it belongs in the group of nodes
                "removed": False,
                "selected": False,  # the node is not selected
                "selectable": True,  # we can select the node
                "locked": False,  # the node position is not immutable
                "grabbable": True  # we can grab and move the node 
            }
            nodes.append(node)

        for element in list_trabalhos:
            q = f"""MATCH (t:Trabalho{{id:'{element[0]}'}})-[s:Referencia]->(r:Reference) return r.ref_id, r.title order by r.ref_id"""
            result2 = session.run(q)

            list_ref = []
            for record in result2:
                list_ref.append(record.values())
            
            for element_ref in list_ref:
                node = {
                    "data": {
                        "id": "n" + str(element_ref[0]),  # the string representation of the unique node ID
                        "idInt": int(element_ref[0]),  # the numeric representation of the unique node ID
                        "name": element_ref[1],  # the name of the node used for printing
                        "query": True,
                        "isref": "blue"
                    },
                    "group": "nodes",  # it belongs in the group of nodes
                    "removed": False,
                    "selected": False,  # the node is not selected
                    "selectable": True,  # we can select the node
                    "locked": False,  # the node position is not immutable
                    "grabbable": True  # we can grab and move the node 
                }
                nodes.append(node)
            
            for element_ref in list_ref:
                edge = {
                    "data": {
                        "source": "n" + str(element[0]),  # the source node id (edge comes from this node)
                        "target": "n" + str(element_ref[0]),  # the target node id (edge goes to this node)
                        "directed": True,
                        "id": "e" + str(edge_id),
                    },
                    "position": {},  # the initial position is not known
                    "group": "edges",  # it belongs in the group of edges
                    "removed": False,
                    "selected": False,  # the edge is not selected
                    "selectable": True,  # we can select the node
                    "locked": False,  # the edge position is not immutable
                    "grabbable": False,  # we can grab and move the node
                    "directed": True  # the edge is directed
                }
                edges.append(edge)
                edge_id += 1
            #result2 = session.run("MATCH (t:Trabalho)-[s:Referencia]->(r:Reference) r.title limit 23")
        data = nodes + edges
        djs = json.dumps(data)   
        
        """for i in range(total_records):
            val1.append(res_lis[i])
            num_ref = int(res_lis[i][1])
            for j in range(num_ref):
                val2.append(res_lis[i+j][2])
                k+=1
                continue
            #val1.append(record['a_ref_id'])
        print(val1)"""
        return djs

#SCRAPER

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

