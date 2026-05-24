def generate_tutor_response(question, level):

    if level == "beginner":

        return {
            "answer": "Encoder converts input tokens into contextual representations in a simple way.",
            "difficulty": "easy",
            "next_topic": "Self Attention"
        }

    elif level == "intermediate":

        return {
            "answer": "Encoder generates contextual embeddings using self-attention mechanisms.",
            "difficulty": "medium",
            "next_topic": "Multi-Head Attention"
        }

    return {
        "answer": "Encoder produces high-dimensional contextual token embeddings for sequence understanding.",
        "difficulty": "hard",
        "next_topic": "Cross Attention"
    }