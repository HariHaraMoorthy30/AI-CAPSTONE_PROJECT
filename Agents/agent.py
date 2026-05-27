from dotenv import load_dotenv
from langchain.agents import create_agent

from app.Tools.tools import (

    detect_mode,

    query_documents,

    hybrid_search,

    fts_search

)

load_dotenv()


my_agent = create_agent(

    model=
    "google_genai:gemini-3.1-pro-preview",

    tools=[

        detect_mode,

        query_documents,

        hybrid_search,

        fts_search

    ],

    system_prompt="""

You are an AI-powered
Retail Banking and Wealth
Advisory Assistant.

RULES:

1. NEVER answer from memory

2. ALWAYS retrieve context

3. FIRST call detect_mode

4. Based on detect_mode:

keyword → fts_search

hybrid → hybrid_search

vector → query_documents

5. Answer ONLY using
retrieved context

6. Never hallucinate

7. If retrieval is empty
respond exactly:

No information found

8. Personalized recommendations
must consider:

-age
-income
-goals
-credit score
-liabilities
-existing investments
-employment
-risk appetite

9. Response format:

### Recommendation

### Rationale

### Risk Warning

### Next Steps

### Citations

10. Never mention tools

"""

)


def ask_agent(
        query: str
):

    response = my_agent.invoke(

        {

            "messages": [

                {

                    "role": "user",

                    "content": query

                }

            ]

        }

    )

    return response[
        "messages"
    ][-1].text