from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_cors import CORS
from langchain_neo4j import Neo4jGraph
from neo4j.time import DateTime as Neo4jDateTime
from datetime import datetime
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.prompts import ChatPromptTemplate
from tqdm import tqdm

load_dotenv()

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

neo4j_graph = Neo4jGraph(
    url=url, username=username, password=password, refresh_schema=False
)

app = Flask(__name__)
api = Api(app)
CORS(app)


current_date = datetime(2024, 5, 5, 14, 30)


class DateResource(Resource):
    def get(self):
        return make_response(jsonify({"current_date": current_date.isoformat()}), 200)

    def put(self):
        data = request.json
        new_date = data.get("current_date")

        if new_date:
            try:
                # Validate and parse the new date
                parsed_date = datetime.fromisoformat(new_date)
                global current_date
                current_date = parsed_date
                return make_response(
                    jsonify({"message": "Date updated successfully!"}), 200
                )
            except ValueError:
                return make_response(jsonify({"message": "Invalid date format!"}), 400)
        else:
            return make_response(jsonify({"message": "No date provided!"}), 400)

api.add_resource(DateResource, "/date")

class UserResource(Resource):
    def post(self):
        # Create user node
        data = request.json
        user_id = data.get("id")
        name = data.get("name")
        base_understanding = data.get("base_understanding", "Beginner")
        join_date = data.get("join_date", datetime.now().isoformat())

        # Insert into Neo4j
        query = """
        MERGE (user:User {id: $user_id})
        SET user.name = $name,
            user.base_understanding = $base_understanding,
            user.join_date = datetime($join_date)
        """
        neo4j_graph.query(
            query,
            {
                "user_id": user_id,
                "name": name,
                "base_understanding": base_understanding,
                "join_date": join_date,
            },
        )
        print(f"User {name} created with ID {user_id}.")
        return make_response(jsonify({"message": "User created successfully!"}), 201)

    def put(self):
        # Update user node
        data = request.json
        user_id = data.get("id")
        name = data.get("name")
        base_understanding = data.get("base_understanding")
        join_date = data.get("join_date")

        # Update query for Neo4j
        query = """
        MATCH (user:User {id: $user_id})
        SET user.name = $name,
            user.base_understanding = $base_understanding,
            user.join_date = datetime($join_date)
        """
        neo4j_graph.query(
            query,
            {
                "user_id": user_id,
                "name": name,
                "base_understanding": base_understanding,
                "join_date": join_date,
            },
        )

        return make_response(jsonify({"message": "User updated successfully!"}), 200)

    def get(self):
        user_id = request.args.get("id")
        # Query to retrieve user information and their subscribed interests with levels
        query = """
        MATCH (user:User {id: $user_id})
        OPTIONAL MATCH (user)-[:SUBSCRIBED_TO]->(topic:Topic)
        OPTIONAL MATCH (user)-[r:LEVEL_OF_UNDERSTANDING]->(topic)
        RETURN
            user.id AS id, 
            user.name AS name,
            user.base_understanding AS base_understanding,
            user.join_date AS join_date,
            collect({topic: topic.name, level: r.level}) AS interests
        """

        result = neo4j_graph.query(query, {"user_id": user_id})
        if result and len(result) > 0:
            user = result[0]
            if hasattr(user["join_date"], "to_native"):
                user["join_date"] = user["join_date"].to_native().isoformat()

            return make_response(jsonify(user), 200)
        else:
            return make_response(jsonify({"message": "User not found!"}), 201)


class UserInterestResource(Resource):
    def post(self, user_id):
        # Add user interest
        data = request.json
        topic_name = data.get("topic_name")
        level = data.get("level", "Beginner")

        # Add relationship: User SUBSCRIBED_TO Topic
        query = """
        MATCH (user:User {id: $user_id}), (topic:Topic {name: $topic_name})
        MERGE (user)-[:SUBSCRIBED_TO]->(topic)
        """
        neo4j_graph.query(query, {"user_id": user_id, "topic_name": topic_name})

        # Add level of understanding relationship
        query_level = """
        MATCH (user:User {id: $user_id}), (topic:Topic {name: $topic_name})
        MERGE (user)-[r:LEVEL_OF_UNDERSTANDING]->(topic)
        SET r.level = $level
        """
        neo4j_graph.query(
            query_level, {"user_id": user_id, "topic_name": topic_name, "level": level}
        )

        return make_response(jsonify({"message": "Interest added successfully!"}), 201)

    def delete(self, user_id):
        # Remove user interest
        data = request.json
        topic_name = data.get("topic_name")

        # Remove subscription relationship
        query = """
        MATCH (user:User {id: $user_id})-[r:SUBSCRIBED_TO]->(topic:Topic {name: $topic_name})
        DELETE r
        """
        neo4j_graph.query(query, {"user_id": user_id, "topic_name": topic_name})

        return make_response(jsonify({"message": "Interest removed successfully!"}), 200)


class UserArticleResource(Resource):
    def post(self, user_id):
        # Save article for later
        data = request.json
        article_link = data.get("article_link")

        # Add relationship: User SAVED_FOR_LATER Article
        query = """
        MATCH (user:User {id: $user_id}), (article:Article {link: $article_link})
        MERGE (user)-[:SAVED_FOR_LATER]->(article)
        """
        neo4j_graph.query(query, {"user_id": user_id, "article_link": article_link})

        return make_response(jsonify({"message": "Article saved successfully!"}), 201)

    def delete(self, user_id):
        # Remove saved article
        data = request.json
        article_link = data.get("article_link")

        # Remove saved article relationship
        query = """
        MATCH (user:User {id: $user_id})-[r:SAVED_FOR_LATER]->(article:Article {link: $article_link})
        DELETE r
        """
        neo4j_graph.query(query, {"user_id": user_id, "article_link": article_link})

        return make_response(jsonify({"message": "Article removed from saved list!"}), 200)

class InterestResource(Resource):
    def get(self):
        # Get all topics
        query = """
        MATCH (topic:Topic)
        RETURN topic.name AS name
        """
        result = neo4j_graph.query(query)
        topics = [record["name"] for record in result]
        return make_response(jsonify(topics), 200)
    

class SummarizeAllArticlesResource(Resource):
    def get(self):
        summaries = request.args.get("combined_summaries")  
        topic = request.args.get("topic")
        if not summaries:
            return make_response(jsonify({"error": "No summaries provided"}), 400)
        if not topic:
            return make_response(jsonify({"error": "No topic provided"}), 400)
        # Generate meta-summary
        summary_ret = meta_summary_chain.invoke({"summaries": summaries, "topic": topic}).content
        
        return summary_ret


api.add_resource(UserResource, "/user")
api.add_resource(UserInterestResource, "/user/<string:user_id>/interest")
api.add_resource(UserArticleResource, "/user/<string:user_id>/article")
api.add_resource(InterestResource, "/interests")
api.add_resource(SummarizeAllArticlesResource, "/summarize_all_articles")


# gives 10 articles related to the topic
class ArticleTopicResource(Resource):
    def get(self):
        topic = request.args.get('topic')
        level = request.args.get('level')
        before_date = request.args.get('before_date')

        if not topic or not before_date or not level:
            return make_response(jsonify({"error": "Missing 'topic' or 'before_date' or 'level' parameter"}), 400)
        try:
            # Ensure before_date is a valid ISO format date string
            datetime.strptime(before_date, '%Y-%m-%d')
        except ValueError:
            return make_response(jsonify({"error": "'before_date' must be in 'YYYY-MM-DD' format"}), 400)

        articles = get_related_articles(topic, before_date, level)
        return make_response(jsonify({"articles": articles}))

api.add_resource(ArticleTopicResource, "/articles/topic")

llm = ChatOllama(model="llama3.2", temperature=0.7, num_predict=256)
summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are generating concise and accurate summaries based on the information found in the text and a provided topic",
        ),
        ("human", "Generate a summary of the following input: {question} based on the topic of {topic} and explain it at a {level} level. Return just the summary.\nSummary:"),
    ]
)
summary_chain = summary_prompt | llm

meta_summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are generating a meta-summary from multiple summaries about a given topic.",
        ),
        (
            "human",
            "Generate an overall summary of the following summaries: {summaries} based on the topic of {topic}. Do not include any extra text or headings—just return the summary.:",
        ),
    ]
)
meta_summary_chain = meta_summary_prompt | llm

embeddings = OllamaEmbeddings(model="nomic-embed-text")
embedding_dimension = 4096
def get_related_articles(topic: str, before_date: str, level: str):
    query = """
        WITH $topic_embedding AS topic_vector
        CALL db.index.vector.queryNodes('article_vectors', 5, topic_vector) YIELD node, score
        RETURN node.link AS link, node.title AS title, node.description AS description,
            node.pubDate AS pubDate, score
        ORDER BY score DESC
        LIMIT 5;
    """

    random_query = """
        MATCH (article:Article)-[:RELATED_TO]->(topic:Topic {name: $topic})
        WHERE article.pubDate < datetime($before_date)
        RETURN article.link AS link, article.title AS title, article.description AS description,
               article.pubDate AS pubDate, 0 AS score
        ORDER BY rand()
        LIMIT 5
    """

    result = neo4j_graph.query(
        query,
        {
            "topic_embedding": embeddings.embed_query(topic),
            "before_date": before_date,
        },
    )

    articles = []
    for record in tqdm(result, desc="Processing articles", unit="article"):
        summary = summary_chain.invoke({"question": record["title"] + record["description"], "topic": topic, "level": level}).content
        articles.append(
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                "score": record["score"],
                "summary": summary,
            }
        )

    result = neo4j_graph.query(
        random_query,
        {
            "topic": topic,
            "before_date": before_date,
        },
    )
    for record in tqdm(result, desc="Processing articles", unit="article"):
        summary = summary_chain.invoke(
            {"question": record["title"] + record["description"], "topic": topic, "level": level}
        ).content
        articles.append(
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                "score": record["score"],
                "summary": summary,
            }
        )
    return articles


if __name__ == "__main__":
    app.run(debug=True)
