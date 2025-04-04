from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_module import generate_response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    response = generate_response(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
