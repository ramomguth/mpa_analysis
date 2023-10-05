from neo4j import GraphDatabase
import igraph as ig
from igraph import Graph
#import numpy as np
#import pandas as pd
import json
import traceback
from collections import defaultdict


def save_altered_similarities(main_ref, params, user_id, project_id):
    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
    """
    nova logica
    1 - com o id da ref a ser alterada, encontrar quem referencia ela
    2 - deletar essa referencia e seus relacionamentos (similaridades e referenciamentos)
    3 - criar o novo relacionamento entre a principal e quem referenciava a deletada
    
    Basicamente tem 4 casos
    1 - ref com ref, já feito
    2 - primaria com ref: um principal vai endereçar outro indiretamente
    principal -> ref -> outro principal
    3 - marcar ref com principal não pode, ignora o usuario e marca a primaria como principal
    4 - primaria com primaria: Não pode, deleta a similaridade e da continue - tratado no compare_refs
    
    """
    try:
        with driver.session() as session: 
            tx = session.begin_transaction()

            # 1 - atualizar o status da flag de similaridade
            query = "MATCH (f:simil_flag {user_id:$user_id, project_id:$project_id}) set f.status = 'in_progress'"
            tx.run (query, user_id=user_id, project_id=project_id)

            '''
            caso = 0 -> tudo que foi marcado pelo usuario e referencia secundaria
            caso = 1 -> o usuario marcou uma referencia primaria como principal
            caso = 2 -> o usuario marcou uma referencia secundaria como principal e quer alterar para primaria - NAO PODE
            '''
            caso = 0
            ref_to_alter = 0
            for ref_id in params:
                query = "MATCH (a:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}),(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.tipo as tipo_main, b.tipo as tipo_b"
                result = tx.run(query, main_ref=main_ref, ref_id=ref_id, user_id=user_id, project_id=project_id).single()
                #for record in result:   caso nao usar .single() no result precisa fazer isso
                #    tipo_main = record['tipo_main']
                #    tipo_b = record['tipo_b']
                if (result['tipo_main'] != 'referencia'):
                    caso = 1
                    break
                if (result['tipo_b'] != 'referencia'):
                    caso = 2
                    ref_to_alter = ref_id
                    break
            
            if (caso == 0):
                print('caso0')
                for ref_id in params:
                    query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id"
                    id_work_to_alter = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    id_work_to_alter = id_work_to_alter.single().value()
                    #print("para alterar", id_work_to_alter)

                    #3 deletar a ref antiga propriamente com seus relacionamentos
                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    #print("deletado", ref_id)

                    #4 criar o novo relacionamento de referencia
                    query = "MATCH (t:trabalho{id:$id_work_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_work_to_alter=id_work_to_alter, main_ref=main_ref, user_id=user_id, project_id=project_id)
                    #print(id_work_to_alter, "referencia", main_ref)
                    

            '''no caso 1, todas as referencias devem apontar para a principal (que eh do tipo primaria)'''
            if (caso == 1):
                print("caso 1")
                for ref_id in params:
                    query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id as id_to_alter"
                    result = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id).single()
                    id_to_alter = result['id_to_alter']
                    #print("para alterar ",id_to_alter)

                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    #print('deletado ', ref_id)


                    query = "MATCH (t:trabalho{id:$id_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_to_alter=id_to_alter, main_ref=main_ref, user_id=user_id, project_id=project_id)
                    #print(id_to_alter, "referencia", main_ref)
            
            #no caso 2 todas referencias tambem devem apontar para a referencia primaria, mesmo que o usuario tenha marcado uma secundaria como principal
            if (caso == 2):
                print("caso 2")
                params.remove(ref_to_alter)
                params.append(main_ref)
                
                for ref_id in params:
                    query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id as id_to_alter"
                    result = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id).single()
                    id_to_alter = result['id_to_alter']
                    #print("para alterar ",id_to_alter)
                

                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    #print('deletado ', ref_id)


                    query = "MATCH (t:trabalho{id:$id_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$ref_to_alter, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_to_alter=id_to_alter, ref_to_alter=ref_to_alter, user_id=user_id, project_id=project_id)
                    #print(id_to_alter, "referencia", ref_to_alter)

            tx.commit()
            return ("ok")
    except Exception as e:
        tx.rollback()
        traceback.print_exc()
        return(e)

def get_full_graph(user_id, project_id):
    try:
        driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
        with driver.session() as session: 
            query = "match (s:trabalho {user_id:$user_id, project_id:$project_id})-[:referencia]->(d:trabalho {user_id:$user_id, project_id:$project_id}) return s.id as source_id, s.title as source_name, d.id as target_id, d.title as target_name" 
            result = session.run(query, user_id=user_id, project_id=project_id)
            data = [record for record in result]
            
            sources = [record['source_id'] for record in data]
            targets = [record['target_id'] for record in data]
            comb = list(zip(sources, targets))

            query = "match (s:trabalho {user_id:$user_id, project_id:$project_id}) return s.id as source_id, s.title as source_name, s.tipo as tipo"
            result = session.run(query, user_id=user_id, project_id=project_id)
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

            in_degrees = g.indegree()
            out_degrees = g.outdegree()
            total_degrees = g.degree()

            # Step 3: Find the vertices with the highest indegree, outdegree, and total degree
            max_indegree_vertex_id = in_degrees.index(max(in_degrees))
            max_outdegree_vertex_id = out_degrees.index(max(out_degrees))
            max_total_degree_vertex_id = total_degrees.index(max(total_degrees))

            # Step 4: Get the names of the vertices with the highest degrees
            max_indegree_vertex_name = g.vs[max_indegree_vertex_id]['name']
            max_outdegree_vertex_name = g.vs[max_outdegree_vertex_id]['name']
            max_total_degree_vertex_name = g.vs[max_total_degree_vertex_id]['name']

            indegree_result = {'id': max_indegree_vertex_id, 'name': max_indegree_vertex_name, 'degree': max(in_degrees)}
            outdegree_result = {'id': max_outdegree_vertex_id, 'name': max_outdegree_vertex_name, 'degree': max(out_degrees)}
            total_degree_result = {'id': max_total_degree_vertex_id, 'name': max_total_degree_vertex_name, 'degree': max(total_degrees)}

            indegree_list = [max_indegree_vertex_id, "Indegree = " + str(max(in_degrees)), max_indegree_vertex_name]
            outdegree_list = [max_outdegree_vertex_id, "Outdegree = " + str(max(out_degrees)), max_outdegree_vertex_name]
            total_degree_list = [max_total_degree_vertex_id,"Total Degree = " + str(max(total_degrees)), max_total_degree_vertex_name]
            
            nodes = [{"data": {
                            "id": v.index, 
                            "tipo": v["tipo"], 
                            "name":v["name"], 
                            "label": v["name"],
                            "max_indegree": str(v.index == max_indegree_vertex_id).lower(),
                            "max_outdegree": str(v.index == max_outdegree_vertex_id).lower(),
                            "max_total_degree": str(v.index == max_total_degree_vertex_id).lower()
                        }
                    } for v in g.vs]
            edges = [{"data": {"source": edge.source, "target": edge.target}} for edge in g.es]
            
            for node in nodes:
                if node["data"]["max_indegree"] == True: print(node)
            cytoscape_json = {
                "elements": {
                    "nodes": nodes,
                    "edges": edges
                },
                "infos": [indegree_list, outdegree_list, total_degree_list]
            }
            return cytoscape_json
        
    except Exception as e:
        traceback.print_exc()
        return (e)

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
                ig.plot(g, layout="kk", edge_label=g.es["SPLC"], target="g.svg",bbox=(800, 400))
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
                

                #nodes
                nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in g.vs]
                # Create edges list
                edges = [{
                            "data": {
                                "source": edge.source, 
                                "target": edge.target, 
                                "splc":edge["SPLC"],
                                "in_main_path": str(edge.index in longest_edge_path).lower()
                            }
                        } for edge in g.es if edge["SPLC"] > 1]

                
                #mpa nodes
                mpa_nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in main_path.vs]
                # Create edges list
                mpa_edges = [{"data": {"source": edge.source, "target": edge.target}} for edge in main_path.es]

                #print("Longest path:", longest_path)
                #print("edge:", longest_edge_path)
                #print("Longest path length:", max_length)
                #print (main_path)
                #ig.plot(main_path, layout="kk", edge_label=main_path.es["SPLC"], target="main_path.svg",bbox=(1920, 1080)) 

                #update the name to trim everything after a ) character is found
                for node in mpa_nodes:
                    s = node['data']['name']
                    
                    if ')' in s:
                        name = s.split(')')[0] + ')'
                    else:
                        name = s
                    node['data']['name'] = name
                    
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
                #print("Longest path:", longest_path)
                #print("edge:", longest_edge_path)
                #print("Longest path length:", max_length)
                #print (main_path)
                #ig.plot(main_path, layout="kk", edge_label=main_path.es["SPC"], target="main_path.svg",bbox=(3000, 3000))

                #complete graph nodes
                nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in g.vs]
                # Create edges list
                edges = [{"data": {"source": edge.source, "target": edge.target, "spc":edge["SPC"], "in_main_path": str(edge.index in longest_edge_path).lower()}} for edge in g.es if edge["SPC"] > 1]

                #mpa nodes
                mpa_nodes = [{"data": {"id": v.index, "tipo": v["tipo"], "name":v["name"], "label": v["name"]}} for v in main_path.vs]
                # Create edges list
                mpa_edges = [{"data": {"source": edge.source, "target": edge.target}} for edge in main_path.es]

                #update the name to trim everything after a ) character is found
                for node in mpa_nodes:
                    s = node['data']['name']
                    
                    if ')' in s:
                        name = s.split(')')[0] + ')'
                    else:
                        name = s
                    node['data']['name'] = name

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


def longest_path_spc(graph, vertex, visited, path, edge_path, path_length, max_path, max_edge_path, max_length):
    visited[vertex] = True
    path.append(vertex)

    for neighbor in graph.neighbors(vertex, mode=ig.OUT):
        edge = graph.get_eid(vertex, neighbor, directed=True, error=False)
        if edge != -1:
            edge_spc = graph.es[edge]['SPC']
            if not visited[neighbor]:
                path_length += edge_spc
                edge_path.append(edge)
                max_path, max_edge_path, max_length = longest_path_spc(graph, neighbor, visited, path, edge_path, path_length, max_path, max_edge_path, max_length)
                path_length -= edge_spc
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
        
        all_paths = []
        for ps in primary_sources:
            for s in sinks:
                paths = g.get_all_simple_paths(ps, s, mode="out")
                all_paths.extend(paths)
        
        edge_list = g.get_edgelist()
        
        for index, edge in enumerate(edge_list):
            # Filter paths that include the specific edge
            paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
            #print("caminhos com o escolhido = ",len(paths_with_edge))
            g.es[index]["SPC"] = len(paths_with_edge)
        
        ''' OLD VERSION really slow
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


            TEST VERSION
            sinks = [v.index for v in g.vs if g.outdegree(v.index) == 0]
            primary_sources = [v.index for v in g.vs if g.indegree(v.index) == 0]
            
            # Create a dictionary to store all paths from each source to each sink
            paths_dict = {(ps, s): g.get_all_simple_paths(ps, s, mode="out") for ps in primary_sources for s in sinks}
            
            all_paths = [path for paths in paths_dict.values() for path in paths]
            
            edge_list = g.get_edgelist()
            
            for index, edge in enumerate(edge_list):
                # Filter paths that include the specific edge
                paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
                g.es[index]["SPC"] = len(paths_with_edge)
            '''

def splc(g):
    sinks = [v.index for v in g.vs if g.outdegree(v.index) == 0]
    edge_list = g.get_edgelist()

    # Cache for paths
    paths_cache = defaultdict(list)

    # Precompute unique predecessors for each node
    predecessors_cache = {}
    for v_index in range(g.vcount()):
        predecessors = []
        find_all_predecessors(g, v_index, predecessors)
        unique_pred = list(set(p.index for p in predecessors))
        predecessors_cache[v_index] = unique_pred

    # Main loop over edges
    for index, edge in enumerate(edge_list):
        all_paths = []
        current_node = edge[1]  # destination node
        
        # Fetch precomputed unique predecessors
        unique_pred = predecessors_cache[current_node]

        # Calculate or fetch cached paths
        for pred in unique_pred:
            pred_sink_key = (pred, "sinks")
            if pred_sink_key not in paths_cache:
                for s in sinks:
                    paths = g.get_all_simple_paths(pred, s, mode="out")
                    paths_cache[pred_sink_key].extend(paths)

                all_paths.extend(paths_cache[pred_sink_key])
            else:
                all_paths.extend(paths_cache[pred_sink_key])

        # Filtering paths containing the current edge
        paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]

        # Update SPLC value
        g.es[index]["SPLC"] = len(paths_with_edge)
   
    '''
    OLD VERSION , VERY SLOW DUE TO NO CACHE
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
            #print("todos caminhos", all_paths)  ps-72 sink-373
        
        paths_with_edge = [path for path in all_paths if edge in zip(path, path[1:])]
        #print("caminhos com o escolhido = ",len(paths_with_edge))            
        g.es[index]["SPLC"] = len(paths_with_edge)'''


def find_all_predecessors(g, node, predecessors):
    pred = g.vs[node].predecessors()
    if len(pred) == 0:
        return predecessors
    else:
        predecessors.extend(pred)
        for p in pred:
            find_all_predecessors(g, p.index, predecessors)


