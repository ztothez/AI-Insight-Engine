import asyncio
import fitz
from app.db.database import async_session
from app.services.embedding_service import ingest_document

BOOKS = [
    {"path": "/home/ztothez/Documents/Learning/Coding/cleancodeinpython.pdf", "doc_id": "clean_code_python"},
    {"path": "/home/ztothez/Documents/Learning/Coding/handsonsoftwareengineeringwithpython.pdf", "doc_id": "software_engineering_python"},
    {"path": "/home/ztothez/Documents/Learning/Coding/guidebook_handbook_Secure_Agile.pdf", "doc_id": "secure_agile"},
    {"path": "/home/ztothez/Documents/Learning/Coding/Secure_Coding_Principles_and_Practices.pdf", "doc_id": "secure_coding_principles"},
    {"path": "/home/ztothez/Documents/Learning/Hacking/web_application_hackers_handbook_finding_and_exploiting_security_flaws.pdf", "doc_id": "web_app_hackers_handbook"},
    {"path": "/home/ztothez/Documents/Learning/Hacking/security_engineering_a_guide_to_building_dependable_distributed_systems.pdf", "doc_id": "security_engineering"},
    {"path": "/home/ztothez/Documents/Learning/Hacking/threat_modeling_designing_for_security.pdf", "doc_id": "threat_modeling"},
    {"path": "/home/ztothez/Documents/Learning/Hacking/websecurity.pdf", "doc_id": "web_security"},
]

async def main():
    # STEP 1: Open a database session for the complete ingestion run.
    async with async_session() as db:
        for book in BOOKS:
            # STEP 2: Extract searchable text from each reference document.
            print(f"Ingesting {book['doc_id']}...")
            doc = fitz.open(book["path"])
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            # STEP 3: Chunk and store the document as vector-search evidence.
            embeddings = await ingest_document(text, book["doc_id"], db)
            print(f"✅ Stored {len(embeddings)} chunks for {book['doc_id']}")

asyncio.run(main())
