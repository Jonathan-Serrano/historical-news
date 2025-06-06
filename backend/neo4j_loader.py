import os
import pandas as pd
from dotenv import load_dotenv
from neo4j.exceptions import ClientError
from tqdm import tqdm
from langchain_neo4j import Neo4jGraph
import ast

load_dotenv()

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")


neo4j_graph = Neo4jGraph(
    url=url, username=username, password=password, refresh_schema=False
)
embedding_dimension = 768

def create_constraints(graph: Neo4jGraph):
    constraints = [
        ("user_id_unique", "User", "id"),
        ("topic_name_unique", "Topic", "name"),
        ("channel_title_unique", "Channel", "title"),
        ("article_link_unique", "Article", "link"),
    ]

    for name, label, property in constraints:
        cypher = f"""
        CREATE CONSTRAINT {name} IF NOT EXISTS
        FOR (n:{label})
        REQUIRE n.{property} IS UNIQUE
        """
        graph.query(cypher)

def insert_csv_data(data: pd.DataFrame):
    for index, row in tqdm(
        data.iterrows(), total=len(data), desc="Inserting Data", unit="row"
    ):
        topic_names = row["assigned_topic_name"].split(", ") if row["assigned_topic_name"] else []
        params = {
            "article_link": row["url"],
            "article_title": row["title"],
            "article_description": row["body"],
            "pub_date": row["timestamp"],
            "article_embedding": row["embedding"],
        }

        # Updated query to save article with its embedding
        query_article_and_embedding = """
            MERGE (article:Article {link: $article_link})
            ON CREATE SET 
                article.title = $article_title, 
                article.description = $article_description,
                article.pubDate = datetime($pub_date)

            WITH article, $article_embedding AS embedding
            CALL db.create.setNodeVectorProperty(article, 'embedding', embedding)
            RETURN article
        """
        neo4j_graph.query(query_article_and_embedding, params)

        # Ensure that an index exists on the article embeddings
        try:
            neo4j_graph.query(
                """
                CREATE VECTOR INDEX article_vectors IF NOT EXISTS
                FOR (n:Article)
                ON (n.embedding)
                OPTIONS {
                indexConfig: {
                    `vector.dimensions`: $dimension,
                    `vector.similarity_function`: 'cosine'
                  }
                }
                """,
                {"dimension": embedding_dimension},
            )
        except ClientError as e:
            if "Index already exists" not in str(e):
                print(f"Error creating index: {e}")

        query_channel = """
        MERGE (channel:Channel {title: $channel_title})
        """

        neo4j_graph.query(
            query_channel,
            {
                "channel_title": row["source"],
            },
        )

        # Article comes from Channel
        query_comes_from = """
        MATCH (article:Article {link: $article_link}), (channel:Channel {title: $channel_title})
        MERGE (article)-[:COMES_FROM]->(channel)
        """
        neo4j_graph.query(
            query_comes_from,
            {"article_link": row["url"], "channel_title": row["source"]},
        )

        for topic_name in topic_names:
            query_topic = """
            MERGE (topic:Topic {name: $topic_name})
            """
            neo4j_graph.query(query_topic, {"topic_name": topic_name})

            # Create relationship: Article is RELATED_TO Topic
            query_related_to = """
            MATCH (article:Article {link: $article_link}), (topic:Topic {name: $topic_name})
            MERGE (article)-[:RELATED_TO]->(topic)
            """
            neo4j_graph.query(
                query_related_to,
                {"article_link": row["url"], "topic_name": topic_name},
            )


def insert_topic_data(topic_df: pd.DataFrame):
    for index, row in topic_df.iterrows():
        # Skip if Generated_Name is missing
        if pd.isna(row["Generated_Name"]):
            continue

        query = """
        MERGE (topic:Topic {name: $generated_name})
        SET topic.topicId = $topic_id,
            topic.internalName = $internal_name,
            topic.keywords = $keywords
        """
        neo4j_graph.query(
            query,
            {
                "generated_name": row["Generated_Name"],
                "topic_id": int(row["Topic"]),
                "internal_name": row["Name"],
                "keywords": (
                    eval(row["Representation"])
                    if isinstance(row["Representation"], str)
                    else []
                ),
            },
        )
        
csv_data = pd.read_csv("data.csv")
csv_data = csv_data.fillna("")
csv_data["timestamp"] = pd.to_datetime(csv_data["timestamp"], errors="coerce", utc=True)
csv_data["embedding"] = csv_data["embedding"].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
)
print("CSV data shape:", csv_data.shape)
create_constraints(neo4j_graph)
insert_csv_data(csv_data)

topic_names = pd.read_csv("topic_data.csv")
topic_names = topic_names.fillna("")
insert_topic_data(topic_names)

print("Data inserted into Neo4j successfully!")
