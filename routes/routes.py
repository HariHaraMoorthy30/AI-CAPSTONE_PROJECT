# app/routes/rag_routes.py

import os
import shutil
import uuid
import time
import traceback
from pydantic import BaseModel

from pathlib import Path

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from google.api_core.exceptions import ResourceExhausted
from app.Agents.agent import ask_agent
from app.core.db import get_vector_store
from app.Services.services_updated import upload_pdf_ingestion
load_dotenv()
class QueryRequest(BaseModel):
    question:str

router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG"]
)

UPLOAD_DIR = "data"

Path(UPLOAD_DIR).mkdir(
    parents=True,
    exist_ok=True
)


@router.post("/upload")

async def upload_pdf(file: UploadFile = File(...)):
    try:
        result = upload_pdf_ingestion(file)

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )
@router.post("/query")
async def chat_query(
        request:QueryRequest
)->dict:

    query=request.question

    answer=ask_agent(query)

    return {

        "answer":answer

    }
# # async def upload_pdf(
#     file: UploadFile = File(...)
# ):

#     try:

#         # ========================
#         # VALIDATE
#         # ========================

#         if not file.filename.endswith(".pdf"):

#             raise HTTPException(
#                 status_code=400,
#                 detail="Only PDF files are allowed"
#             )

#         # ========================
#         # SAVE FILE
#         # ========================

#         file_path = os.path.join(
#             UPLOAD_DIR,
        #     file.filename
        # )

        # with open(file_path, "wb") as buffer:

        #     shutil.copyfileobj(
        #         file.file,
        #         buffer
        #     )

        # print("PDF Saved:", file_path)

        # print(
        #     "========== INGESTION STARTED =========="
        # )

        # # ========================
        # # LOAD PDF
        # # ========================

        # loader = PyPDFLoader(file_path)

        # docs = loader.load()

        # print("Pages:", len(docs))

    #     # ========================
    #     # METADATA
    #     # ========================

    #     for doc in docs:

    #         doc.metadata.update({

    #             "source": file_path,

    #             "document_extension": "pdf",

    #             "page": doc.metadata.get(
    #                 "page"
    #             ),

    #             "last_updated":
    #             os.path.getmtime(
    #                 file_path
    #             )
    #         })

    #     # ========================
    #     # CHUNKING
    #     # Bigger chunks => fewer requests
    #     # ========================

    #     splitter = RecursiveCharacterTextSplitter(

    #         chunk_size=1500,

    #         chunk_overlap=200
    #     )

    #     chunks = splitter.split_documents(
    #         docs
    #     )

    #     print(
    #         "Total Chunks:",
    #         len(chunks)
    #     )

    #     # Optional:
    #     # limit during testing

    #     # chunks = chunks[:20]

    #     # ========================
    #     # VECTOR STORE
    #     # ========================

    #     vector_store = get_vector_store(
    #         collection_name=
    #         "hr_support_desk",
    #         pre_delete_collection=True
    #     )

    #     # ========================
    #     # BATCH INSERT
    #     # ========================

    #     batch_size = 10

    #     for i in range(
    #         0,
    #         len(chunks),
    #         batch_size
    #     ):

    #         batch = chunks[
    #             i:i + batch_size
    #         ]

    #         ids = [

    #             str(uuid.uuid4())

    #             for _ in batch
    #         ]

    #         retries = 3

    #         for attempt in range(retries):

    #             try:

    #                 print(
    #                     f"Inserting batch "
    #                     f"{i//batch_size+1}"
    #                 )

    #                 vector_store.add_documents(
    #                     documents=batch,
    #                     ids=ids
    #                 )

    #                 break

    #             except ResourceExhausted:

    #                 wait = (
    #                     20 *
    #                     (attempt + 1)
    #                 )

    #                 print(
    #                     f"Rate limit hit. "
    #                     f"Waiting {wait}s..."
    #                 )

    #                 time.sleep(wait)

    #         time.sleep(3)

    #     print(
    #         "Chunks Stored Successfully"
    #     )

    #     print(
    #         "========== INGESTION COMPLETED =========="
    #     )

    #     return {

    #         "status": "success",

    #         "message":
    #         "PDF uploaded and ingested successfully",

    #         "file_name":
    #         file.filename,

    #         "saved_path":
    #         file_path,

    #         "total_pages":
    #         len(docs),

    #         "total_chunks":
    #         len(chunks)
    #     }

    # except Exception as e:

    #     print(
    #         traceback.format_exc()
    #     )

    #     raise HTTPException(

    #         status_code=500,

    #         detail=str(e)
    #     )