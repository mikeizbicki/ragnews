from openai import OpenAI
client = OpenAI()

'''
response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "system",
      "content": "You are an expert on politics.  Answer the user question in one sentence or less."
    },
    {
      "role": "user",
      "content": "Who are the current presidential candidates?"
    }
  ],
  temperature=0.7,
  max_tokens=64,
  top_p=1
)
'''

import lmql

query = r"""
argmax
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: Who is the democratic presidential candidate?\n"
    "A: [ANSWER]\n"
from
    "openai/gpt-3.5-turbo-instruct"
where
    ANSWER in set(["Trump", "Harris"])
"""

query = r"""
argmax
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: Compare the democratic and republican position on immigration?\n"
    "A: [ANSWER]\n"
from
    "openai/gpt-3.5-turbo-instruct"
where
    STOPS_AT(ANSWER, ".")
"""

query = r"""
argmax
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: How old are the major party candidates?\n"
    "A: Harris is [HARRIS] years old and Trump is [TRUMP] years old.\n"
from
    "openai/gpt-3.5-turbo-instruct"
where
    INT(HARRIS) and INT(TRUMP)
"""

query = r"""
argmax
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: List the major issues in the 2024 election.\n"
    "A: Harris is [HARRIS] years old and Trump is [TRUMP] years old.\n"
from
    "openai/gpt-3.5-turbo-instruct"
where
    INT(HARRIS) and INT(TRUMP)
"""

query = r"""
argmax
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: List the major issues in the 2024 election.\n"
    "A: The major issues are\n"
    "-[ISSUE1]" where STOPS_AT(ISSUE1, "\n")
    "-[ISSUE2]" where STOPS_AT(ISSUE2, "\n")
    "-[ISSUE3]" where STOPS_AT(ISSUE3, "\n")
from
    "openai/gpt-3.5-turbo-instruct"
"""

query = r"""
sample(temperature=0.8)
    "You are an expert on politics.  Answer the user question in one sentence or less.\n"
    "Q: List the major issues in the {year} election.\n"
    "A: The major issues are\n"
    ISSUES = []
    for i in range(10):
        "-[ISSUE]" where STOPS_AT(ISSUE, "\n")
        ISSUES.append(ISSUE.strip())
    "The most important issue for college students is [IMPORTANT]." where IMPORTANT in ISSUES
    return {'ISSUES':ISSUES, 'IMPORTANT':IMPORTANT}
from
    "openai/gpt-3.5-turbo-instruct"
"""

#x = lmql.run_sync(query, year=2024)
#print(f"x={x}")


@lmql.query
def which_candidate(question):
    """lmql
    argmax
        "You are an expert on politics.  Answer the user question in one sentence or less.\n"
        "Q: Which candidate {question}?\n"
        "A: [ANSWER]\n"
        return ANSWER
    from
        "openai/gpt-3.5-turbo-instruct"
    where
        ANSWER in set(["Trump", "Harris"])
    """
