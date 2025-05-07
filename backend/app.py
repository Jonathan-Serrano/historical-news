from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from flask_cors import CORS
from langchain_neo4j import Neo4jGraph
from neo4j.time import DateTime as Neo4jDateTime
from datetime import datetime
from dotenv import load_dotenv
import os
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_distances
import numpy as np

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

@app.route("/topic/get_seed", methods=["GET"])
def get_topic_seed():
    query = """
    MATCH (n:Topic)
    WHERE n.celfSpread IS NOT NULL AND n.celfSpread <> 0
    RETURN n.name AS name, n.celfSpread AS spread
    ORDER BY spread DESC, name ASC
    """
    result = neo4j_graph.query(query)
    topics = [{"name": record["name"]} for record in result]
    return make_response(jsonify(topics), 200)


@app.route("/topic/<string:topic_name>", methods=["GET"])
def get_related_topics(topic_name):
    user_id = request.args.get("id")
    if not user_id:
        return make_response(jsonify({"error": "Missing user_id"}), 400)

    query = """
    MATCH (u:User {id: $user_id})-[:SUBSCRIBED_TO]->(subscribed:Topic)
    WITH u, collect(subscribed.name) AS subscribed_names
    MATCH (t:Topic {name: $topic_name})-[s:SIMILAR]-(other:Topic)
    WHERE NOT other.name IN subscribed_names
    RETURN other.name AS name, s.score AS score
    ORDER BY s.score DESC
    LIMIT 5
    """
    result = neo4j_graph.query(
        query,
        {
            "topic_name": topic_name,
            "user_id": user_id,
        },
    )
    
    seen = set()
    topics = []
    for record in result:
        if record["name"] not in seen:
            seen.add(record["name"])
            topics.append({"name": record["name"], "score": record["score"]})
            
    return make_response(jsonify(topics), 200)


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
    
    def get(self, user_id):
        # Get all topics the user is subscribed to
        query = """
        MATCH (user:User {id: $user_id})-[:SUBSCRIBED_TO]->(topic:Topic)
        OPTIONAL MATCH (user)-[r:LEVEL_OF_UNDERSTANDING]->(topic)
        RETURN topic.name AS name, r.level AS level
        """
        result = neo4j_graph.query(query, {"user_id": user_id})
        topics = [
            {"topic": record["name"], "level": record["level"]} for record in result
        ]
        return make_response(jsonify(topics), 200)


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
    def post(self):
        data = request.get_json()
        topic = data.get("topic")
        summaries = data.get("combined_summaries")
        if not summaries:
            return make_response(jsonify({"error": "No summaries provided"}), 400)
        if not topic:
            return make_response(jsonify({"error": "No topic provided"}), 400)
        # Generate meta-summary
        role = "A journalist whose sole job is to write a summary of multiple articles and want to make sure that the summary is accurate and informative" 

        summary_ret = meta_summary_chain.invoke({"summaries": summaries, "topic": topic, "role": role}).content
        
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

llm = ChatOllama(model="mistral", temperature=0.7, num_predict=256)

class ArticleAnalysis(BaseModel):
    summary: str
    intent: str

parser = JsonOutputParser(pydantic_object=ArticleAnalysis)

summary_prompt = ChatPromptTemplate(
    messages=[
        (
            "system",
            "You are an expert media analyst generating concise and accurate summaries based on the information found in the text and a provided topic",
        ),
        (
            "human",
            """
            You will perform two tasks based on the following input:

            {question}

            1. Generate a summary based on the topic of {topic}:

            2. Classify the intent as one of:
               - Inform
               - Persuade
               - Manipulate
               - Mislead
               - Satirize

            {format_instructions}
        """,
        ),
    ],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)
summary_chain = summary_prompt | llm | parser

meta_summary_prompt = ChatPromptTemplate(
    [
        (
            "system",
            "You are a {role}. You are generating an overall summary from multiple summaries about a given topic.",
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
    if (level == "Beginner"):
        level = "middle schooler who is just starting to learn about the topic and wants to understand the basics"
    elif (level == "Intermediate"):
        level = "graduate student who has some knowledge about the topic and wants to learn more advanced concepts"
    elif (level == "Expert"):
        level = "Industry profession in the domain who is well-versed in the topic and wants to explore a deeper understanding"
    role = "A journalist whose sole job is to make summaries of articles and want to make sure that the summary is accurate and informative" 
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
        response_dict = summary_chain.invoke({"question": record["title"] + record["description"], "topic": topic, "level": level})
        articles.append(
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                "score": record["score"],
                "summary": response_dict["summary"],
                "intent": response_dict["intent"],
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
        response_dict = summary_chain.invoke(
            {"question": record["title"] + record["description"], "topic": topic, "level": level}
        )
        articles.append(
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                "score": record["score"],
                "summary": response_dict["summary"],
                "intent": response_dict["intent"],
            }
        )
    return articles

class HistoryResource(Resource):
    def post(self, user_id, topic):
        data = request.json
        date = data.get("current_date")
        
        # Retrieve all article embeddings from given topic the tiven user is subscribed to
        query = """
        MATCH (user:User {id: $user_id})-[:SUBSCRIBED_TO]->(topic:Topic)<-[:RELATED_TO]-(article:Article)
        WHERE topic.name = $topic
        AND article.pubDate < datetime($date)
        RETURN article.embedding AS embedding, elementId(article) as elementId, article.link AS link,
               article.title AS title, article.description AS description, article.pubDate AS pubDate
        ORDER BY article.pubDate DESC
        """
        result = neo4j_graph.query(query, {"user_id": user_id, "topic": topic, "date": date})
        embeddings = np.array([article["embedding"] for article in result])
        
        # print length of result
        print(f"Number of articles retrieved: {len(result)}")
        print (f"Embeddings shape: {embeddings.shape}")

        select_indices = select_dissimilar_embeddings(embeddings, 25) # k = 25 = history size limit
        selected_articles = [result[i] for i in select_indices]

        # Add LAST_QUERY relationship for each selected article's topic
        query = """
        UNWIND $articles AS article
        MATCH (user:User {id: $user_id})
        MATCH (a:Article)-[:RELATED_TO]->(topic:Topic {name: $topic})
        WHERE elementId(a) = article.elementId
        MERGE (user)-[r:LAST_QUERY]->(a)
        SET r.lastQueriedAt = $date
        MERGE (user)-[r2:LAST_QUERY]->(topic)
        SET r2.lastQueriedAt = $date
        """
        neo4j_graph.query(query, {
            "user_id": user_id,
            "articles": selected_articles,  # Each dict should have "elementId" key
            "topic": topic,
            "date": date
        })

        articles = [
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S")
            }
            for record in selected_articles
        ]

        return make_response(jsonify(articles), 201)

    def get(self, user_id, topic):
        # Retrieve all articles related to topic that was last queried by the user
        query = """
        MATCH (user:User {id: $user_id})-[:LAST_QUERY]->(topic:Topic {name: $topic})<-[:RELATED_TO]-(article:Article)
        MATCH (user)-[:LAST_QUERY]->(article)
        RETURN article.link AS link, article.title AS title, article.description AS description, article.pubDate AS pubDate
        """

        history = neo4j_graph.query(query, {"user_id": user_id, "topic": topic})
        articles = [
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for record in history
        ]

        return make_response(jsonify(articles), 201)
    
    def put(self, user_id, topic):
        data = request.json
        date = data.get("current_date")

        # get the date of the last query for the given topic
        query = """
        MATCH (user:User {id: $user_id})-[r:LAST_QUERY]->(topic:Topic {name: $topic})
        RETURN r.lastQueriedAt AS lastQueriedAt
        """
        result = neo4j_graph.query(query, {"user_id": user_id, "topic": topic})
        if result and len(result) > 0:
            prev_date = result[0]["lastQueriedAt"]
        else:
            return make_response(jsonify({"error": "No previous date found"}), 404)
        
        # get all relevant articles that were published after the last query date
        query = """
        MATCH (user:User {id: $user_id})-[:SUBSCRIBED_TO]->(topic:Topic)<-[:RELATED_TO]-(article:Article)
        WHERE topic.name = $topic
        AND article.pubDate > datetime($prev_date)
        RETURN article.embedding AS embedding, elementId(article) as elementId, article.link AS link,
               article.title AS title, article.description AS description, article.pubDate AS pubDate
        ORDER BY article.pubDate DESC
        """
        new_result = neo4j_graph.query(query, {"user_id": user_id, "topic": topic, "prev_date": prev_date})
        new_embeddings = np.array([article["embedding"] for article in new_result])

        # if there are no new articles
        if(len(new_embeddings) == 0):
            articles = [
                {
                    "link": record["link"],
                    "title": record["title"],
                    "description": record["description"],
                    "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                } for record in new_history
            ]
            return make_response(jsonify(articles), 202)


        # get the articles from the history that are related to the topic
        query = """
        MATCH (user:User {id: $user_id})-[:LAST_QUERY]->(topic:Topic {name: $topic})<-[:RELATED_TO]-(article:Article)
        RETURN article.embedding AS embedding, elementId(article) as elementId, article.link AS link, article.title AS title, article.description AS description, article.pubDate AS pubDate
        """
        history = neo4j_graph.query(query, {"user_id": user_id, "topic": topic})
        history_embeddings = np.array([article["embedding"] for article in history])

        all_articles = history + new_result
        all_embeddings = np.concatenate((history_embeddings, new_embeddings), axis=0)

        dissimilar_indices = select_dissimilar_embeddings(all_embeddings, 25) # k = 25 = history size limit
        new_history = [all_articles[i] for i in dissimilar_indices]

        # Add LAST_QUERY relationship for each selected article's topic
        query = """
        UNWIND $articles AS article
        MATCH (user:User {id: $user_id})
        MATCH (a:Article)-[:RELATED_TO]->(topic:Topic {name: $topic})
        WHERE elementId(a) = article.elementId
        MERGE (user)-[r:LAST_QUERY]->(a)
        SET r.lastQueriedAt = $date
        MERGE (user)-[r2:LAST_QUERY]->(topic)
        SET r2.lastQueriedAt = $date
        """
        neo4j_graph.query(query, {
            "user_id": user_id,
            "articles": new_history,  # Each dict should have "elementId" key
            "topic": topic,
            "date": date
        })

        articles = [
            {
                "link": record["link"],
                "title": record["title"],
                "description": record["description"],
                "pubDate": record["pubDate"].strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for record in new_history
        ]

        return make_response(jsonify(articles), 201)


api.add_resource(HistoryResource, "/articles/history")

def select_dissimilar_embeddings(embeddings: np.ndarray, k):
    # embeddings: numpy array of shape [N, D]
    N = embeddings.shape[0]
    if k >= N:
        return list(range(N))  # return all if k >= total nodes

    # Compute cosine distances
    distances = cosine_distances(embeddings)

    # Start with the point that is farthest from all others (max average distance)
    first_idx = np.argmax(distances.mean(axis=1))
    selected = [first_idx]
    remaining = set(range(N)) - {first_idx}

    for _ in range(k - 1):
        # For each candidate, find its distance to the closest selected point
        min_distances = [
            (idx, min(distances[idx][s] for s in selected)) for idx in remaining
        ]
        # Pick the one with the largest min distance (most dissimilar from any selected)
        next_idx = max(min_distances, key=lambda x: x[1])[0]
        selected.append(next_idx)
        remaining.remove(next_idx)

    return selected  # indices of selected embeddings


if __name__ == "__main__":
    app.run(debug=True)
