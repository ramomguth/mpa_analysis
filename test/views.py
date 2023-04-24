from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
#from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from neo4j import GraphDatabase
import networkx as nx
import igraph as ig
from igraph import Graph
import numpy as np
import pandas as pd
import json, uuid
import itertools
from .scraper_sbc import *
import requests 

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        try:
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session: 
                q = f"""MATCH (p:Project{{user_id:"{request.session['user_id']}"}}) return p.name, p.descricao"""       #mostra a lista de projetos para o 
                neo4j_query_result = session.run(q)                                                                     #usuario na tela
                result = []
                for record in neo4j_query_result:
                    result.append(record.values())
                return render(request, 'test/index.html',{'projects': result})
        except Exception as e:
            return (e)
    else:
        return redirect('login_user')


def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session: 
                q = f"""MATCH (u:User{{email:"{email}",passwd:"{password}"}}) return u.name, u.user_id, u.passwd, u.email"""
                result = session.run(q)
                neo4j_response=[]           #eh necessario salvar a resposta numa lista, senao e consumida e fica nula
                for record in result:       #o proprio if(result.value()) consome a resposta
                    neo4j_response = record.values() 

                if (neo4j_response):
                    id = str(neo4j_response[1])
                    user = authenticate(request, username=neo4j_response[0], password=neo4j_response[2])
                    login(request, user)
                    request.session['user_id'] = id
                    #response = redirect('index')
                    #response.set_cookie('user_id', id)
                    response_data = {
                            'auth_status': 'success',
                            'redirect_url': reverse('index')  # Replace 'index' with the name of the view you want to redirect to
                    }
                    response = JsonResponse(response_data)
                    response.set_cookie('user_id', id)
                    return response
                else:
                    response_data = {
                        'auth_status': 'failure',
                        'message': 'Usuario ou senha incorreta.'  # Replace this with your actual error message
                    }
                    return JsonResponse(response_data)
        except Exception as e:
            return (e)
    else:
        return render(request, 'test/login.html')
    #return redirect('index')
 
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']        
        password_2 = request.POST['repeatpasswd']
        if (password != password_2):
            return HttpResponse("Senhas nao sao iguais") 
        try:
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session: 
                q = f"""MATCH (u:User{{email:"{email}"}}) return count (u)"""
                res = session.run(q).single().value()

                if (res == 0):      #nao existe esse email na base
                    id = uuid.uuid4()
                    q = f"""CREATE (u:User{{name:"{username}", passwd:"{password}", email:"{email}", num_projects:"0", user_id:"{id}"}}) return u"""
                    res = session.run(q).single()[0]
                    if (res):
                        user0 = User.objects.create_user(username, email, password)
                        user = authenticate(request, username=username, password=password)
                        login(request, user)
                        request.session['user_id'] = str(id)
                        #response = redirect('index')
                        #response.set_cookie('user_id', id)
                        response_data = {
                            'status': 'success',
                            'redirect_url': reverse('index')  
                        }
                        response = JsonResponse(response_data)
                        response.set_cookie('user_id', id)
                        return response
                else:
                    return JsonResponse("Usuario ou Email ja existe")

        except Exception as e:
            return (e)
        #return render(request, 'test/index.html')
    return render(request, 'test/register.html')


 
def create_project(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            nome = request.POST['nome']
            descricao = request.POST['descricao']
            user_id = request.session['user_id']
            if (nome and descricao and user_id):
                try:
                    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
                    with driver.session() as session:
                        id = uuid.uuid4()
                        q = f"""CREATE (p:Project{{name:"{nome}", descricao:"{descricao}", user_id:"{user_id}", project_id:"{id}", num_works:"0"}}) return p"""
                        result = session.run(q).single()
                        response = redirect('index')
                        return response
                except Exception as e:
                    return (e)
        else:
           return render(request, 'test/create_project.html') 
    else:
        return render(request, 'test/login.html')


def results(request):
    if request.user.is_authenticated:
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        result = return_simil(driver)
        return render(request, 'test/stuff.html',{'refs': result})
    else:
        return redirect('login_user')
  
def logout_view(request):
    logout(request)
    response = redirect('login_user')
    response.delete_cookie('user_id')
    response.delete_cookie('project_id')
    return response


@csrf_exempt 
def backend_test(request):
    #post_data = json.loads(request.body)
    #my_list = [(key, value) for key, value in post_data.items()]
    #print(my_list[0][1])
    
    if request.method == 'POST':
        try:
            #table_data = json.loads(request.POST.get('my_data'))
            post_data = list(json.loads(request.body))
            #table_data = list(table_data.values())

            if not post_data[0]:
                return HttpResponse("Nenhuma mudança encontrada")
            
            main_ref = post_data.pop(0)
            refs_to_alter = list(itertools.chain(*post_data))
            
            for elem in refs_to_alter:
                resp = save_altered_similarities(main_ref,elem)
         
            if (resp == "ok"):
                return HttpResponse(200)
        except Exception as e:
                return HttpResponse(e)
        
    return HttpResponse("e")
                
def scraper(request):
    result = scrape_sbc_event('https://sol.sbc.org.br/index.php/wit/issue/view/509')
    return render(request, 'test/scraper.html',{'works': result})

@csrf_exempt 
def set_project(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            post_data = list(json.loads(request.body))
            user_id = request.session['user_id']
            if (post_data):
                project_name = post_data[0]
                try:
                    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
                    with driver.session() as session:
                        q = f"""MATCH (p:Project{{name:'{project_name}',user_id:'{user_id}'}}) return p.project_id"""
                        project_id = session.run(q).value()[0]  #value traz uma lista com 1 elemento, o [0] pega ele
                        response = HttpResponse('ok')
                        response.set_cookie('project_id', project_id)
                        return response
                except Exception as e:
                    return HttpResponse(e)
    else:
        return redirect('login_user')

def save_altered_similarities(main_ref, params):
    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
    id_ref_1 = params[0]
    id_ref_2 = params[1]
    id_new_ref = main_ref
    
    try:
        with driver.session() as session: 
            # 1 - encontrar o trabalho da ref a ser alterada
            q = f"""MATCH (a:Trabalho)-[c:Referencia]->(b:Reference{{ref_id:'{id_ref_2}'}}) return a.id"""
            id_work_to_alter = session.run(q).single().value()

            #2 deletar o relacionamento de similaridade
            q = f"""MATCH (a:Reference{{ref_id:'{id_ref_1}'}})-[c:Similar_to]->(b:Reference{{ref_id:'{id_ref_2}'}}) delete c"""
            result = session.run(q)

            #3 deletar a ref antiga propriamente
            q = f"""MATCH (a:Reference{{ref_id:'{id_ref_2}'}}) detach delete a"""
            result = session.run(q)

            #4 diminuir o num de referencias em 1 do trabalho que teve a referencia deletada
            q = f"""MATCH (t:Trabalho{{id:'{id_work_to_alter}'}}) return toInteger(t.num_ref) - 1 as a"""
            result = session.run(q)
            k = result.value()[0]
            
            #5 continuacao do 4
            q = f"""MATCH (t:Trabalho{{id:'{id_work_to_alter}'}}) set t.num_ref = '{k}'"""
            result = session.run(q)

            #6 criar o novo relacionamento de referencia
            q = f"""MATCH (t:Trabalho {{id:'{id_work_to_alter}'}}), (r:Reference{{ref_id:'{id_new_ref}'}}) CREATE (t)-[:Referencia]->(r)"""
            result = session.run(q)

            return ("ok")
    except Exception as e:
        return(e)


def add_person(driver):
    with driver.session() as session: 
        result = session.run("match (n) return n.title limit 10")
        val2 = [j[0] for j in result]
        val = []
        for record in result:
            val.append(record.value())
        return val2

def return_simil(driver):
    with driver.session() as session: 
        result = session.run("MATCH (a:Reference)-[c:Similar_to]->(b:Reference) return a.ref_id as a_ref_id,a.title as a_title, b.ref_id as b_ref, b.title as b_title,c.similarity order by a.title")
        val1=[]
        for record in result:
            #val1.append(record['a_ref_id'])
            val1.append(record.values())
        
        for index,element in enumerate(val1):
            simil = round(float(element[4]),3)
            val1[index][4] = simil
        return val1


def graph_test(request):
    if request.user.is_authenticated:
        return render(request, 'test/graph.html')
    else: 
        return render(request, 'test/login.html')


def get_graph_data(request):
    if request.method == 'GET':
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        result = simplequery(driver)
        print(result)
        return JsonResponse(result, safe=False)

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

def mpa(request):
    '''
    if request.user.is_authenticated:
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session: 
            result = session.run("MATCH (t:Trabalho)-[s:Referencia]->(r:Reference) return t.id as citing, r.ref_id as cited limit 20")
            #for r in result:
            #    print(r.values())
            citation_data = pd.DataFrame([r.data() for r in result])
        G = nx.from_pandas_edgelist(citation_data, source='citing', target='cited', create_using=nx.DiGraph())

        return render(request, 'test/mpa.html')
    else: 
    '''
    return render(request, 'test/mpa.html')

def get_mpa_data(request):
    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
    with driver.session() as session: 
        result = session.run("match (s)-[:Referencia]->(d) return id(s) as source_id, s.name as source_name, id(d) as target_id, d.name as target_name") #match (s)-[:Referencia]->(d) return id(s) as source_id, s.name as source_name, id(d) as target_id, d.name as target_name
        data = [record for record in result]
        
        sources = [record['source_id'] for record in data]
        targets = [record['target_id'] for record in data]
        comb = list(zip(sources, targets))

        result = session.run ("match (s) return id(s) as source_id, s.name as source_name")
        data = [record for record in result]
        sources_ids = [record['source_id'] for record in data]
        sources_names = [record['source_name'] for record in data]
        
        g = ig.Graph(directed=True)
        g.add_vertices(sources_ids)
        for index, element in enumerate(sources_names):
            g.vs[index]["name"] = element
        g.add_edges(comb)
        g.vs["label"] = g.vs["name"]
   
        """
        # define the start and end vertices, and the specific edge to include
        sinks = [v.index for v in g.vs if g.outdegree(v.index) == 0]
        primary_sources = [v.index for v in g.vs if g.indegree(v.index) == 0]
        edge_list = g.get_edgelist()

        # find all simple paths between start and end vertices
        for index,edge in enumerate(edge_list):
            all_paths = []
            current_node = edge_list[index][1]  #tem o no de destino, tipo c->e, e eh o destino
            #print("edge = ",g.vs[edge[0]]['name'],g.vs[edge[1]]['name'])
            predecessors = []
            unique_pred = []
            find_all_predecessors(g, current_node, predecessors)
            for p in predecessors:
                unique_pred.append(p.index) #p["name"]
            unique_pred = list(set(unique_pred))

            for elem in unique_pred:
                for s in sinks:
                    paths = g.get_all_simple_paths(elem, s, mode="out")
                    all_paths.extend(paths)
                #all_paths = g.get_all_simple_paths(g.vs.find(0), g.vs.find(name=end_vertex).index, mode="out")
                
            #print("todos caminhos", all_paths)  
            paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
                #print("caminhos com o escolhido = ",len(paths_with_edge))
                    
            g.es[index]["SPLC"] = len(paths_with_edge)
            
        """
        splc(g)
        #ig.plot(g, vertex_label=l.vs["label"], target="l.svg")
        ig.plot(g, layout="kk", edge_label=g.es["SPLC"], target="g.svg")
        
        # Calculate the longest path considering 'SPLC' attribute
        longest_path = []
        max_length = 0
        longest_edge_path = []

        visited = [False] * g.vcount()

        """for v in range(g.vcount()):
            path, length = longest_path_dfs(g, v, visited, [], 0, longest_path, max_length)
            if length > max_length:
                longest_path = path
                max_length = length"""

        for v in range(g.vcount()):
            path, edge_path, length = longest_path_dfs(g, v, visited, [], [], 0, longest_path, longest_edge_path, max_length)
            if length > max_length:
                longest_path = path
                longest_edge_path = edge_path
                max_length = length

        main_path = g.subgraph_edges(longest_edge_path)
        print("Longest path:", longest_path)
        print("edge:", longest_edge_path)
        #print("Longest path length:", max_length)
        print (main_path)
        ig.plot(main_path, layout="kk", edge_label=main_path.es["SPLC"], target="main_path.svg")

        return HttpResponse("ok")


"""def longest_path_dfs(graph, vertex, visited, path, path_length, max_path, max_length):
    visited[vertex] = True
    path.append(vertex)

    for neighbor in graph.neighbors(vertex, mode=ig.OUT):
        edge = graph.get_eid(vertex, neighbor, directed=True, error=False)
        if edge != -1:
            edge_splc = graph.es[edge]['SPLC']
            if not visited[neighbor]:
                path_length += edge_splc
                max_path, max_length = longest_path_dfs(graph, neighbor, visited, path, path_length, max_path, max_length)
                path_length -= edge_splc

    if path_length > max_length:
        max_path = list(path)
        max_length = path_length

    path.pop()
    visited[vertex] = False

    return max_path, max_length"""

def longest_path_dfs(graph, vertex, visited, path, edge_path, path_length, max_path, max_edge_path, max_length):
    visited[vertex] = True
    path.append(vertex)

    for neighbor in graph.neighbors(vertex, mode=ig.OUT):
        edge = graph.get_eid(vertex, neighbor, directed=True, error=False)
        if edge != -1:
            edge_splc = graph.es[edge]['SPLC']
            if not visited[neighbor]:
                path_length += edge_splc
                edge_path.append(edge)
                max_path, max_edge_path, max_length = longest_path_dfs(graph, neighbor, visited, path, edge_path, path_length, max_path, max_edge_path, max_length)
                path_length -= edge_splc
                edge_path.pop()

    if path_length > max_length:
        max_path = list(path)
        max_edge_path = list(edge_path)
        max_length = path_length

    path.pop()
    visited[vertex] = False

    return max_path, max_edge_path, max_length

def spc(g):
        sinks = [v.index for v in g.vs if g.outdegree(v.index) == 0]
        primary_sources = [v.index for v in g.vs if g.indegree(v.index) == 0]
        edge_list = g.get_edgelist()
        # find all simple paths between start and end vertices
        for index,edge in enumerate(edge_list):
            all_paths = []
            #print("edge = ",g.vs[edge[0]]['name'],g.vs[edge[1]]['name'])

            for ps in primary_sources:
                for s in sinks:
                    paths = g.get_all_simple_paths(ps, s, mode="out")
                    all_paths.extend(paths)
                #all_paths = g.get_all_simple_paths(g.vs.find(0), g.vs.find(name=end_vertex).index, mode="out")
            
            #print("todos caminhos", all_paths)  
            # filter paths that include the specific edge
            paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
            #print("caminhos com o escolhido = ",len(paths_with_edge))
            
            g.es[index]["SPC"] = len(paths_with_edge)

def splc(g):
    sinks = [v.index for v in g.vs if g.outdegree(v.index) == 0]
    primary_sources = [v.index for v in g.vs if g.indegree(v.index) == 0]
    edge_list = g.get_edgelist()

        # find all simple paths between start and end vertices
    for index,edge in enumerate(edge_list):
        all_paths = []
        current_node = edge_list[index][1]  #tem o no de destino, tipo c->e, e eh o destino
        #print("edge = ",g.vs[edge[0]]['name'],g.vs[edge[1]]['name'])
        predecessors = []
        unique_pred = []
        find_all_predecessors(g, current_node, predecessors)
        for p in predecessors:
            unique_pred.append(p.index) #p["name"]
        unique_pred = list(set(unique_pred))

        for elem in unique_pred:
            for s in sinks:
                paths = g.get_all_simple_paths(elem, s, mode="out")
                all_paths.extend(paths)
            #all_paths = g.get_all_simple_paths(g.vs.find(0), g.vs.find(name=end_vertex).index, mode="out")                
            #print("todos caminhos", all_paths)  
        
        paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
        #print("caminhos com o escolhido = ",len(paths_with_edge))            
        g.es[index]["SPLC"] = len(paths_with_edge)


def find_all_predecessors(g, node, predecessors):
    pred = g.vs[node].predecessors()
    if len(pred) == 0:
        return predecessors
    else:
        predecessors.extend(pred)
        for p in pred:
            find_all_predecessors(g, p.index, predecessors)


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
