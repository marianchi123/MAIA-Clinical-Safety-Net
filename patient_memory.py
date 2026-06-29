import chromadb
from chromadb.utils import embedding_functions
import uuid

class PatientVectorMemory:
    def __init__(self, db_path="./patient_records_db"):
        print("[Memory] Connecting to persistent patient database...")
        # Указваме на ChromaDB да записва данните на диска
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="patient_profiles",
            embedding_function=self.embedding_fn
        )

    def add_patient_record(self, patient_id: str, clinical_text: str):
        """Запазва нов медицински запис в досието на конкретен пациент."""
        record_id = str(uuid.uuid4())[:8] # Генерира уникален код за всеки запис
        
        self.collection.add(
            documents=[clinical_text],
            metadatas=[{"patient_id": patient_id}],
            ids=[f"{patient_id}_{record_id}"]
        )
        print(f"[Memory] Successfully saved new record for {patient_id}.")

    def retrieve_context(self, patient_id: str, query: str, n_results=3) -> list:
        """Търси в предишните записи на пациента за свързани с текущия проблем симптоми."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"patient_id": patient_id} # Филтрираме паметта САМО за този пациент
            )
            
            if results and results['documents'] and results['documents'][0]:
                return results['documents'][0]
        except Exception as e:
            print(f"[Memory Error] {e}")
            
        return []