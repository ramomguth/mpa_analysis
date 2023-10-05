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
import bcrypt
import csv
#import numpy as np
#import pandas as pd
import json, uuid
import itertools
from .scraper_sbc import *
from .mpa import *
#import requests 
import traceback

#teste outra BRANCH
#
#
def index(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    try:
        #project_id = request.COOKIES.get('project_id')
        #user_id = request.COOKIES.get('user_id')
        #read_csv(user_id,project_id)
        driver = GraphDatabase.driver(uri="bolt://db:7687", auth=("neo4j", "superman"))
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
            return render(request, 'test/index.html', {'projects': project_list, 'project_id': project_name})
    except Exception as e:
        traceback.print_exc()
        return (e)

def alert_and_redirect(request, message, redirect_url):
    return render(request, 'test/alert_and_redirect.html', {
        'message': message,
        'redirect_url': redirect_url
    })    

def projects(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    try:
        #project_id = request.COOKIES.get('project_id')
        #user_id = request.COOKIES.get('user_id')
        #read_csv(user_id,project_id)
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
            return render(request, 'test/projects.html', {'projects': project_list, 'project_id': project_name})
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
            q = f"""MATCH (u:User{{email:"{email}"}}) return u.name, u.user_id, u.passwd, u.email"""
            result = session.run(q)
            neo4j_response=[]           #eh necessario salvar a resposta numa lista, senao e consumida e fica nula
            for record in result:       #o proprio if(result.value()) consome a resposta
                neo4j_response = record.values() 

            if neo4j_response and bcrypt.checkpw(password.encode('utf-8'), neo4j_response[2].encode('utf-8')):
                id = str(neo4j_response[1])
                user = authenticate(request, username=neo4j_response[0], password=password)
                if user:
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
        traceback.print_exc()
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
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        driver = GraphDatabase.driver(uri="bolt://db:7687", auth=("neo4j", "superman"))
        with driver.session() as session: 
            q = f"""MATCH (u:User{{email:"{email}"}}) return count (u)"""
            res = session.run(q).single().value()
            copy_res = res
            
            if (copy_res == 0):      #nao existe esse email na base
                id = uuid.uuid4()
                
                q = f"""CREATE (u:User{{name:"{username}", passwd:"{hashed_password}", email:"{email}", user_id:"{id}"}}) return u"""
                res = session.run(q).single()[0]
                copy_res = res
                if (copy_res):
                    #Django ja tem um sistema de criptografia de senhas interno, logo nao precisa usar outro
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
                q = f"""CREATE (p:Project{{name:"{nome}", descricao:"{descricao}", user_id:"{user_id}", project_id:"{id}"}}) return p.project_id"""
                result = session.run(q).single().value()
                project_id = result
                response = redirect('index')
                response.set_cookie('project_id', project_id)
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
        project_id_cookie = request.COOKIES.get('project_id')
        project_name = (json.loads(request.body))
        if (not project_name):
            response = HttpResponse("empty")
            return response
        else:            
            driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
            with driver.session() as session:
                tx = session.begin_transaction()
                try:
                    query = "MATCH (p:Project {user_id:$user_id, name:$project_name}) return p.project_id"
                    project_id = tx.run (query, user_id=user_id, project_name=project_name).single().value()

                    query = "MATCH (p:Project {user_id:$user_id, project_id:$project_id}) delete p"
                    result = tx.run (query, user_id=user_id, project_id=project_id)

                    query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) delete f"
                    result = tx.run (query, user_id=user_id, project_id=project_id)  
                    query = "MATCH (t:trabalho {user_id:$user_id, project_id:$project_id}) detach delete t"
                    result = tx.run (query, user_id=user_id, project_id=project_id)
                    tx.commit()
                    if (project_id_cookie == project_id):
                        expires = datetime.now() - timedelta(days=365)  # Set the expired date in the past
                        response = HttpResponse("ok")
                        response.set_cookie('project_id', '', expires=expires)
                        return response
                    else:
                        response = HttpResponse("ok")
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
        message = 'Necessário selecionar um projeto antes!'
        redirect_url = reverse('index')  
        return alert_and_redirect(request, message, redirect_url)
     
    if (request.user.is_authenticated and request.method == 'POST'):
        project_id = request.COOKIES.get('project_id')
        user_id = request.COOKIES.get('user_id')
        try:
            #pega o link do usuario
            body_unicode = request.body.decode('utf-8')
            post_data = json.loads(body_unicode)
            result = scrape_sbc_event(post_data, user_id, project_id)
            
            if result == "invalid_url":
                response_data = {
                    'status': result,
                }
                response = JsonResponse(response_data)
                return response
            if result == "url_already_used":
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

def import_csv(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        message = 'Necessário selecionar um projeto antes!'
        redirect_url = reverse('index')  
        return alert_and_redirect(request, message, redirect_url)
    if (request.user.is_authenticated and request.method != 'POST'): 
        return render(request, 'test/import.html')
    try:
        uploaded_file = request.FILES.get('file')
        decoded_file = uploaded_file.read().decode('utf-8').splitlines()   
        # Create a CSV reader object
        csv_reader = csv.reader(decoded_file)  
        data = []
        for row in csv_reader:
            data.append(row)
        project_id = request.COOKIES.get('project_id')
        user_id = request.COOKIES.get('user_id')
        status = read_csv(data, user_id, project_id)
        if status == 'ok':
            return HttpResponse('ok')
    except Exception as e:
        traceback.print_exc()
        return (e)

           
def similarities(request): 
    if (not request.user.is_authenticated):
        return redirect('login_user')
    
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        message = 'Necessário selecionar um projeto antes!'
        redirect_url = reverse('index')  
        return alert_and_redirect(request, message, redirect_url)
    
    result = return_simil(user_id, project_id)
    return render(request, 'test/similarities.html',{'refs': result})
   
  
  
def save_similarities(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        return redirect('index')
    if request.method == 'POST':
        try:
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
            
            #st = time.time()
            #for elem in unique_refs:
            resp = save_altered_similarities(main_ref, unique_refs, user_id, project_id)
            #et = time.time()
            #print ("time = ", et - st)
            if (resp == "ok"):
                return HttpResponse(200)
        except Exception as e:
                traceback.print_exc()
                return HttpResponse(e)
        

def finish_similarities(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
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

def infos(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        message = 'Necessário selecionar um projeto antes!'
        redirect_url = reverse('index')  
        return alert_and_redirect(request, message, redirect_url)
    
    if request.method == 'GET':
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session:
            query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) return f.status"
            result = session.run (query, user_id=user_id, project_id=project_id).single().value()
            if result != 'complete':
                message = 'Necessário finalizar o processo de similaridades!'
                redirect_url = reverse('similarities')  
                return alert_and_redirect(request, message, redirect_url)
            else:
                return render(request, 'test/mpa.html')
  
    if request.method == 'POST':
        try:
            cytoscape_json = get_full_graph(user_id, project_id)
            return JsonResponse(cytoscape_json)
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(e)
        

def mpa(request):
    if (not request.user.is_authenticated):
        return redirect('login_user')
    
    user_id = request.COOKIES.get('user_id')
    project_id = request.COOKIES.get('project_id')
    if (not project_id):
        message = 'Necessário selecionar um projeto antes!'
        redirect_url = reverse('index')  
        return alert_and_redirect(request, message, redirect_url)
    if request.method == 'GET':
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session:
            query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) return f.status"
            result = session.run (query, user_id=user_id, project_id=project_id).single().value()
            if result != 'complete':
                message = 'Necessário finalizar o processo de similaridades!'
                redirect_url = reverse('similarities')  
                return alert_and_redirect(request, message, redirect_url)
            else:
                return render(request, 'test/mpa.html')
    
    if request.method == 'POST':
        try:
            post_data = json.loads(request.body)
            tipo = post_data[0]
            #st = time.time()
            cytoscape_json = make_mpa(tipo, user_id, project_id)
            #et = time.time()
            #print ("mpa time = ", et - st)
            return JsonResponse(cytoscape_json)
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(e)