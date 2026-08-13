
import streamlit as st
import os
import json
import re
import time
from google import genai

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Interactive Question Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #0e1117;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(
        135deg,
        #151922,
        #202431
    );
    border: 1px solid #343a46;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 5px;
}

.hero p {
    font-size: 17px;
    color: #b8bec9;
}

.question-card {
    padding: 25px;
    border-radius: 18px;
    background: #181c25;
    border: 1px solid #343a46;
    margin-top: 15px;
    margin-bottom: 20px;
}

.score-card {
    padding: 25px;
    border-radius: 18px;
    background: #171b23;
    border: 1px solid #343a46;
    text-align: center;
}

.correct {
    padding: 15px;
    border-radius: 12px;
    background: rgba(0, 180, 100, 0.12);
    border: 1px solid #00b46b;
}

.incorrect {
    padding: 15px;
    border-radius: 12px;
    background: rgba(255, 70, 70, 0.12);
    border: 1px solid #ff4646;
}

.info-box {
    padding: 15px;
    border-radius: 12px;
    background: #20242e;
    border: 1px solid #343a46;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "quiz": [],
    "current_question": 0,
    "score": 0,
    "answered": False,
    "selected_answer": None,
    "quiz_started": False,
    "quiz_finished": False,
    "answer_history": [],
    "quiz_title": "",
    "generation_time": 0,
    "show_explanation": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GEMINI API KEY
# ============================================================

api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚙️ Quiz Settings")

    st.markdown("---")

    subject = st.text_input(
        "📚 Subject",
        placeholder="Example: Artificial Intelligence"
    )

    topic = st.text_input(
        "🎯 Topic",
        placeholder="Example: Uninformed Search"
    )

    academic_level = st.selectbox(
        "🎓 Academic Level",
        [
            "School",
            "Intermediate",
            "Undergraduate",
            "Postgraduate",
            "Competitive Exam"
        ]
    )

    difficulty = st.select_slider(
        "🔥 Difficulty",
        options=[
            "Easy",
            "Medium",
            "Hard",
            "Expert"
        ],
        value="Medium"
    )

    question_type = st.selectbox(
        "📝 Question Type",
        [
            "Multiple Choice Questions (MCQ)",
            "True / False",
            "Short Answer"
        ]
    )

    number_questions = st.slider(
        "🔢 Number of Questions",
        min_value=3,
        max_value=15,
        value=5
    )

    st.markdown("---")

    additional_instructions = st.text_area(
        "✨ Additional Instructions",
        placeholder=(
            "Example:\n"
            "Focus on exam-oriented questions.\n"
            "Include real-world applications.\n"
            "Avoid very easy questions."
        ),
        height=120
    )

    st.markdown("---")

    generate_button = st.button(
        "🚀 Generate Interactive Quiz",
        use_container_width=True,
        type="primary"
    )

    reset_button = st.button(
        "🔄 Reset Quiz",
        use_container_width=True
    )


# ============================================================
# RESET QUIZ
# ============================================================

if reset_button:

    for key in defaults:
        st.session_state[key] = defaults[key]

    st.rerun()


# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div class="hero">

<h1>🧠 AI Interactive Question Generator</h1>

<p>
Generate AI-powered questions with Gemini,
answer them interactively, receive explanations,
and track your score in real time.
</p>

</div>
""", unsafe_allow_html=True)


# ============================================================
# API KEY CHECK
# ============================================================

if not api_key:

    st.warning(
        "⚠️ Gemini API key not configured. "
        "Add GEMINI_API_KEY to Streamlit Secrets."
    )

    st.info(
        "For Google Colab testing, set the environment variable "
        "GEMINI_API_KEY before running the app."
    )

    st.stop()


# ============================================================
# GEMINI QUESTION GENERATOR
# ============================================================

def generate_questions():

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert educational assessment generator.

Generate exactly {number_questions} questions.

Subject:
{subject}

Topic:
{topic}

Academic Level:
{academic_level}

Difficulty:
{difficulty}

Question Type:
{question_type}

Additional Instructions:
{additional_instructions}

IMPORTANT:

Return ONLY valid JSON.

The JSON must follow this exact structure:

{{
    "quiz_title": "string",
    "questions": [
        {{
            "question": "string",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "explanation": "string",
            "hint": "string"
        }}
    ]
}}

Rules:

1. Create exactly {number_questions} questions.
2. Questions must specifically relate to the given topic.
3. Avoid duplicate questions.
4. Make the difficulty appropriate.
5. For MCQs provide exactly four options.
6. The answer must contain the exact correct option text.
7. Provide a useful explanation.
8. Provide a short educational hint.
9. Do not include markdown.
10. Return only JSON.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text.strip()

    # Remove accidental markdown code fences
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()

    return json.loads(text)


# ============================================================
# GENERATE QUIZ
# ============================================================

if generate_button:

    if not subject.strip():
        st.error("Please enter a subject.")

    elif not topic.strip():
        st.error("Please enter a topic.")

    else:

        with st.spinner("🧠 Gemini is creating your interactive quiz..."):

            start_time = time.time()

            try:

                result = generate_questions()

                st.session_state.quiz = result["questions"]
                st.session_state.quiz_title = result.get(
                    "quiz_title",
                    f"{subject} - {topic}"
                )

                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.answer_history = []
                st.session_state.quiz_started = True
                st.session_state.quiz_finished = False
                st.session_state.answered = False
                st.session_state.selected_answer = None
                st.session_state.show_explanation = False

                st.session_state.generation_time = round(
                    time.time() - start_time,
                    2
                )

                st.success(
                    f"🎉 Generated {len(st.session_state.quiz)} questions!"
                )

                st.rerun()

            except Exception as e:

                st.error("❌ Unable to generate questions.")

                st.code(str(e))


# ============================================================
# QUIZ INTERFACE
# ============================================================

if st.session_state.quiz_started and st.session_state.quiz:

    quiz = st.session_state.quiz

    current = st.session_state.current_question

    total = len(quiz)

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    if st.session_state.quiz_finished:

        st.markdown("## 🏆 Quiz Completed!")

        percentage = round(
            (st.session_state.score / total) * 100
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Score",
                f"{st.session_state.score}/{total}"
            )

        with col2:

            st.metric(
                "Percentage",
                f"{percentage}%"
            )

        with col3:

            if percentage >= 80:
                grade = "Excellent 🥇"
            elif percentage >= 60:
                grade = "Good 🥈"
            elif percentage >= 40:
                grade = "Needs Practice 📚"
            else:
                grade = "Keep Learning 💪"

            st.metric(
                "Performance",
                grade
            )

        st.markdown("---")

        st.markdown("### 📊 Question Review")

        for i, item in enumerate(
            st.session_state.answer_history
        ):

            if item["correct"]:

                st.markdown(
                    f"""
                    <div class="correct">
                    <b>Question {i+1} — ✅ Correct</b><br>
                    {item["question"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="incorrect">
                    <b>Question {i+1} — ❌ Incorrect</b><br>
                    {item["question"]}<br><br>
                    <b>Your answer:</b> {item["selected"]}<br>
                    <b>Correct answer:</b> {item["answer"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with st.expander("💡 Explanation"):

                st.write(item["explanation"])

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "🔄 Take Another Quiz",
                use_container_width=True,
                type="primary"
            ):

                st.session_state.quiz = []
                st.session_state.quiz_started = False
                st.session_state.quiz_finished = False
                st.session_state.answer_history = []

                st.rerun()

        with col2:

            report = f"""
AI INTERACTIVE QUIZ REPORT

Quiz:
{st.session_state.quiz_title}

Score:
{st.session_state.score}/{total}

Percentage:
{percentage}%

Performance:
{grade}
"""

            st.download_button(
                "📥 Download Result",
                report,
                file_name="quiz_result.txt",
                mime="text/plain",
                use_container_width=True
            )

    else:

        # ----------------------------------------------------
        # QUIZ HEADER
        # ----------------------------------------------------

        st.markdown(
            f"## 📖 {st.session_state.quiz_title}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Question",
                f"{current + 1}/{total}"
            )

        with col2:
            st.metric(
                "Score",
                st.session_state.score
            )

        with col3:
            st.metric(
                "Difficulty",
                difficulty
            )

        st.progress(
            (current + 1) / total
        )

        # ----------------------------------------------------
        # CURRENT QUESTION
        # ----------------------------------------------------

        q = quiz[current]

        st.markdown(
            f"""
            <div class="question-card">

            <h3>
            Question {current + 1}
            </h3>

            <h2>
            {q["question"]}
            </h2>

            </div>
            """,
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # ANSWERING
        # ----------------------------------------------------

        if not st.session_state.answered:

            if question_type == "Multiple Choice Questions (MCQ)":

                selected = st.radio(
                    "Choose your answer:",
                    q["options"],
                    key=f"answer_{current}"
                )

            elif question_type == "True / False":

                selected = st.radio(
                    "Choose your answer:",
                    ["True", "False"],
                    key=f"answer_{current}"
                )

            else:

                selected = st.text_input(
                    "Type your answer:",
                    key=f"answer_{current}"
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Submit Answer",
                    use_container_width=True,
                    type="primary"
                ):

                    if not selected:

                        st.warning(
                            "Please select or enter an answer."
                        )

                    else:

                        correct_answer = q["answer"]

                        if question_type == "Short Answer":

                            is_correct = (
                                selected.strip().lower()
                                == correct_answer.strip().lower()
                            )

                        else:

                            is_correct = (
                                selected.strip().lower()
                                == correct_answer.strip().lower()
                            )

                        if is_correct:

                            st.session_state.score += 1

                        st.session_state.answered = True
                        st.session_state.selected_answer = selected
                        st.session_state.show_explanation = False

                        st.session_state.answer_history.append(
                            {
                                "question": q["question"],
                                "selected": selected,
                                "answer": correct_answer,
                                "correct": is_correct,
                                "explanation": q["explanation"]
                            }
                        )

                        st.rerun()

            with col2:

                if st.button(
                    "💡 Show Hint",
                    use_container_width=True
                ):

                    st.info(
                        f"💡 Hint: {q['hint']}"
                    )


        # ----------------------------------------------------
        # ANSWER FEEDBACK
        # ----------------------------------------------------

        else:

            selected = st.session_state.selected_answer

            correct_answer = q["answer"]

            is_correct = (
                selected.strip().lower()
                == correct_answer.strip().lower()
            )

            if is_correct:

                st.success(
                    "🎉 Correct! Excellent work."
                )

            else:

                st.error(
                    f"❌ Not quite. The correct answer is: "
                    f"{correct_answer}"
                )

            with st.expander(
                "💡 View AI Explanation",
                expanded=True
            ):

                st.write(q["explanation"])

            # -----------------------------------------------
            # NEXT QUESTION
            # -----------------------------------------------

            if current + 1 < total:

                if st.button(
                    "➡️ Next Question",
                    use_container_width=True,
                    type="primary"
                ):

                    st.session_state.current_question += 1
                    st.session_state.answered = False
                    st.session_state.selected_answer = None
                    st.session_state.show_explanation = False

                    st.rerun()

            else:

                if st.button(
                    "🏆 Finish Quiz",
                    use_container_width=True,
                    type="primary"
                ):

                    st.session_state.quiz_finished = True

                    st.rerun()


# ============================================================
# EMPTY STATE
# ============================================================

else:

    st.markdown("## 🚀 Start Learning")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="info-box">

        ### 🎯 Topic Focus

        Enter any subject and topic
        to generate customized questions.

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="info-box">

        ### 🧠 Gemini AI

        Questions, hints and explanations
        are generated dynamically using Gemini.

        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="info-box">

        ### 🏆 Interactive Quiz

        Answer questions, get instant feedback
        and track your performance.

        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.info(
        "👈 Configure your quiz from the sidebar "
        "and click **Generate Interactive Quiz**."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🧠 AI Interactive Question Generator | "
    "Powered by Gemini AI + Streamlit"
)
