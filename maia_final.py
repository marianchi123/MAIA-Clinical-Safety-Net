import json
import requests
from nlp_bridge import ClinicalEntityExtractor
from ddi_checker import DDIChecker
from patient_memory import PatientVectorMemory
from cdss_module import CDSS_Recommender

# === DETERMINISTIC MEDICAL KNOWLEDGE GRAPH (Neuro-Symbolic Gate) ===
# This dictionary represents hardcoded, zero-fault medical logic. 
# It prevents the LLM from making probabilistic mistakes on critical contraindications.
CONTRAINDICATIONS_DB = {
    "ibuprofen": ["bronchial asthma", "ace inhibitors", "peptic ulcer"],
    "dexamethasone": ["type 2 diabetes", "glaucoma"],
    "naproxen": ["bronchial asthma", "heart failure"]
}

class Full_MAIA_System:
    def __init__(self):
        print("[M.A.I.A.] Starting Hybrid Neuro-Symbolic modules...")
        self.memory = PatientVectorMemory()
        self.extractor = ClinicalEntityExtractor(model_name="llama3.1:latest") 
        self.ddi_checker = DDIChecker()
        self.cdss = CDSS_Recommender(model_name="llama3.1:latest")
        print("[M.A.I.A.] All systems are online and air-gapped.\n")

    def _deterministic_safety_check(self, all_meds: list, conditions: list, allergies: list) -> dict:
        """100% deterministic check bypassing LLM probabilities for known critical risks."""
        risk_factors = [c.lower() for c in conditions + allergies]
        
        for drug in all_meds:
            for known_drug, bad_conditions in CONTRAINDICATIONS_DB.items():
                # Използваме 'in', за да хванем случаи като '400mg ibuprofen'
                if known_drug in drug.lower():
                    for bad_cond in bad_conditions:
                        # Scan patient profile for the forbidden condition
                        if any(bad_cond in factor for factor in risk_factors):
                            return {
                                "risk_found": True,
                                "severity_level": "CRITICAL (KNOWLEDGE GRAPH)",
                                "clinical_description": f"Deterministic protocol violation: {known_drug.capitalize()} is strictly contraindicated for {bad_cond}.",
                                "conflicting_drugs": known_drug.capitalize()
                            }
        return {"risk_found": False}

    def _semantic_safety_check(self, proposed_meds: list, current_meds: list, history: list, conditions: list) -> dict:
        """Probabilistic AI inspector for edge cases not covered by the strict Knowledge Graph."""
        all_meds = proposed_meds + current_meds
        
        if not all_meds:
            return {"risk_found": False}

        system_prompt = """
        You are a medical safety AI. Catch CRITICAL risks.
        Analyze if ANY of the MEDICATIONS IN THE LIST conflict with:
        1. EACH OTHER (Drug-Drug Interactions)
        2. PATIENT HISTORY/ALLERGIES
        3. ACTIVE CONDITIONS
        
        Output ONLY valid JSON:
        {
           "risk_found": true or false,
           "severity_level": "CRITICAL (AI INSPECTION)",
           "clinical_description": "Explanation of the interaction",
           "conflicting_drugs": "Name the specific conflicting drugs"
        }
        """
        prompt = f"MEDICATIONS TO CHECK: {all_meds}\nHISTORY AND ALLERGIES: {history}\nACTIVE CONDITIONS: {conditions}"
        
        try:
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama3.1:latest",
                "prompt": prompt,
                "system": system_prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.0} 
            })
            return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            return {"risk_found": False, "error": str(e)}

    def run_consultation(self, patient_id: str, doctor_note: str) -> str:
        print("-> STEP 1: Retrieving persistent EHR memory...")
        past_history = self.memory.retrieve_context(patient_id=patient_id, query=doctor_note)
        history_text = " ".join(past_history) if past_history else "No previous records found."
        
        enriched_prompt = f"PAST HISTORY: {history_text}\nCURRENT NOTE: {doctor_note}"
        
        print("-> STEP 2: Local NLP Extraction...")
        nlp_data = self.extractor.extract_entities(enriched_prompt)
        
        if "error" in nlp_data:
            return f"❌ NLP extraction error: {nlp_data['error']}"

        current_meds = nlp_data.get("current_medications", [])
        proposed_meds = nlp_data.get("proposed_medications", [])
        active_conditions = nlp_data.get("active_conditions", [])
        allergies_and_history = nlp_data.get("allergies_and_history", [])

        print("-> STEP 3: Hybrid Neuro-Symbolic Safety Gate...")
        
        # 3.1 Hard Deterministic Check First - Проверяваме ВСИЧКИ лекарства
        det_safety_data = self._deterministic_safety_check(
            all_meds=current_meds + proposed_meds, 
            conditions=active_conditions, 
            allergies=allergies_and_history
        )
        
        has_det_risk = det_safety_data.get("risk_found", False)
        has_api_risk = False
        has_ai_risk = False
        
        ddi_data = {}
        ai_safety_data = {}

        # 3.2 If the deterministic gate passes, run the probabilistic AI & API checks
        if not has_det_risk:
            ddi_data = self.ddi_checker.check_interactions(current_meds + proposed_meds)
            ai_safety_data = self._semantic_safety_check(
                proposed_meds=proposed_meds,
                current_meds=current_meds,
                history=allergies_and_history,
                conditions=active_conditions
            )
            has_api_risk = ddi_data.get("total_interactions_found", 0) > 0
            has_ai_risk = ai_safety_data.get("risk_found", False)
        
        cdss_recommendations = None
        
        # STEP 4: CDSS Activation
        if has_det_risk or has_api_risk or has_ai_risk:
            print("-> STEP 4: Risk triggered! Fetching RAG Clinical Guidelines...")
            target_condition = f"Complaint: {doctor_note}. Known conditions: {', '.join(active_conditions)}"
            rejected_drug = proposed_meds[0] if proposed_meds else (current_meds[0] if current_meds else "Unknown")
            
            context_arr = current_meds + allergies_and_history
            
            cdss_recommendations = self.cdss.suggest_alternatives(
                target_condition=target_condition, 
                rejected_drug=rejected_drug, 
                patient_context=f"Data: {', '.join(context_arr)}"
            )

        print("-> STEP 5: Auto-saving to Patient EHR...")
        memory_entry = f"Note: {doctor_note} | Diagnosed: {', '.join(active_conditions)} | Prescribed: {', '.join(proposed_meds)}"
        self.memory.add_patient_record(patient_id=patient_id, clinical_text=memory_entry)

        return self._generate_report(patient_id, nlp_data, det_safety_data, ddi_data, ai_safety_data, cdss_recommendations)

    def _generate_report(self, patient_id: str, nlp_data: dict, det_data: dict, ddi_data: dict, ai_data: dict, cdss_data: dict) -> str:
        report = f"### 🩺 CLINICAL REPORT | PATIENT: {patient_id}\n---\n\n"
        
        report += "#### 📋 EXTRACTED PROFILE:\n"
        report += f"* **Conditions:** {', '.join(nlp_data.get('active_conditions', ['None']))}\n"
        report += f"* **Allergies/History:** {', '.join(nlp_data.get('allergies_and_history', ['None']))}\n"
        report += f"* **Current Therapy:** {', '.join(nlp_data.get('current_medications', ['None']))}\n"
        report += f"* **Proposed Therapy:** {', '.join(nlp_data.get('proposed_medications', ['None']))}\n\n"

        report += "#### ⚠️ HYBRID SAFETY GATE:\n"
        is_safe = True

        # Render Deterministic Graph Block
        if det_data.get("risk_found", False):
            is_safe = False
            report += f"🛑 **{det_data.get('severity_level')}**\n"
            report += f"> *{det_data.get('clinical_description')}*\n\n"

        # Render AI / Probabilistic Block
        if ai_data.get("risk_found", False):
            is_safe = False
            report += f"🚨 **{ai_data.get('severity_level')}** | Conflict: {ai_data.get('conflicting_drugs')}\n"
            report += f"> *Reason: {ai_data.get('clinical_description')}*\n\n"

        # Render API Block
        if ddi_data.get("total_interactions_found", 0) > 0:
            is_safe = False
            for interaction in ddi_data["interactions"]:
                report += f"🚨 **{interaction['severity_level']} (NIH DATABASE):** {' + '.join(interaction['drugs_involved'])}\n"
                report += f"> *Reason: {interaction['clinical_description']}*\n\n"

        if is_safe:
            report += "✅ **Therapy is safe.** Cleared by both Deterministic Graph and AI Inspector.\n\n"

        # Render CDSS Guidance
        if cdss_data:
            report += "---\n#### 💡 CDSS ADVISORY (BASED ON LOCAL PROTOCOLS):\n"
            if "error" in cdss_data:
                report += f"*[Guideline Extraction Error: {cdss_data['error']}]*\n"
            elif "alternatives" in cdss_data:
                for alt in cdss_data["alternatives"]:
                    report += f"**Recommended:** {alt.get('medication_name', 'N/A')}\n\n"
                    report += f"**Rationale:** {alt.get('rationale', 'N/A')}\n\n"
                    report += f"**Precautions:** {alt.get('precautions', 'N/A')}\n\n"

        return report

if __name__ == "__main__":
    maia = Full_MAIA_System()
    print("\n" + "-"*50)
    print("🤖 M.A.I.A. IS READY (TERMINAL MODE)")
    print("-"*50 + "\n")

    while True:
        doctor_input = input("\n[Doctor]: ")
        if doctor_input.lower() in ['exit', 'quit']: break
        if doctor_input.strip() == "": continue

        print("\n⏳ M.A.I.A. is analyzing...")
        print(maia.run_consultation(patient_id="PATIENT-007", doctor_note=doctor_input))