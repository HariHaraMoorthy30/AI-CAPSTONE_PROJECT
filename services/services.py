# app/routes/rag_routes.py

import os
import shutil
import uuid
import time
import traceback

from pathlib import Path

from fastapi import (
    UploadFile,
    File,
    HTTPException
)

from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from google.api_core.exceptions import (
    ResourceExhausted
)

from app.core.db import (
    get_vector_store
)

load_dotenv()

UPLOAD_DIR = "data"

Path(UPLOAD_DIR).mkdir(
    parents=True,
    exist_ok=True
)


def upload_pdf_ingestion(
        file: UploadFile = File(...)
):

    try:

        #####################################
        # Validate
        #####################################

        if not file.filename.endswith(".pdf"):

            raise HTTPException(
                status_code=400,
                detail="Only PDF files allowed"
            )

        #####################################
        # Save PDF
        #####################################

        file_path = os.path.join(
            UPLOAD_DIR,
            file.filename
        )

        with open(
                file_path,
                "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print(
            "PDF Saved:",
            file_path
        )

        #####################################
        # Load PDF
        #####################################

        loader = PyPDFLoader(
            file_path
        )

        docs = loader.load()

        print(
            "Pages:",
            len(docs)
        )

        #####################################
        # Metadata
        #####################################

        for doc in docs:

            doc.metadata.update({

                "source":
                file.filename,

                "page":
                doc.metadata.get(
                    "page",
                    0
                ),

                "document_extension":
                "pdf",

                "last_updated":
                os.path.getmtime(
                    file_path
                )

            })

        #####################################
        # Chunking
        #####################################

        splitter = RecursiveCharacterTextSplitter(

            chunk_size=1000,

            chunk_overlap=150
        )

        chunks = splitter.split_documents(
            docs
        )

        print(
            "Total Chunks:",
            len(chunks)
        )

        #####################################
        # Vector Store
        #####################################

        vector_store = get_vector_store(

            collection_name=
            "hr_support_desk",

            # IMPORTANT FIX
            pre_delete_collection=False
        )

        #####################################
        # Batch insert
        #####################################

        batch_size = 3

        inserted = 0

        failed = []

        total_batches = (

            len(chunks)
            + batch_size - 1

        ) // batch_size


        for i in range(
                0,
                len(chunks),
                batch_size
        ):

            batch = chunks[
                    i:i+batch_size
                    ]

            ids = [

                str(
                    uuid.uuid4()
                )

                for _ in batch
            ]

            success = False

            print(
                "\nBatch:",
                i//batch_size+1,
                "/",
                total_batches
            )

            for attempt in range(5):

                try:

                    vector_store.add_documents(

                        documents=batch,

                        ids=ids
                    )

                    inserted += len(
                        batch
                    )

                    success = True

                    print(
                        "Inserted:",
                        inserted
                    )

                    try:

                        count = (
                            vector_store
                            ._collection
                            .count()
                        )

                        print(
                            "DB Count:",
                            count
                        )

                    except Exception:
                        pass

                    break


                except ResourceExhausted:

                    wait = (
                        10 *
                        (
                                attempt+1
                        )
                    )

                    print(
                        f"Rate limit..."
                        f"waiting {wait}"
                    )

                    time.sleep(
                        wait
                    )


                except Exception as e:

                    print(
                        "Batch Error:"
                    )

                    print(e)

                    break


            if not success:

                failed.append(
                    i//batch_size+1
                )


            time.sleep(2)

        #####################################
        # Final verification
        #####################################

        print(
            "\nTotal Chunks:",
            len(chunks)
        )

        print(
            "Inserted:",
            inserted
        )

        print(
            "Failed:",
            failed
        )

        print(
            "========== COMPLETE =========="
        )

        return {

            "status":
            "success",

            "total_pages":
            len(docs),

            "total_chunks":
            len(chunks),

            "inserted":
            inserted,

            "failed_batches":
            failed
        }


    except Exception as e:

        print(
            traceback.format_exc()
        )

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )