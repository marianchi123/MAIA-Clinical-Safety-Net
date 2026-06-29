import requests
from typing import List, Dict, Any

class DDIChecker:
    def __init__(self):
        self.rxnorm_base_url = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
        self.interaction_base_url = "https://rxnav.nlm.nih.gov/REST/interaction/list.json"

    def _get_rxcui(self, drug_name: str) -> str:
        try:
            response = requests.get(f"{self.rxnorm_base_url}?name={drug_name}")
            response.raise_for_status()
            data = response.json()
            if "idGroup" in data and "rxnormId" in data["idGroup"]:
                return data["idGroup"]["rxnormId"][0]
            return None
        except requests.exceptions.RequestException as e:
            print(f"[Грешка при връзка с RxNorm за {drug_name}]: {e}")
            return None

    def check_interactions(self, medication_list: List[str]) -> Dict[str, Any]:
        rxcuis = []
        unmatched_drugs = []
        for drug in medication_list:
            cui = self._get_rxcui(drug)
            if cui:
                rxcuis.append(cui)
            else:
                unmatched_drugs.append(drug)

        if len(rxcuis) < 2:
            return {"status": "success", "interactions": [], "unmatched": unmatched_drugs, "total_interactions_found": 0}

        rxcuis_string = "+".join(rxcuis)
        query_url = f"{self.interaction_base_url}?rxcuis={rxcuis_string}"

        try:
            response = requests.get(query_url)
            response.raise_for_status()
            interaction_data = response.json()
            return self._parse_interaction_data(interaction_data, unmatched_drugs)
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e), "total_interactions_found": 0}

    def _parse_interaction_data(self, data: Dict, unmatched: List[str]) -> Dict[str, Any]:
        parsed_results = []
        if "fullInteractionTypeGroup" in data:
            for group in data["fullInteractionTypeGroup"]:
                for interaction_type in group["fullInteractionType"]:
                    for interaction in interaction_type["interactionPair"]:
                        severity = interaction.get("severity", "UNKNOWN").upper()
                        description = interaction.get("description", "Няма налично описание.")
                        drug1 = interaction["interactionConcept"][0]["minConceptItem"]["name"]
                        drug2 = interaction["interactionConcept"][1]["minConceptItem"]["name"]
                        
                        parsed_results.append({
                            "drugs_involved": [drug1, drug2],
                            "severity_level": "КРИТИЧНО" if severity == "HIGH" else "ВНИМАНИЕ",
                            "clinical_description": description,
                            "source": group["sourceName"]
                        })

        return {
            "status": "success",
            "total_interactions_found": len(parsed_results),
            "interactions": parsed_results,
            "unmatched_drugs": unmatched
        }