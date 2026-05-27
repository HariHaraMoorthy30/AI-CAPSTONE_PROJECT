import re
import os
import psycopg

from dotenv import load_dotenv
from psycopg.rows import dict_row
from langchain_core.tools import tool

from app.core.db import get_vector_store

load_dotenv()

COLLECTION_NAME = "hr_support_desk"

_row_conn = (
    os.getenv(
        "PG_CONNECTION_STRING"
    ).replace(
        "postgresql+psycopg",
        "postgresql"
    )
)


##################################
# CORE FUNCTIONS
##################################

_KEYWORD_PATTERNS = [

    r"[A-Z]{2,}-\d{4}-\w+",

    r"\b[A-Z]{2,5}\b",

    r"\d{6,}"

]

_KEYWORD_RE = re.compile(
    "|".join(
        _KEYWORD_PATTERNS
    )
)


def detect_mode_core(
        query: str
) -> str:

    query = query.strip()

    if _KEYWORD_RE.search(
            query
    ):
        return "keyword"

    if len(
            query.split()
    ) <= 3:
        return "hybrid"

    return "vector"


def vector_search_core(
        query: str,
        k: int = 5
):

    vector_store = get_vector_store(
        collection_name=
        COLLECTION_NAME
    )

    docs = vector_store.similarity_search(
        query,
        k=k
    )

    return [

        d.page_content

        for d in docs

    ]


def fts_search_core(
        query: str,
        k: int = 5
):

    sql = """

    SELECT
    e.document AS content

    FROM langchain_pg_embedding e

    JOIN langchain_pg_collection c
    ON c.uuid=e.collection_id

    WHERE

    c.name=%(collection)s

    AND

    to_tsvector(
    'english',
    e.document
    )

    @@

    plainto_tsquery(
    'english',
    %(query)s
    )

    LIMIT %(k)s

    """

    with psycopg.connect(

            _row_conn,

            row_factory=
            dict_row

    ) as conn:

        with conn.cursor() as cur:

            cur.execute(

                sql,

                {

                    "query": query,

                    "collection":
                    COLLECTION_NAME,

                    "k": k

                }

            )

            rows = cur.fetchall()

    return [

        x["content"]

        for x in rows

    ]


def hybrid_search_core(
        query: str,
        k: int = 5
):

    vector_docs = vector_search_core(
        query,
        k
    )

    keyword_docs = fts_search_core(
        query,
        k
    )

    merged = []

    seen = set()

    for item in (
            vector_docs +
            keyword_docs
    ):

        if item not in seen:

            merged.append(
                item
            )

            seen.add(
                item
            )

    return merged[:k]


##################################
# TOOL WRAPPERS
##################################

@tool
def detect_mode(
        query: str
) -> str:
    """
    Detect retrieval mode:
    keyword / hybrid / vector
    """

    return detect_mode_core(
        query
    )


@tool
def query_documents(
        query: str
) -> str:
    """
    Semantic vector retrieval
    """

    docs = vector_search_core(
        query
    )

    return "\n\n".join(
        docs
    )


@tool
def fts_search(
        query: str
) -> str:
    """
    Keyword retrieval
    """

    docs = fts_search_core(
        query
    )

    return "\n\n".join(
        docs
    )


@tool
def hybrid_search(
        query: str
) -> str:
    """
    Hybrid retrieval
    """

    docs = hybrid_search_core(
        query
    )

    return "\n\n".join(
        docs
    )