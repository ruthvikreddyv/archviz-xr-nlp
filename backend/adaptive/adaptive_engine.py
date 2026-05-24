def get_learning_level(score):

    if score < 40:
        return {
            "level": "beginner",
            "difficulty": "easy",
            "hints": True
        }

    elif score < 70:
        return {
            "level": "intermediate",
            "difficulty": "medium",
            "hints": False
        }

    return {
        "level": "advanced",
        "difficulty": "hard",
        "hints": False
    }