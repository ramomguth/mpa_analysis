from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
#from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from dataclasses import dataclass
import igraph as ig
from igraph import Graph
import numpy as np
import pandas as pd
import json, uuid
import itertools
from .scraper_sbc import *
from .mpa import *
#import requests 
import traceback

# Create your views here.
def index(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    try:
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session: 
            q = f"""MATCH (p:Project{{user_id:"{request.session['user_id']}"}}) return p.name, p.descricao"""       #mostra a lista de projetos para o 
            neo4j_query_result = session.run(q)                                                                     #usuario na tela
            project_list = []
            for record in neo4j_query_result:
                project_list.append(record.values())
            
            # mostra o projeto selecionado atualmente
            project_id = request.COOKIES.get('project_id')
            if (project_id):
                q = f"""MATCH (p:Project{{project_id:"{project_id}"}}) return p.name"""       #retorna o nome do projeto 
                project_name = session.run(q).value()[0] 
            else:
                project_name = "Nenhum projeto selecionado"
            user_id = request.COOKIES.get('user_id')
            #compare_refs(user_id, project_id)
            return render(request, 'test/index.html', {'projects': project_list, 'project_id': project_name})
    except Exception as e:
        traceback.print_exc()
        return (e)


def login_user(request):
    if request.method != 'POST':
        return render(request, 'test/login.html')
    
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
                        'redirect_url': reverse('index')  
                }
                response = JsonResponse(response_data)
                response.set_cookie('user_id', id)
                return response
            else:
                response_data = {
                    'auth_status': 'failure',
                    'message': 'Usuario ou senha incorreta.'  
                }
                return JsonResponse(response_data)
    except Exception as e:
        return (e)
 
def register(request):
    if request.method != 'POST':
        return render(request, 'test/register.html')
    
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
            copy_res = res
            
            if (copy_res == 0):      #nao existe esse email na base
                id = uuid.uuid4()
                q = f"""CREATE (u:User{{name:"{username}", passwd:"{password}", email:"{email}", user_id:"{id}"}}) return u"""
                res = session.run(q).single()[0]
                copy_res = res
                if (copy_res):
                    user0 = User.objects.create_user(username, email, password)
                    user = authenticate(request, username=username, password=password)
                    login(request, user)
                    request.session['user_id'] = str(id)
                    #response = redirect('index')
                    #response.set_cookie('user_id', id)
                    response_data = {
                        'auth_status': 'success',
                        'redirect_url': reverse('index')  
                    }
                    response = JsonResponse(response_data)
                    response.set_cookie('user_id', id)
                    return response
            else:
                response_data = {
                    'auth_status': 'failure',
                    'message': 'Usuario ou Email ja existe',  
                }
                response = JsonResponse(response_data)
                return response

    except Exception as e:
        traceback.print_exc()
        return (e)

def logout_view(request):
    logout(request)
    response = redirect('login_user')
    response.delete_cookie('user_id')
    response.delete_cookie('project_id')
    return response


def create_project(request):
    if (not request.user.is_authenticated):
        return render(request, 'test/login.html')
    if request.method != 'POST':
        return render(request, 'test/create_project.html') 
    
    nome = request.POST['nome']
    descricao = request.POST['descricao']
    user_id = request.session['user_id']
    if (nome and descricao and user_id):
        try:
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session:
                id = uuid.uuid4()
                q = f"""CREATE (p:Project{{name:"{nome}", descricao:"{descricao}", user_id:"{user_id}", project_id:"{id}"}}) return p"""
                result = session.run(q).single()
                response = redirect('index')
                return response
        except Exception as e:
            return (e)
   

def set_project(request):
    if (request.user.is_authenticated and request.method == 'POST'):
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
    
def delete_project(request):
    if (request.user.is_authenticated and request.method == 'DELETE'):
        user_id = request.session['user_id']
        project_id = request.COOKIES.get('project_id')

        if (not project_id):
            response = HttpResponse("empty")
            return response
        else:
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session:
                tx = session.begin_transaction()
                try:
                    query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) delete f"
                    result = tx.run (query, user_id=user_id, project_id=project_id)
                    query = "MATCH (p:Project {user_id:$user_id, project_id:$project_id}) delete p"
                    result = tx.run (query, user_id=user_id, project_id=project_id)
                    query = "MATCH (t:trabalho {user_id:$user_id, project_id:$project_id}) detach delete t"
                    result = tx.run (query, user_id=user_id, project_id=project_id)
                    tx.commit()

                    expires = datetime.now() - timedelta(days=365)  # Set the expired date in the past
                    response = HttpResponse("ok")
                    response.set_cookie('project_id', '', expires=expires)
                    return response
                except Exception as e:
                    tx.rollback()
                    return HttpResponse(e)
    else:
        return redirect('login_user')
  
  
def scraper(request):
    if (not request.user.is_authenticated):
        return render(request, 'test/login.html')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        return redirect('index') 
     
    if (request.user.is_authenticated and request.method == 'POST'):
        project_id = request.COOKIES.get('project_id')
        user_id = request.COOKIES.get('user_id')
        try:
            #pega o link do usuario
            body_unicode = request.body.decode('utf-8')
            post_data = json.loads(body_unicode)
            result = scrape_sbc_event(post_data)
            
            if result == "invalid_url":
                response_data = {
                    'status': result,
                }
                response = JsonResponse(response_data)
                return response
            else:
                print_data = []
                for trabalho in result:
                    print_data.append(trabalho.title)
                    for ref in trabalho.references:
                        print_data.append(ref)

                save_scraper_data(result, user_id, project_id)
                #compare_refs(user_id, project_id)
                response_data = {
                    'size': len(print_data),
                    'content': print_data,
                    'status': 'ok',
                }
                response = JsonResponse(response_data)
                return response
        except Exception as e:
            traceback.print_exc()
            response_data = {
                'content': result,
                'status': 'ok',
            }
            return (e)
    #return render(request, 'test/scraper.html',{'works': result})
    return render(request, 'test/scraper.html')



def similarities(request): #simil result?
    if (not request.user.is_authenticated):
        return redirect('login_user')
    
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        return redirect('index')
    
    #q=f"""MATCH (t:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}})-[s:similar_to]->(r:trabalho {{user_id:'{user_id}', project_id:'{project_id}'}}) return t.id as a_ref_id, t.title as a_title, r.id as b_ref, r.title as b_title, s.value as similarity order by t.title""" 
    #print(q)
    result = return_simil(user_id, project_id)
    return render(request, 'test/similarities.html',{'refs': result})
   
  
  
def save_similarities(request):
    #post_data = json.loads(request.body)
    #my_list = [(key, value) for key, value in post_data.items()]
    #print(my_list[0][1])
    if (not request.user.is_authenticated):
        return redirect('login_user')
    
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        return redirect('index')
    
    if request.method == 'POST':
        try:
            #table_data = json.loads(request.POST.get('my_data'))
            #table_data = list(table_data.values())
            post_data = list(json.loads(request.body))
            if not post_data[0]:
                return HttpResponse("none")
            if not post_data[1]:
                return HttpResponse("none")
            
            main_ref = post_data.pop(0)
            main_ref = main_ref[0][0] #por alguma razao vem como lista de lista
            info_to_alter = list(itertools.chain(*post_data)) #vem com infos desnecessarias
            refs_to_alter = [[sublist[0], sublist[2]] for sublist in info_to_alter] #pega so os ids das refer
           
            flattened_list = [item for sublist in refs_to_alter for item in sublist] # Creating a set to remove duplicates

            unique_refs = list(set(flattened_list))
            unique_refs.remove(main_ref)
            
            
            st = time.time()
            #for elem in unique_refs:
            resp = save_altered_similarities(main_ref, unique_refs, user_id, project_id)
            et = time.time()
            print ("time = ", et - st)

            if (resp == "ok"):
                return HttpResponse(200)
        except Exception as e:
                traceback.print_exc()
                return HttpResponse(e)
        

def finish_similarities(request):
    if request.method == 'POST':
        try:
            post_data = json.loads(request.body)
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            user_id = request.COOKIES.get('user_id')
            project_id = request.COOKIES.get('project_id')

            with driver.session() as session:
                tx = session.begin_transaction()
                query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) set f.status = 'complete'"
                result = tx.run (query, user_id=user_id, project_id=project_id)
              
                query = "MATCH (a:trabalho {user_id:$user_id, project_id:$project_id})-[s:similar_to]->(b:trabalho {user_id:$user_id, project_id:$project_id}) delete s"
                result = tx.run (query, user_id=user_id, project_id=project_id)

                #query = "MATCH (t:trabalho {user_id:$user_id, project_id:$project_id})<-[:referencia]-(r) WITH t, count(r) as incomingRefs WHERE incomingRefs = 1 set t.show = 'false'"
                #result = tx.run (query, user_id=user_id, project_id=project_id)

                resp = {
                    'status': 'ok'
                }
                tx.commit()
                return JsonResponse(resp)
        except Exception as e:
            tx.rollback()
            traceback.print_exc()
            return HttpResponse(e)


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

def mpa(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    
    if request.method == 'GET':
        return render(request, 'test/mpa.html')
    
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        return redirect('index')
    
    if request.method == 'POST':
        try:
            post_data = json.loads(request.body)
            tipo = post_data[0]
            cytoscape_json = make_mpa(tipo, user_id, project_id)

            return JsonResponse(cytoscape_json)
        
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(e)


def make_mpa(tipo, user_id, project_id):
    try:
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session: 
            query = "match (s:trabalho {user_id:$user_id, project_id:$project_id})-[:referencia]->(d:trabalho {user_id:$user_id, project_id:$project_id}) return s.id as source_id, s.title as source_name, d.id as target_id, d.title as target_name" 
            result = session.run(query, user_id=user_id, project_id=project_id)
            #query = "match (s:Trabalho)-[:Referencia]->(d:Trabalho) return id(s) as source_id, s.title as source_name, id(d) as target_id, d.title as target_name" 
            #result = session.run(query)
            data = [record for record in result]
            
            sources = [record['source_id'] for record in data]
            targets = [record['target_id'] for record in data]
            comb = list(zip(sources, targets))
          
            
            query = "match (s:trabalho {user_id:$user_id, project_id:$project_id}) return s.id as source_id, s.title as source_name, s.tipo as tipo"
            result = session.run(query, user_id=user_id, project_id=project_id)
            #query = "match (s:Trabalho) return id(s) as source_id, s.title as source_name"
            #result = session.run(query)
            data = [record for record in result]
            #isso nao sao sources, sao todos os nos
            all_nodes_ids = [record['source_id'] for record in data]
            all_nodes_names = [record['source_name'] for record in data]
            all_nodes_tipo = [record['tipo'] for record in data]

            
            #usa como id numeros crescente inves de usar o uuid
            g = ig.Graph(directed=True)
            id_to_index = {}
            for index, node_id in enumerate(all_nodes_ids):
                g.add_vertex(name=all_nodes_names[index])
                id_to_index[node_id] = index

            # Add edges to the graph using the mapping.
            for source_id, target_id in comb:
                g.add_edge(id_to_index[source_id], id_to_index[target_id])
        
            for index, element in enumerate(all_nodes_names):
                g.vs[index]["name"] = element

            for index, element in enumerate(all_nodes_tipo):
                g.vs[index]["tipo"] = element
           
            g.vs["label"] = g.vs["name"]   

            if tipo == 'splc':
                splc(g)
                #ig.plot(g, vertex_label=l.vs["label"], target="l.svg")
                ig.plot(g, layout="kk", edge_label=g.es["SPLC"], target="g.svg",bbox=(5000, 5000))
                longest_path = []
                max_length = 0
                longest_edge_path = []

                visited = [False] * g.vcount()

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
                #print (main_path)
                ig.plot(main_path, layout="kk", edge_label=main_path.es["SPLC"], target="main_path.svg",bbox=(1920, 1080))

                #nodes
                nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in g.vs]
                # Create edges list
                edges = [{"data": {"source": edge.source, "target": edge.target, "splc":edge["SPLC"]}} for edge in g.es if edge["SPLC"] > 1]

                #mpa nodes
                mpa_nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in main_path.vs]
                # Create edges list
                mpa_edges = [{"data": {"source": edge.source, "target": edge.target}} for edge in main_path.es]
            else:
                spc(g)
                ig.plot(g, layout="kk", edge_label=g.es["SPC"], target="g.svg")
            
                # Calculate the longest path considering 'SPC' attribute
                longest_path = []
                max_length = 0
                longest_edge_path = []

                visited = [False] * g.vcount()

                for v in range(g.vcount()):
                    path, edge_path, length = longest_path_spc(g, v, visited, [], [], 0, longest_path, longest_edge_path, max_length)
                    if length > max_length:
                        longest_path = path
                        longest_edge_path = edge_path
                        max_length = length

                main_path = g.subgraph_edges(longest_edge_path)
                print("Longest path:", longest_path)
                print("edge:", longest_edge_path)
                #print("Longest path length:", max_length)
                #print (main_path)
                ig.plot(main_path, layout="kk", edge_label=main_path.es["SPC"], target="main_path.svg",bbox=(3000, 3000))

                #complete graph nodes
                nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in g.vs]
                # Create edges list
                edges = [{"data": {"source": edge.source, "target": edge.target, "spc":edge["SPC"]}} for edge in g.es if edge["SPC"] > 1]

                #mpa nodes
                mpa_nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in main_path.vs]
                # Create edges list
                mpa_edges = [{"data": {"source": edge.source, "target": edge.target}} for edge in main_path.es]

            # Create a dictionary in the desired format
            cytoscape_json = {
                "elements": {
                    "nodes": nodes,
                    "edges": edges
                },
                "mpa_elements": {
                    "mpa_nodes": mpa_nodes,
                    "mpa_edges": mpa_edges
                }
            }

            #print(cytoscape_json["mpa_elements"])
            return cytoscape_json
    except Exception as e:
        traceback.print_exc()
        return (e)
    
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
        print(sources_names) #tem todos os nos

        '''for i, elem in enumerate(comb):
                print(i, elem)
                print(g.vertices())
                s = elem[0]
                t = elem[1]
                g.add_edge(s,t)'''
        
        '''comb = [('a', 'c'), ('b', 'j'), ('b', 'd'), ('b', 'c'), ('c', 'h'), ('c', 'e'), ('d', 'i'), ('d', 'f'), ('e', 'g'), ('f', 'h'), 
            ('f', 'i'), ('g', 'h'), ('h', 'k'), ('i', 'm'), ('i', 'l'), ('j', 'm'), ('m', 'n')]'''
            
        g = ig.Graph(directed=True)
        g.add_vertices(sources_ids)
        for index, element in enumerate(sources_names):
            g.vs[index]["name"] = element
        g.add_edges(comb)
        g.vs["label"] = g.vs["name"]
        return HttpResponse("ok")
   
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
    


#backup
'''
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

        return HttpResponse("ok")'''

