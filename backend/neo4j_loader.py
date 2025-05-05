import os
import pandas as pd
from dotenv import load_dotenv
from neo4j.exceptions import ClientError
from tqdm import tqdm
from langchain_neo4j import Neo4jGraph
from langchain_text_splitters import TokenTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.prompts import ChatPromptTemplate

load_dotenv()

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")


neo4j_graph = Neo4jGraph(
    url=url, username=username, password=password, refresh_schema=False
)

embeddings = OllamaEmbeddings(model="nomic-embed-text")
embedding_dimension = 768
# llm = ChatOllama(model="mistral:instruct", temperature=0.7, num_predict=256)
# summary_prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are generating concise and accurate summaries based on the information found in the text.",
#         ),
#         ("human", "Generate a summary of the following input: {question}\nSummary:"),
#     ]
# )

# summary_chain = summary_prompt | llm

def create_constraints(graph: Neo4jGraph):
    constraints = [
        ("user_id_unique", "User", "id"),
        # ("author_name_unique", "Author", "name"),
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

        # # Merge Channel node
        # query_channel = """
        # MERGE (channel:Channel {title: $channel_title})
        # ON CREATE SET channel.rss_link = $rss_link, channel.description = $channel_description
        # """
        # neo4j_graph.query(
        #     query_channel,
        #     {
        #         "channel_title": row["channel_title"],
        #         "rss_link": row["source"],
        #         "channel_description": row["channel_description"],
        #     },
        # )

        # Using f-strings for cleaner string concatenation
        article_text = (
            f"{row.get('title', '')} {row.get('body', '')}".strip()
        )

        # summary = summary_chain.invoke({"question": article_text}).content
        # summary_embedding = embeddings.embed_query(summary)

        article_embedding = embeddings.embed_query(article_text)
        params = {
            "article_link": row["url"],
            "article_title": row["title"],
            "article_description": row["body"],
            "pub_date": row["timestamp"],
            "article_embedding": article_embedding,
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

        # # Merge Author node
        # query_author = """
        # MERGE (author:Author {name: $author_name})
        # """
        # neo4j_graph.query(query_author, {"author_name": row["author"]})

        # # Article is written by Author
        # query_written_by = """
        # MATCH (article:Article {link: $article_link}), (author:Author {name: $author_name})
        # MERGE (article)-[:WRITTEN_BY]->(author)
        # """
        # neo4j_graph.query(
        #     query_written_by,
        #     {"article_link": row["link"], "author_name": row["author"]},
        # )

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
print("CSV data shape:", csv_data.shape)
create_constraints(neo4j_graph)
insert_csv_data(csv_data)

topic_names = pd.read_csv("topic_data.csv")
topic_names = topic_names.fillna("")
insert_topic_data(topic_names)

print("Data inserted into Neo4j successfully!")
