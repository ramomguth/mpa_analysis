from neo4j import GraphDatabase
import igraph as ig
from igraph import Graph
import numpy as np
import pandas as pd
import json
import traceback


def save_altered_similarities(main_ref, params, user_id, project_id):
    driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("batman", "superman"))
    #ref_id = params
    #id_ref_2 = params[2]
    
    
    print("marquei como main", main_ref)
    
    #implementar o check de que quando o usuario nao finalizou as similaridades nao pode fazer o MPA 
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
    4 - primaria com primaria: Não pode, deleta a similaridade e da continue foi tratado no compare_refs
    
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
            caso = 2 -> o usuario marcou uma referencia secundaria como principal e quer alterar para primaria NAO PODE
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
                    print("para alterar", id_work_to_alter)

                    #3 deletar a ref antiga propriamente com seus relacionamentos
                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    print("deletado", ref_id)

                    #4 criar o novo relacionamento de referencia
                    query = "MATCH (t:trabalho{id:$id_work_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_work_to_alter=id_work_to_alter, main_ref=main_ref, user_id=user_id, project_id=project_id)
                    print(id_work_to_alter, "referencia", main_ref)
                    

            '''no caso 1, todas as referencias devem apontar para a principal (que eh do tipo primaria)'''
            if (caso == 1):
                for ref_id in params:
                    query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id as id_to_alter"
                    result = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id).single()
                    id_to_alter = result['id_to_alter']
                    print("para alterar ",id_to_alter)

                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    print('deletado ', ref_id)


                    query = "MATCH (t:trabalho{id:$id_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$main_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_to_alter=id_to_alter, main_ref=main_ref, user_id=user_id, project_id=project_id)
                    print(id_to_alter, "referencia", main_ref)
            
            #no caso 2 todas referencias tambem devem apontar para a referencia primaria, mesmo que o usuario tenha marcado uma secundaria como principal
            if (caso == 2):
                params.remove(ref_to_alter)
                params.append(main_ref)
                
                for ref_id in params:
                    query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id as id_to_alter"
                    result = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id).single()
                    id_to_alter = result['id_to_alter']
                    print("para alterar ",id_to_alter)
                

                    query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
                    result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
                    print('deletado ', ref_id)


                    query = "MATCH (t:trabalho{id:$id_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$ref_to_alter, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
                    result2 = tx.run(query, id_to_alter=id_to_alter, ref_to_alter=ref_to_alter, user_id=user_id, project_id=project_id)
                    print(id_to_alter, "referencia", ref_to_alter)


            '''# 2 - encontrar o trabalho da ref a ser alterada
            query = "MATCH (a:trabalho{user_id:$user_id, project_id:$project_id})-[r:referencia]->(b:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) return a.id"
            id_work_to_alter = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
            id_work_to_alter = id_work_to_alter.single().value()
            print(id_work_to_alter, "references", ref_id)

            #3 deletar a ref antiga propriamente com seus relacionamentos
            query = "MATCH (t:trabalho{id:$ref_id, user_id:$user_id, project_id:$project_id}) detach delete t"
            result1 = tx.run(query, ref_id=ref_id, user_id=user_id, project_id=project_id)
            print("deletado", ref_id)

            #4 criar o novo relacionamento de referencia
            query = "MATCH (t:trabalho{id:$id_work_to_alter, user_id:$user_id, project_id:$project_id}), (r:trabalho{id:$id_new_ref, user_id:$user_id, project_id:$project_id}) CREATE (t)-[:referencia]->(r)"
            result2 = tx.run(query, id_work_to_alter=id_work_to_alter, id_new_ref=id_new_ref, user_id=user_id, project_id=project_id)
            print("deu bom")'''

            tx.commit()
            return ("ok")
    except Exception as e:
        tx.rollback()
        traceback.print_exc()
        return(e)

    

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
        print("caminhos com o escolhido = ",len(paths_with_edge))            
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