import os
from langchain.chains import ConversationChain
from langchain_community.llms import Ollama
from backend.neo4j_loader import get_context

llm = Ollama(model=os.getenv("OLLAMA_MODEL"))


def generate_response(user_input):
    grounding_data = get_context(user_input)
    full_input = f"User: {user_input}\n\nRelevant context:\n{grounding_data}"

    chain = ConversationChain(llm=llm)
    return chain.run(full_input)
