from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_cors import CORS
from langchain_neo4j import Neo4jGraph
from neo4j.time import DateTime as Neo4jDateTime
from datetime import datetime
from dotenv import load_dotenv
import os

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
        MATCH (user:User {id: $user_id})-[:SUBSCRIBED_TO]->(topic:Topic)
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
            return make_response(jsonify({"message": "User not found!"}), 404)


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

api.add_resource(UserResource, "/user")
api.add_resource(UserInterestResource, "/user/<string:user_id>/interest")
api.add_resource(UserArticleResource, "/user/<string:user_id>/article")
api.add_resource(InterestResource, "/interests")

if __name__ == "__main__":
    app.run(debug=True)
