import streamlit as st
from groq import Groq
from dotenv import load_dotenv  # gets API key from .env file
import os
import time  # for warning system & testing schedule

# load API key and Groq() makes reusable client object that connects to API with key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# === EARLY WARNING SYSTEM ===
# Groq model limits
TPM_LIMIT = 0
RPM_LIMIT = 0

used_tokens = 0
used_requests = 0
start_time = time.time()

# auto pause/ slow before hitting 429 error
# funciton to check if can make request
    # check elapsed time, reset counters every min
    # show warning before hitting limit st.warning(x "left until token limit")
    # progress bar: st.progress(used_tokens / TPM_LIMIT)
    # allow request if under limit

# === WEBSITE DISPLAY ===
st.set_page_config(page_title="Recall-Ready", layout="centered")
st.title("Recall-Ready")
st.write(
    "Paste your notes here. "
    "This tool will generate a short quiz designed to help you actively study.\n\n"  # need to figure out how to handle limits
    "_Disclaimer: The quality of the quiz depends on the **quality of your notes**._"
    )  
# maybe if notes: user could mark where they're confused and chat could clarify misunderstandings

# === INPUT PREPROCESSING ===
# shorten prompts, break large text into small chunks
notes = st.text_area(
    "Paste notes:",
    height=300,
    placeholder="Notes here..."
)
char_count = len(notes)
st.caption(f"Character Count: {char_count} / 20,000")
MAX_CHARS = 20000

if len(notes) > MAX_CHARS:
    st.error("Input too long. Please shorten your notes to under 20,000 characters.")
    st.stop()


num_questions = st.slider("Number of quiz questions", 3, 10, 5)


# === QUIZ === 
# could track token frequency to track key concepts
# give API context 
# messages = [ {"role": "system", "content": "You are a intelligent study assistant etctectc."} ]
# TO DO: requiz only with missed questions until they get them right 
if st.button("Generate Quiz"):
    if not notes.strip():
        st.warning("Please paste some notes first.")
    else:
        with st.spinner("Generating quiz..."):

            prompt = f"""
You are an intelligent study assistant.

From the following notes, generate {num_questions} multiple-choice questions.
Each question should have:
- A question based on the notes
- 4 answer choices (A, B, C, D)
- One clearly correct answer

Format EXACTLY like this:

Question 1: ...
A. ...
B. ...
C. ...
D. ...

Correct Answer: A

Notes:
{notes}
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            quiz_text = response.choices[0].message.content
            st.session_state["quiz"] = quiz_text

# ===== DISPLAY QUIZ =====
if "quiz" in st.session_state:
    st.subheader("Quiz")

    quiz_lines = st.session_state["quiz"].split("\n")
    questions = []
    current = {}

    for line in quiz_lines:
        line = line.strip()

        if line.startswith("Question"):
            if current:
                questions.append(current)
            current = {"question": line, "options": [], "answer": ""}
        elif line.startswith(("A.", "B.", "C.", "D.")):
            current["options"].append(line)
        elif line.startswith("Correct Answer"):
            current["answer"] = line.split(":")[-1].strip()

    if current:
        questions.append(current)

    user_answers = {}

    for i, q in enumerate(questions):
        st.markdown(f"**{q['question']}**")
        choice = st.radio(
            f"Select an answer for Question {i+1}",
            q["options"],
            key=i
        )
        user_answers[i] = choice[0]

    if st.button("Submit Quiz"):
        score = 0
        st.subheader("Results")

        for i, q in enumerate(questions):
            correct = q["answer"]
            user = user_answers[i]

            if user == correct:
                st.success(f"Question {i+1}: Correct!")
                score += 1
            else:
                st.error(
                    f"Question {i+1}: Incorrect. "
                    f"Correct answer was {correct}."
                )

        st.markdown(f"### Final Score: **{score} / {len(questions)}**")


