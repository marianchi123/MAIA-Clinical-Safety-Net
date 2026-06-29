import chromadb
import requests
import json

class CDSS_Recommender:
    def __init__(self, model_name="llama3.1:latest", db_path="./maia_guidelines_db"):
        print("[CDSS] Connecting to Clinical Guidelines Database...")
        self.model_name = model_name
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="medical_protocols")

    def suggest_alternatives(self, target_condition: str, rejected_drug: str, patient_context: str) -> dict:
        # 1. Извличане на точния параграф от PDF векторната база
        search_query = f"Treatment for {target_condition}. Avoid: {rejected_drug}."
        
        try:
            results = self.collection.query(
                query_texts=[search_query],
                n_results=1 # Взимаме само най-релевантния резултат
            )
            retrieved_context = " ".join(results['documents'][0]) if results and results['documents'] else "No specific guidelines found."
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

        # 2. ЖЕЛЯЗЕН SYSTEM PROMPT (Тук спираме халюцинациите)
        system_prompt = """
        You are a strict, highly accurate Clinical Decision Support System (CDSS).
        Your ONLY job is to extract the recommended alternative treatment from the provided CLINICAL GUIDELINES.

        CRITICAL RULES:
        1. READ THE GUIDELINES CAREFULLY. You MUST NOT recommend any drug that the text explicitly says is "contraindicated", "avoid", or can trigger bad reactions.
        2. DO NOT HALLUCINATE. If the text only suggests ONE alternative, output ONLY that ONE alternative. Do not invent a second one.
        3. Never recommend the REJECTED DRUG.
        
        Output MUST be valid JSON in this exact format:
        {
           "alternatives": [
               {
                   "medication_name": "Name of the drug",
                   "rationale": "Exact reason derived from the text",
                   "precautions": "Any warnings or monitoring mentioned in the text"
               }
           ]
        }
        """
        
        user_prompt = f"""
        TARGET CONDITION / COMPLAINT: {target_condition}
        REJECTED DRUG (DO NOT USE): {rejected_drug}
        PATIENT DATA: {patient_context}
        
        === CLINICAL GUIDELINES (YOUR ONLY SOURCE OF TRUTH) ===
        {retrieved_context}
        =======================================================
        """
        
        # 3. Изпращане на заявката към Llama 3.1
        try:
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": self.model_name,
                "prompt": user_prompt,
                "system": system_prompt,
                "format": "json",
                "stream": False,
                # Слагаме температурата на абсолютната нула за максимална прецизност
                "options": {"temperature": 0.0, "top_p": 0.1} 
            })
            return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            return {"error": f"LLM parsing error: {str(e)}"}