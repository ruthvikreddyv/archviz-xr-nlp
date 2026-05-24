def calculate_score(quiz, answers):

    score = 0

    for i in range(len(quiz)):

        if answers[i] == quiz[i]["answer"]:
            score += 1

    percentage = (score / len(quiz)) * 100

    return percentage