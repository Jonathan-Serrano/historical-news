import os
import requests
import pandas as pd
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from datetime import datetime
import json

load_dotenv()

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")


neo4j_graph = Neo4jGraph(
    url=url, username=username, password=password, refresh_schema=False
)

def create_constraints(graph: Neo4jGraph):
    constraints = [
        ("user_id_unique", "User", "id"),
        ("author_name_unique", "Author", "name"),
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
    for index, row in data.iterrows():
        topic_names = row["assigned_topic_name"].split(", ") if row["assigned_topic_name"] else []

        # Merge User node
        query_user = """
        MERGE (user:User {id: $user_id})
        """
        neo4j_graph.query(query_user, {"user_id": row["author"]})

        # Merge Channel node
        query_channel = """
        MERGE (channel:Channel {title: $channel_title})
        ON CREATE SET channel.rss_link = $rss_link, channel.description = $channel_description
        """
        neo4j_graph.query(
            query_channel,
            {
                "channel_title": row["channel_title"],
                "rss_link": row["source"],
                "channel_description": row["channel_description"],
            },
        )

        # Merge Article node
        query_article = """
        MERGE (article:Article {link: $article_link})
        ON CREATE SET article.title = $article_title, article.description = $article_description,
                      article.pubDate = datetime($pub_date)
        """
        neo4j_graph.query(
            query_article,
            {
                "article_link": row["link"],
                "article_title": row["title"],
                "article_description": row["description"],
                "pub_date": row["pubDate"],
            },
        )

        # Merge Author node
        query_author = """
        MERGE (author:Author {name: $author_name})
        """
        neo4j_graph.query(query_author, {"author_name": row["author"]})

        # # Create relationships
        # # User subscribes to Topic
        # query_subscribe = """
        # MATCH (user:User {id: $user_id}), (topic:Topic {name: $topic_name})
        # MERGE (user)-[:SUBSCRIBED_TO]->(topic)
        # """
        # neo4j_graph.query(
        #     query_subscribe,
        #     {"user_id": row["author"], "topic_name": row["assigned_topic_name"]},
        # )

        # Article is written by Author
        query_written_by = """
        MATCH (article:Article {link: $article_link}), (author:Author {name: $author_name})
        MERGE (article)-[:WRITTEN_BY]->(author)
        """
        neo4j_graph.query(
            query_written_by,
            {"article_link": row["link"], "author_name": row["author"]},
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
                {"article_link": row["link"], "topic_name": topic_name},
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


# csv_data = pd.read_csv("data.csv")
# csv_data = csv_data.fillna("")
# csv_data["pubDate"] = pd.to_datetime(csv_data["pubDate"], errors="coerce", utc=True)
# print("CSV data shape:", csv_data.shape)
# create_constraints(neo4j_graph)
# insert_csv_data(csv_data)

topic_names = pd.read_csv("topic_data.csv")
topic_names = topic_names.fillna("")
insert_topic_data(topic_names)

print("Data inserted into Neo4j successfully!")
