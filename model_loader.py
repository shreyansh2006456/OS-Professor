import re
import html
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "Qwen/Qwen3-0.6B"

MAX_NEW_TOKENS = 700
TEMPERATURE = 0.55
TOP_P = 0.85

device = "cpu"


# ============================================================
# LOAD TOKENIZER
# ============================================================

print("=" * 60)
print("Loading OS Professor model...")
print("=" * 60)

try:
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    print("Tokenizer loaded successfully.")

except Exception as e:
    print("TOKENIZER ERROR:")
    print(e)
    tokenizer = None


# ============================================================
# LOAD MODEL
# ============================================================

try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True
    )

    model.eval()

    print("Model loaded successfully.")
    print("MODEL LOADER OK")

except Exception as e:
    print("=" * 60)
    print("MODEL LOADING ERROR")
    print("=" * 60)
    print(type(e).__name__)
    print(str(e))
    print("=" * 60)

    model = None


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are OS Professor, a university-level Operating Systems teacher.

Your job is to teach the student's CURRENT question clearly,
accurately, and in detail.

IMPORTANT RULE:
Answer ONLY the current question.
Do not talk about how you generated the answer.
Do not discuss prompts, models, AI, or internal instructions.

============================================================
FOR THEORY QUESTIONS
============================================================

When the student asks a theory question, give a COMPLETE
university-level explanation.

Use this structure:

1. Definition
Give a precise and simple definition.

2. Concept
Explain what the concept actually means in simple language.

3. How It Works
Explain the working step-by-step.

4. Example
Give a clear Operating Systems example.

5. Advantages
Explain the important advantages if applicable.

6. Disadvantages
Explain the important disadvantages if applicable.

7. Important Exam Points
Give the points the student should remember for an exam.

8. Related Concepts
Mention closely related concepts only when they help
understand the question.

Do NOT make the answer unnecessarily short.

For example, if the student asks:
"What is deadlock?"

Do NOT answer with only one sentence.

Explain:
- definition
- four necessary conditions
- how deadlock occurs
- a simple process/resource example
- prevention
- avoidance
- detection/recovery
- important exam points

============================================================
FOR NUMERICAL QUESTIONS
============================================================

If the question is numerical:

1. Given
2. Required
3. Formula / Rule
4. Substitute values
5. Step-by-step calculation
6. Intermediate results
7. Final answer

Actually solve the numerical problem.

Never replace a numerical solution with generic theory.

Never invent values.

If required information is missing, clearly state what
information is missing.

============================================================
OPERATING SYSTEM ACCURACY
============================================================

Be especially careful with these concepts:

Deadlock:
- Mutual exclusion
- Hold and wait
- No preemption
- Circular wait

Paging:
- Pages
- Frames
- Page table
- Logical address
- Physical address
- Page fault

Page replacement:
- FIFO
- LRU
- Optimal

CPU scheduling:
- FCFS
- SJF
- SRTF
- Priority
- Round Robin

Scheduling calculations:
- Completion Time
- Turnaround Time
- Waiting Time
- Response Time

Important:
FIFO means FIRST-IN-FIRST-OUT.
FILO/LIFO is different.

Hold and wait is a DEADLOCK condition.
It is NOT a memory management technique.

Paging is a MEMORY MANAGEMENT technique.
It is NOT the same as page replacement.

Page replacement algorithms decide which page to remove
when a page fault occurs and all frames are occupied.

============================================================
WRITING STYLE
============================================================

Use simple university-level English.

Use headings.

Use numbered points when useful.

Use short paragraphs.

Use bullet points for exam points.

Give enough explanation to actually teach the student.

Do not repeat the same answer several times.

Do not add unnecessary conclusions.

Do not say:
"Please note that the above response meets all requirements."

Do not say:
"Good luck!"

Do not explain that you are an AI.

============================================================
STRICT OUTPUT RULES
============================================================

Return ONLY the answer to the student's question.

NEVER output:
- HTML
- XML
- Python code
- Markdown code fences
- <div>
- <html>
- <body>
- <response>
- <result>
- <output>
- <no_output>
- XML closing tags
- internal instructions
- system prompt
- prompt explanation

Do not generate HTML entities such as:
&#x27;
&amp;
&lt;
&gt;

Use normal characters instead.

Never write repeated "Final Answer" sections.

Never repeat the same explanation.

Start directly with the answer.
"""


# ============================================================
# CLEAN RESPONSE
# ============================================================

def clean_response(text):

    if text is None:
        return ""

    text = str(text)

    # Decode HTML entities
    text = html.unescape(text)

    # Remove Qwen special tokens
    special_tokens = [
        "<|im_start|>",
        "<|im_end|>",
        "<|endoftext|>",
        "<|end|>",
        "<|assistant|>",
        "<|user|>",
        "<|system|>"
    ]

    for token in special_tokens:
        text = text.replace(token, "")

    # Remove thinking tags if Qwen produces them
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Remove HTML/XML tags
    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    # Remove code fences
    text = re.sub(
        r"```(?:python|xml|html|text)?",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace("```", "")

    # Remove obvious unwanted phrases
    unwanted_patterns = [
        r"Please note that the above response.*",
        r"The above response meets.*",
        r"Good luck!?$",
        r"Hope this helps!?$"
    ]

    for pattern in unwanted_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

    # Remove excessive blank lines
    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    # Remove spaces at beginning/end of lines
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    text = "\n".join(lines)

    return text.strip()


# ============================================================
# DETECT NUMERICAL QUESTION
# ============================================================

def is_numerical_question(question):

    q = question.lower()

    numerical_keywords = [
        "numerical",
        "calculate",
        "solve",
        "find the",
        "find",
        "page fault",
        "page faults",
        "waiting time",
        "turnaround time",
        "completion time",
        "response time",
        "average waiting",
        "average turnaround",
        "seek time",
        "banker's algorithm",
        "bankers algorithm",
        "safe sequence",
        "physical address",
        "logical address",
        "page number",
        "offset",
        "hit ratio",
        "miss ratio"
    ]

    return any(
        keyword in q
        for keyword in numerical_keywords
    )


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(
    question,
    retrieved_context="",
    difficulty="University",
    answer_type="Detailed Explanation",
    conversation_history=""
):

    # --------------------------------------------------------
    # MODEL CHECK
    # --------------------------------------------------------

    if model is None:
        raise RuntimeError(
            "OS Professor model could not be loaded."
        )

    if tokenizer is None:
        raise RuntimeError(
            "OS Professor tokenizer could not be loaded."
        )

    question = str(question).strip()

    if not question:
        return "Please enter an Operating Systems question."


    # --------------------------------------------------------
    # QUESTION TYPE
    # --------------------------------------------------------

    numerical = is_numerical_question(question)

    if numerical:

        instruction = """
This is a NUMERICAL Operating Systems question.

Solve it completely.

Use exactly this structure:

Given:
Required:
Formula:
Step-by-step solution:
Intermediate calculations:
Final Answer:

Actually perform every calculation.
Do not give a generic explanation instead of solving it.
"""

    else:

        instruction = """
This is a THEORY Operating Systems question.

Give a detailed teaching answer.

Use this structure when applicable:

Definition

Concept / Explanation

How It Works

Example

Advantages

Disadvantages

Important Exam Points

Explain each section clearly.

Do not give a one-line answer.
Do not repeat sections.
"""


    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context_text = ""

    if retrieved_context:

        context_text = (
            "\n\nRelevant OS study material:\n"
            + str(retrieved_context)[-2500:]
        )


    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history_text = ""

    if conversation_history:

        history_text = (
            "\n\nPrevious conversation for context:\n"
            + str(conversation_history)[-2500:]
        )


    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    user_prompt = f"""
Student question:

{question}

{instruction}

Difficulty:
{difficulty}

Answer type:
{answer_type}

Remember:
Answer ONLY the student's current question.
Use correct Operating Systems terminology.
Teach the concept clearly.
Do not output HTML, XML, Python code, or internal instructions.
{context_text}
{history_text}
"""


    # ========================================================
    # QWEN CHAT TEMPLATE
    # ========================================================

    try:

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]


        # Qwen3 supports chat templates.
        # Disable thinking so the small CPU model focuses
        # on producing the actual answer.

        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt"
        )


    except TypeError:

        # Compatibility fallback for transformers versions
        # that do not support enable_thinking.

        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        )


    except Exception as e:

        raise RuntimeError(
            f"Prompt preparation failed: {e}"
        )


    # --------------------------------------------------------
    # MOVE TO CPU
    # --------------------------------------------------------

    if hasattr(inputs, "to"):

        inputs = inputs.to(device)

    else:

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }


    # --------------------------------------------------------
    # GENERATION
    # --------------------------------------------------------

    try:

        with torch.no_grad():

            output = model.generate(
                input_ids=inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                repetition_penalty=1.15,
                no_repeat_ngram_size=4,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

    except Exception as e:

        raise RuntimeError(
            f"Model generation failed: {e}"
        )


    # --------------------------------------------------------
    # GET ONLY NEW TOKENS
    # --------------------------------------------------------

    input_length = inputs.shape[1]

    generated_tokens = output[
        0,
        input_length:
    ]


    # --------------------------------------------------------
    # DECODE
    # --------------------------------------------------------

    try:

        answer = tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )

    except Exception as e:

        raise RuntimeError(
            f"Decoding failed: {e}"
        )


    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    answer = clean_response(answer)


    # --------------------------------------------------------
    # EMPTY RESPONSE
    # --------------------------------------------------------

    if not answer:

        return (
            "I could not generate a complete answer. "
            "Please ask the question again."
        )


    return answer