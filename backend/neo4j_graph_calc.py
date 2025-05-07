import os
import pandas as pd
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

neo4j_graph = Neo4jGraph(
    url=url, username=username, password=password, refresh_schema=False
)

def generate_similarity(graph_name):
    query = """
    CALL gds.nodeSimilarity.write($graphName, {
        writeRelationshipType: 'SIMILAR',
        writeProperty: 'score'
    })
    YIELD nodesCompared, relationshipsWritten
    """
    neo4j_graph.query(query, {"graphName": graph_name})

def generate_seed_topic(graph_name, seed_size=10):
    query = """
        CALL gds.influenceMaximization.celf.write($graphName, {
            writeProperty: 'celfSpread',
            seedSetSize: $seedSize,
            relationshipTypes: ['RELATED_TO']
        })
        YIELD nodePropertiesWritten;
    """
    neo4j_graph.query(query, {"graphName": graph_name, "seedSize": seed_size})
    return True


def register_graph(graph_name: str):
    query = """
        CALL gds.graph.project(
        $graphName,
        ['Article', 'Topic', 'Channel'],
        {
            RELATED_TO: {
            type: 'RELATED_TO',
            orientation: 'UNDIRECTED'
            },
            COMES_FROM: {
            type: 'COMES_FROM',
            orientation: 'UNDIRECTED'
            }
        }
        )
        YIELD graphName, nodeCount, relationshipCount;
    """
    neo4j_graph.query(query, {"graphName": graph_name})
    return True

graph_name = "newsGraph"
register_graph(graph_name)
generate_seed_topic(graph_name)
generate_similarity(graph_name)
