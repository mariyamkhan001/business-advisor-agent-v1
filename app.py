"""
Business Advisor App
---------------------
A beginner-friendly Streamlit app that uses a single CrewAI agent (powered
by Groq's "openai/gpt-oss-120b" model) to analyze a business idea or
business problem and produce:
  1. A clear analysis of what was provided
  2. Practical recommendations
  3. General (non-legal-advice) considerations about IP / patent protection
  4. A list of missing information the user should think about
  5. A structured, actionable action plan

The agent is instructed to NEVER invent facts. If something is not in the
user's input, it must say so instead of guessing.

This file is intentionally written with lots of comments and small,
readable functions so it is easy to follow for students / non-technical
readers.
"""

import time
import traceback

import streamlit as st
from crewai import Agent, Crew, Task, Process, LLM

# ---------------------------------------------------------------------------
# 1. PAGE CONFIG (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Business Advisor",
    page_icon="🧭",
    layout="centered",
)

# ---------------------------------------------------------------------------
# 2. CONSTANTS
# ---------------------------------------------------------------------------
# The exact Groq production model requested. CrewAI (via LiteLLM) expects
# Groq models to be prefixed with "groq/".
GROQ_MODEL_NAME = "groq/openai/gpt-oss-120b"

MIN_INPUT_LENGTH = 25  # minimum characters before we consider the input usable
MAX_RETRIES = 2         # how many times we retry on transient Groq errors
REQUEST_TIMEOUT_SECONDS = 60  # per-call timeout passed to the LLM

DISCLAIMER = (
    "⚠️ **Disclaimer:** This tool provides general, educational business "
    "information only. It is **not** legal, financial, or patent advice. "
    "For real IP protection or legal decisions, please consult a licensed "
    "attorney or a registered patent professional."
)


# ---------------------------------------------------------------------------
# 3. HELPER: Safely load the Groq API key from Streamlit Secrets
# ---------------------------------------------------------------------------
def get_groq_api_key():
    """
    Reads the Groq API key from Streamlit's secrets manager.
    Returns None (instead of crashing) if it is missing, so we can show
    a friendly error message in the UI instead of a raw Python traceback.
    """
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 4. HELPER: Build the CrewAI agent, task and crew
# ---------------------------------------------------------------------------
def build_crew(api_key: str, user_input: str) -> Crew:
    """
    Creates a single-agent CrewAI Crew configured to talk to Groq.
    Kept as a function so a fresh crew is built for every request
    (avoids leftover state between runs).
    """

    # The LLM object tells CrewAI which model/provider to call.
    # CrewAI uses LiteLLM under the hood, which routes "groq/..." model
    # names to Groq's API automatically as long as the key is provided.
    llm = LLM(
        model=GROQ_MODEL_NAME,
        api_key=api_key,
        temperature=0.3,       # lower temperature = more focused, less "creative" guessing
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    # ---- The single agent -------------------------------------------------
    business_advisor = Agent(
        role="Business Advisor",
        goal=(
            "Analyze the business idea or problem the user describes, and "
            "produce a grounded, honest, and structured response that helps "
            "the user think clearly about their next steps."
        ),
        backstory=(
            "You are a pragmatic, experienced business advisor who has "
            "helped many early-stage founders and small business owners. "
            "You are careful, precise, and you NEVER invent facts, numbers, "
            "market data, competitor names, or legal conclusions that were "
            "not given to you by the user. When information is missing, you "
            "clearly say so instead of guessing. You explain things in "
            "plain, simple language suitable for a beginner or a "
            "non-technical founder."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # ---- The task -----------------------------------------------------
    task_description = f"""
You will analyze the following business idea or business problem, exactly
as written by the user. Do not add facts, statistics, competitor names,
market sizes, or legal conclusions that are not explicitly present in the
text below.

USER INPUT:
\"\"\"
{user_input}
\"\"\"

Follow these rules strictly:
- Base your entire analysis ONLY on the information given above.
- If something important is not mentioned (e.g., target market, budget,
  location, business stage, competitors, uniqueness of the idea), do NOT
  assume it. Instead, list it under "Missing Information".
- Do not give specific legal, tax, or regulatory advice. For IP/patent
  topics, explain GENERAL concepts only (e.g., the difference between an
  idea and an invention, that patents generally protect novel inventions
  and not pure ideas, that trademarks protect brand names/logos, that
  copyrights protect original creative works) and always recommend
  consulting a qualified professional for real decisions.
- Be honest about uncertainty or risk instead of being overly positive.
- Keep language simple and beginner-friendly. Avoid jargon, or explain it
  briefly when you must use it.

Structure your response using EXACTLY these five Markdown headings, in
this order:

## 1. Business Analysis
Summarize and evaluate what the user described: the core idea/problem,
its apparent strengths, and its apparent risks or weaknesses, based only
on what was provided.

## 2. Recommendations
Give clear, practical, and realistic next-step recommendations based only
on the given information.

## 3. Intellectual Property (IP) & Patent Considerations (General Information Only)
Explain, in general terms, what kinds of protection (patent, trademark,
copyright, trade secret) MIGHT be relevant to consider for this type of
idea, and why. Clearly state this is general education, not legal advice,
and that a qualified IP attorney should be consulted before taking action.

## 4. Missing Information
List, as bullet points, the important details that were NOT provided and
would be needed for a more complete and accurate analysis. Do not guess
their values.

## 5. Action Plan
Provide a clear, numbered, step-by-step action plan the user could
realistically follow next, based only on what is known. Keep steps
specific and actionable (not vague).
"""

    business_task = Task(
        description=task_description,
        expected_output=(
            "A well-structured Markdown response containing exactly the "
            "five required sections, grounded only in the user's input, "
            "with missing information clearly flagged rather than assumed."
        ),
        agent=business_advisor,
    )

    # ---- The crew (single agent, single task) ------------------------
    crew = Crew(
        agents=[business_advisor],
        tasks=[business_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


# ---------------------------------------------------------------------------
# 5. HELPER: Run the crew with basic retry logic for transient errors
# ---------------------------------------------------------------------------
def run_crew_with_retries(crew: Crew):
    """
    Runs the crew and retries a couple of times on transient failures
    (e.g., short network hiccups). Returns (result_text, error_message).
    Exactly one of the two will be None.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):  # e.g. 1 try + MAX_RETRIES retries
        try:
            result = crew.kickoff()
            # CrewAI's kickoff() returns a CrewOutput object; str() gives
            # us the final text.
            return str(result), None

        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()

            # --- Try to classify the error for a friendlier message -----
            is_rate_limit = (
                "rate limit" in error_text
                or "429" in error_text
                or "too many requests" in error_text
            )
            is_timeout = "timeout" in error_text or "timed out" in error_text
            is_auth = (
                "401" in error_text
                or "unauthorized" in error_text
                or "invalid api key" in error_text
                or "authentication" in error_text
            )

            # Auth errors won't be fixed by retrying — stop immediately.
            if is_auth:
                return None, (
                    "🔑 **Authentication error.** Your Groq API key appears to be "
                    "missing or invalid. Please check the `GROQ_API_KEY` value in "
                    "your Streamlit Secrets."
                )

            # If we still have retries left, wait a moment and try again.
            if attempt <= MAX_RETRIES:
                wait_seconds = 2 * attempt  # simple linear backoff
                if is_rate_limit:
                    st.info(
                        f"⏳ Groq rate limit reached. Retrying in "
                        f"{wait_seconds} seconds... (attempt {attempt} of {MAX_RETRIES})"
                    )
                elif is_timeout:
                    st.info(
                        f"⏳ The request timed out. Retrying in "
                        f"{wait_seconds} seconds... (attempt {attempt} of {MAX_RETRIES})"
                    )
                else:
                    st.info(
                        f"⏳ A temporary error occurred. Retrying in "
                        f"{wait_seconds} seconds... (attempt {attempt} of {MAX_RETRIES})"
                    )
                time.sleep(wait_seconds)
                continue

            # No retries left — build a final, friendly error message.
            if is_rate_limit:
                return None, (
                    "🚦 **Groq rate limit reached.** You've sent too many requests "
                    "in a short time. Please wait a minute and try again."
                )
            if is_timeout:
                return None, (
                    "⏱️ **The request timed out.** Groq's servers took too long to "
                    "respond. Please try again in a moment."
                )
            return None, (
                "❌ **An unexpected error occurred while contacting Groq.**\n\n"
                f"Technical details: `{exc}`"
            )

    return None, f"❌ Unknown error. Last exception: {last_error}"


# ---------------------------------------------------------------------------
# 6. UI: Header
# ---------------------------------------------------------------------------
st.title("🧭 Business Advisor")
st.write(
    "Describe your business idea or business problem below. The AI advisor "
    "will analyze **only** what you provide, give recommendations, explain "
    "general IP/patent considerations, flag missing information, and build "
    "an action plan."
)
st.info(DISCLAIMER)

# ---------------------------------------------------------------------------
# 7. UI: Check for API key before showing the rest of the app
# ---------------------------------------------------------------------------
groq_api_key = get_groq_api_key()

if not groq_api_key:
    st.error(
        "🔑 **Groq API key not found.**\n\n"
        "This app needs a Groq API key to work. If you are the developer:\n\n"
        "1. Create a file at `.streamlit/secrets.toml` (for local testing), or\n"
        "2. Add it in **Streamlit Community Cloud → App settings → Secrets** "
        "(for deployment).\n\n"
        "In both cases, add a line like this:\n\n"
        "```toml\n"
        'GROQ_API_KEY = "your-groq-api-key-here"\n'
        "```"
    )
    st.stop()  # Stop here — no point showing the input form without a key

# ---------------------------------------------------------------------------
# 8. UI: Input form
# ---------------------------------------------------------------------------
with st.form("business_input_form"):
    user_input = st.text_area(
        "Describe your business idea or problem:",
        placeholder=(
            "Example: I want to start a subscription box service for "
            "eco-friendly pet toys, aimed at dog owners in my city. I have "
            "no funding yet and haven't researched competitors."
        ),
        height=200,
    )
    submitted = st.form_submit_button("Analyze My Business Idea")

# ---------------------------------------------------------------------------
# 9. UI: Handle submission
# ---------------------------------------------------------------------------
if submitted:
    # --- Basic input validation (handled gracefully, no crashes) -------
    cleaned_input = (user_input or "").strip()

    if not cleaned_input:
        st.warning("⚠️ Please enter a business idea or problem before submitting.")
        st.stop()

    if len(cleaned_input) < MIN_INPUT_LENGTH:
        st.warning(
            "⚠️ That description looks very short. Please add a bit more detail "
            "(what the idea/problem is, who it's for, etc.) so the advisor can "
            "give you a meaningful analysis."
        )
        st.stop()

    # --- Run the agent ---------------------------------------------------
    with st.spinner("🤔 Analyzing your business idea... this may take a moment."):
        try:
            crew = build_crew(api_key=groq_api_key, user_input=cleaned_input)
            result_text, error_message = run_crew_with_retries(crew)
        except Exception:
            # Catch-all safety net so the app never shows a raw crash screen.
            result_text, error_message = None, (
                "❌ **Something went wrong while setting up the analysis.**\n\n"
                f"Technical details:\n```\n{traceback.format_exc()}\n```"
            )

    # --- Show results or errors ------------------------------------------
    if error_message:
        st.error(error_message)
    elif result_text:
        st.success("✅ Analysis complete!")
        st.markdown("---")
        st.markdown(result_text)
        st.markdown("---")
        st.caption(DISCLAIMER)
    else:
        st.error("❌ No response was generated. Please try again.")
