import json
import requests
from typing import Dict, Any

class ClinicalEntityExtractor:
    def __init__(self, model_name: str = "llama3.1:latest"):
        self.api_url = "http://localhost:11434/api/generate"
        self.model = model_name
        self.system_prompt = """
        You are a strict clinical data extraction API. 
        Extract medical conditions, medications, and ALLERGIES/PAST ISSUES from the text.
        You must reply ONLY with a valid JSON object. Do not add any conversational text.
        
        CRITICAL RULES:
        1. Translate all extracted conditions and medications to standard English medical terms.
        2. Categorize the data strictly into the defined keys.
        
        Expected JSON format:
        {
          "active_conditions": ["Condition 1", "Condition 2"],
          "current_medications": ["Med 1"],
          "proposed_medications": ["Med 2"],
          "allergies_and_history": ["Allergy 1", "Past issue 1"]
        }
        
        If a category has no data found in the text, return an empty array [].
        """

    def extract_entities(self, doctor_text: str) -> Dict[str, Any]:
        prompt = f"Doctor's note & Past history: {doctor_text}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": self.system_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0 # ЗАДЪЛЖИТЕЛНО: Спира халюцинациите и "измислянето" на болести
            }
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            result_text = response.json().get("response", "")
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {"error": "Моделът не върна валиден JSON формат."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Грешка при връзка с Ollama: {e}"}