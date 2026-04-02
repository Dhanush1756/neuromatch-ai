"""Phase 2 — Interview question generator + cover email writer"""

QUESTION_BANK = {
    "python":           ["Explain list comprehensions vs generators.",
                         "What is Python's GIL and why does it matter?",
                         "How does Python manage memory (garbage collection)?"],
    "machine learning": ["What is overfitting? How do you prevent it?",
                         "Explain bias-variance tradeoff with an example.",
                         "When would you choose Random Forest over XGBoost?"],
    "deep learning":    ["Explain backpropagation in simple terms.",
                         "What are vanishing gradients? How do you fix them?",
                         "Describe the transformer architecture."],
    "nlp":              ["What is tokenisation? Name common strategies.",
                         "Explain TF-IDF and when you'd use it.",
                         "How does BERT differ from GPT architecturally?"],
    "sql":              ["Difference between INNER JOIN and LEFT JOIN?",
                         "How do you optimise a slow SQL query?",
                         "Explain ACID properties in databases."],
    "react":            ["What are React hooks? Explain useState and useEffect.",
                         "What is the virtual DOM and why is it faster?",
                         "How does React differ from Angular?"],
    "docker":           ["Difference between a Docker image and container?",
                         "Explain Docker networking modes.",
                         "How do you manage secrets in Docker securely?"],
    "aws":              ["Difference between EC2 and AWS Lambda?",
                         "Explain S3 storage classes.",
                         "How do you design for high availability on AWS?"],
    "data analysis":    ["How do you handle missing data in a dataset?",
                         "Explain the difference between correlation and causation.",
                         "What is A/B testing and when would you use it?"],
    "git":              ["Explain git rebase vs git merge.",
                         "What is a pull request workflow?",
                         "How do you resolve merge conflicts?"],
    "kubernetes":       ["What problem does Kubernetes solve?",
                         "Explain pods, deployments, and services.",
                         "How does Kubernetes handle rolling updates?"],
    "tensorflow":       ["Difference between eager and graph execution?",
                         "Explain the Keras functional API.",
                         "How do you save and load a TensorFlow model?"],
}

GENERIC_QUESTIONS = [
    "Tell me about yourself and your background.",
    "What is your greatest technical strength?",
    "Describe a challenging project and how you overcame obstacles.",
    "Where do you see yourself in 5 years?",
    "Why are you interested in this role?",
    "How do you stay updated with new technologies?",
    "Describe your ideal work environment.",
]

def generate_interview_questions(skills: list) -> list:
    questions = list(GENERIC_QUESTIONS)
    for skill in skills:
        if skill in QUESTION_BANK:
            questions.extend(QUESTION_BANK[skill])
    seen, unique = set(), []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique[:15]


def generate_email(name: str, skills: list) -> str:
    skill_str = ", ".join(skills[:6]) if skills else "software development and problem solving"
    return f"""Subject: Application for Internship / Job Position

Dear Hiring Manager,

I hope this message finds you well. My name is {name}, and I am writing to express my strong interest in joining your esteemed organisation.

I have hands-on experience and solid proficiency in {skill_str}. I am passionate about applying these skills to real-world challenges and am eager to contribute meaningfully to your team.

I am a quick learner, a team player, and highly motivated to grow in a professional environment. Please find my resume attached for your kind consideration.

I would welcome the opportunity to discuss how my background and skills align with your requirements. Thank you for your time.

Warm regards,
{name}
"""
