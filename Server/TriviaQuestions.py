import random

class TriviaQuestions:
    def __init__(self):
        self.questions = [
            {"question": "True or false: Mount Hermon is the highest point in Israel.", "answer": True},
            {"question": "True or false: The Jordan River is the longest river in Israel.", "answer": True},
            {"question": "True or false: The Negev Desert covers more than half of Israel's land area.", "answer": True},
            {"question": "True or false: Israel has no access to the Red Sea.", "answer": False},
            {"question": "True or false: The Dead Sea is the lowest point on Earth's surface.", "answer": True},
            {"question": "True or false: Mount Carmel is located in the southern part of Israel.", "answer": False},
            {"question": "True or false: The Sea of Galilee is a freshwater lake.", "answer": True},
            {"question": "True or false: The Yarkon River is in Jerusalem.", "answer": False},
            {"question": "True or false: Israel shares a border with Lebanon.", "answer": True},
        ]
        self.current_question = None

    def get_random_question(self):
        self.current_question = random.choice(self.questions)
        return self.current_question

    def check_answer(self, answer):
        if self.current_question is None:
            return False
        # Assuming 'T', 'Y', '1' are considered true, and 'F', 'N', '0' are false
        is_true_answer = answer.upper() in ['T', 'Y', '1']
        return is_true_answer == self.current_question["answer"]
