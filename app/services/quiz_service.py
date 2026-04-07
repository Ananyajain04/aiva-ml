"""
Daily Quiz Service
──────────────────
Generates contextual and cognitive daily quiz questions.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime

from app.models.schemas import QuizQuestion, QuizResponse


def generate_daily_quiz(user_id: str) -> QuizResponse:
    """Generate 3 contextual daily quiz questions."""
    questions = []
    now = datetime.now()

    # 1. Orientation question
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    actual_day = now.strftime("%A")
    wrong_days = [d for d in days if d != actual_day]
    options_day = random.sample(wrong_days, 3) + [actual_day]
    random.shuffle(options_day)

    questions.append(
        QuizQuestion(
            id=str(uuid.uuid4()),
            question="What day of the week is it today?",
            options=options_day,
            correct_option_index=options_day.index(actual_day),
        )
    )

    # 2. Basic Math question
    a = random.randint(3, 9)
    b = random.randint(2, 9)
    ans = a + b
    wrong_math = [ans - 1, ans + 1, ans + 2]
    options_math = wrong_math + [ans]
    random.shuffle(options_math)

    questions.append(
        QuizQuestion(
            id=str(uuid.uuid4()),
            question=f"What is {a} + {b}?",
            options=[str(opt) for opt in options_math],
            correct_option_index=options_math.index(ans),
        )
    )

    # 3. Simple observation / season question
    month = now.strftime("%B")
    months = ["January", "April", "July", "October"]
    if month not in months:
        months[0] = month  # Ensure correct is in options
    random.shuffle(months)

    questions.append(
        QuizQuestion(
            id=str(uuid.uuid4()),
            question="Which month are we currently in?",
            options=months,
            correct_option_index=months.index(month),
        )
    )

    return QuizResponse(questions=questions)
