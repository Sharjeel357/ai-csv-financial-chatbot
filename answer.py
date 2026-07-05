"""
This is the SECOND and final place the LLM is used. By this point,
compute.py has already calculated the real number using Pandas. The
LLM's only job here is to explain that number in a friendly sentence —
it is given the number as a fact and told not to change it.

If Groq isn't available, we fall back to a simple template so the app
still gives a readable answer without an LLM.
"""

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS

ANSWER_SYSTEM_PROMPT = """You are a helpful financial assistant for a real-estate
portfolio system. You will be given a question and a result that has ALREADY
been calculated using Pandas. Treat the number as ground truth — never change
it, recalculate it, or round it differently. Your only job is to explain it
in 2-4 clear, professional sentences. Do not output JSON or markdown tables.
"""


def _build_result_summary(result: dict) -> str:
    """Turn the result dictionary into a short text summary for the prompt."""
    if result.get("is_guarded"):
        return f"GUARDED: {result.get('guard_message')}"

    parts = []
    if result.get("value") is not None:
        parts.append(f"value = {result['value']}")
    if result.get("table"):
        parts.append(f"table (first 5 rows) = {result['table'][:5]}")
    parts.append(f"rows matched = {result.get('row_count', 0)}")

    return ", ".join(parts)


def _call_groq_for_answer(question: str, result: dict) -> str:
    """Ask Groq to explain the already-computed result."""
    client = Groq(api_key=GROQ_API_KEY)

    result_summary = _build_result_summary(result)
    user_message = (
        f'Question: "{question}"\n'
        f"Computed result (do not change): {result_summary}\n"
        f"Write the final answer now."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return (response.choices[0].message.content or "").strip()


def _template_answer(result: dict) -> str:
    """A simple, no-LLM-required fallback explanation."""
    if result.get("is_guarded"):
        return result.get("guard_message", "This cannot be calculated from the available data.")

    row_count = result.get("row_count", 0)
    if row_count == 0:
        return "No matching data was found for that question. Try a different portfolio, year, or filter."

    if result.get("value") is not None:
        return f"The result is {result['value']:,.2f}, based on {row_count:,} matching rows."

    if result.get("table"):
        top_row = result["table"][0]
        return f"Here is the breakdown across {row_count:,} matching rows. Top entry: {top_row}."

    return f"Calculated across {row_count:,} rows, but there is nothing to display."


def generate_answer(question: str, result: dict) -> str:
    """Main entry point: turn a computed result into a natural-language answer.

    Tries Groq first, falls back to a template if Groq is unavailable or
    the guarded flag is set (guard messages don't need an LLM rewrite).
    """
    if result.get("is_guarded"):
        return result.get("guard_message", "This cannot be calculated from the available data.")

    if GROQ_API_KEY:
        try:
            answer_text = _call_groq_for_answer(question, result)
            if answer_text:
                return answer_text
        except Exception:
            pass  # fall through to the template answer

    return _template_answer(result)
