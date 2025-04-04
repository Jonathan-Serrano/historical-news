import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)


def get_context(query):
    with driver.session() as session:
        result = session.run(
            "MATCH (n) WHERE n.name CONTAINS $q RETURN n LIMIT 5", q=query
        )
        return "\n".join([str(record["n"]) for record in result])
