import streamlit as st
import re
import html

from model_loader import generate_answer


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OS Professor",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .question-box {
        background: #1f2028;
        padding: 18px;
        border-radius: 12px;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    .answer-box {
        background: #17181f;
        padding: 22px;
        border-radius: 12px;
        margin-bottom: 20px;
        line-height: 1.7;
    }

    .error-box {
        background: #3a1818;
        border: 1px solid #8b3030;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CLEAN MODEL OUTPUT
# ============================================================

def clean_answer(text):

    if not text:
        return ""

    text = str(text)

    # --------------------------------------------------------
    # Decode HTML entities
    # Example:
    # &#x27;  -> '
    # &amp;    -> &
    # --------------------------------------------------------

    text = html.unescape(text)

    # --------------------------------------------------------
    # Remove code fences
    # --------------------------------------------------------

    text = re.sub(r"```python", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # --------------------------------------------------------
    # Remove XML / HTML tags
    # --------------------------------------------------------

    text = re.sub(r"<[^>]*>", "", text)

    # --------------------------------------------------------
    # Remove common model control tokens
    # --------------------------------------------------------

    unwanted_tokens = [
        "<no_output>",
        "</no_output>",
        "<|endoftext|>",
        "<|im_end|>",
        "<|im_start|>",
        "<|end|>",
        "<response>",
        "</response>",
        "<result>",
        "</result>",
        "<output>",
        "</output>",
        "<document>",
        "</document>",
        "<draft>",
        "</draft>",
        "<html>",
        "</html>",
        "<head>",
        "</head>",
        "<body>",
        "</body>"
    ]

    for token in unwanted_tokens:
        text = text.replace(token, "")

    # --------------------------------------------------------
    # Remove repeated model garbage
    # --------------------------------------------------------

    garbage_patterns = [
        r"\*\*Final Answer\*\*",
        r"\*\*Final answer\*\*",
        r"\*\*Answer\*\*",
        r"Please note that the above response.*",
        r"Good luck!.*",
        r"The importance of understanding.*"
    ]

    for pattern in garbage_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

    # --------------------------------------------------------
    # Remove repeated blank lines
    # --------------------------------------------------------

    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # --------------------------------------------------------
    # Remove spaces at line ends
    # --------------------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    text = "\n\n".join(lines)

    return text.strip()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎓 OS Professor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Learn Operating Systems through clear explanations, '
    'examples, numerical problems, and exam-oriented answers.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# INTRODUCTION
# ============================================================

with st.container():

    st.info(
        """
        **OS Professor**

        I will teach Operating Systems step-by-step.

        You can ask:

        • Explain deadlock  
        • What is paging?  
        • Explain CPU scheduling  
        • What is hold and wait?  
        • Explain FIFO page replacement  
        • Give a numerical problem  
        • Solve this numerical step-by-step  
        • What is important for the exam?
        """
    )


# ============================================================
# DISPLAY PREVIOUS CHAT
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="question-box">
                <b>👤 You</b>
                <br><br>
                {html.escape(message["content"])}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<div class="answer-box">',
            unsafe_allow_html=True
        )

        # IMPORTANT:
        # Do NOT use unsafe_allow_html=True for model answer.
        # This prevents generated HTML from being rendered.

        st.markdown(
            message["content"],
            unsafe_allow_html=False
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================
# INPUT
# ============================================================

question = st.chat_input(
    "Ask your OS Professor anything..."
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    question = question.strip()

    if not question:
        st.warning("Please enter a question.")
        st.stop()


    # --------------------------------------------------------
    # SHOW USER QUESTION
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    # --------------------------------------------------------
    # BUILD SHORT HISTORY
    # --------------------------------------------------------

    history_parts = []

    for message in st.session_state.messages[-6:]:

        role = message["role"]

        if role == "user":
            history_parts.append(
                "Student: " + message["content"]
            )

        else:
            history_parts.append(
                "Professor: " + message["content"]
            )


    conversation_history = "\n".join(history_parts)


    # --------------------------------------------------------
    # DETECT QUESTION TYPE
    # --------------------------------------------------------

    lower_question = question.lower()

    numerical_words = [
        "numerical",
        "calculate",
        "calculate the",
        "find the",
        "solve",
        "page fault",
        "page faults",
        "waiting time",
        "turnaround time",
        "completion time",
        "response time",
        "average waiting",
        "average turnaround",
        "seek time",
        "throughput",
        "hit ratio",
        "miss ratio",
        "address",
        "physical address",
        "virtual address"
    ]


    is_numerical = any(
        word in lower_question
        for word in numerical_words
    )


    if is_numerical:

        answer_type = "Numerical Problem"

        difficulty = "Exam Numerical"

    else:

        answer_type = "Theory Explanation"

        difficulty = "University Exam"


    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    with st.spinner("OS Professor is thinking..."):

        try:

            raw_answer = generate_answer(
                question=question,
                retrieved_context="",
                difficulty=difficulty,
                answer_type=answer_type,
                conversation_history=conversation_history
            )

            # VERY IMPORTANT
            # Clean model output BEFORE displaying it.

            answer = clean_answer(raw_answer)


        except Exception as e:

            answer = ""

            st.error(
                f"Model generation error: {type(e).__name__}: {e}"
            )


    # --------------------------------------------------------
    # EMPTY RESPONSE
    # --------------------------------------------------------

    if not answer:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "I could not generate a complete answer. "
                    "Please ask the question again."
                )
            }
        )

        st.rerun()


    # --------------------------------------------------------
    # SAVE ANSWER
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    st.rerun()