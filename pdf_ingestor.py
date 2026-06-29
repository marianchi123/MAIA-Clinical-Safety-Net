import os
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader

class MedicalPDFIngestor:
    def __init__(self, db_path="./maia_guidelines_db"):
        print(f"[Ingestor] Connecting to persistent vector database at {db_path}...")
        # Свързване с правилната папка за медицинските гайдлайни
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Създаваме или отваряме колекцията за медицински протоколи
        self.collection = self.client.get_or_create_collection(
            name="medical_protocols",
            embedding_function=self.embedding_fn
        )

    def process_library(self, library_path="./medical_library"):
        if not os.path.exists(library_path):
            print(f"❌ Error: Library folder '{library_path}' not found!")
            return

        pdf_files = [f for f in os.listdir(library_path) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"⚠ No PDF files found in '{library_path}'.")
            return

        print(f"📚 Found {len(pdf_files)} PDF protocol(s). Processing...")

        for file_name in pdf_files:
            file_path = os.path.join(library_path, file_name)
            print(f"📖 Extracting text from: {file_name}...")
            
            try:
                reader = PdfReader(file_path)
                full_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                if not full_text.strip():
                    print(f"⚠ Warning: {file_name} is empty or unreadable.")
                    continue

                # Нарязваме текста на отделни параграфи за по-прецизно RAG търсене
                chunks = [chunk.strip() for chunk in full_text.split("\n\n") if chunk.strip()]
                
                if not chunks:
                    continue

                # Подготвяме данните за ChromaDB
                ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"source": file_name} for _ in chunks]

                # Записваме параграфите във векторната база данни
                self.collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Successfully ingested {len(chunks)} chunks from {file_name}.")

            except Exception as e:
                print(f"❌ Error processing {file_name}: {e}")

if __name__ == "__main__":
    # Уверяваме се, че стартираме инжектора от главната директория на проекта
    ingestor = MedicalPDFIngestor()
    ingestor.process_library()
    print("\n🚀 Database update complete! M.A.I.A. clinical guidelines are ready.")