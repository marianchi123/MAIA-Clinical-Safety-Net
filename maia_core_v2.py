import json
from nlp_bridge import ClinicalEntityExtractor
from ddi_checker import DDIChecker
from patient_memory import PatientVectorMemory

class MAIA_Orchestrator:
    def __init__(self):
        print("[M.A.I.A.] Инициализиране на пълната екосистема...")
        self.memory = PatientVectorMemory()
        self.extractor = ClinicalEntityExtractor(model_name="llama3")
        self.ddi_checker = DDIChecker()
        print("[M.A.I.A.] Всички системи са онлайн.\n")

    def process_clinical_visit(self, patient_id: str, doctor_note: str) -> str:
        """
        Пълният цикъл: Памет -> Извличане (NLP) -> Безопасност (DDI) -> Доклад
        """
        print(f"-> СТЪПКА 1: Извличане на досие за пациент [{patient_id}]...")
        
        # 1. Търсим релевантна история спрямо текущото оплакване
        past_history = self.memory.retrieve_context(patient_id=patient_id, query=doctor_note)
        
        # 2. Подготвяме "обогатения" контекст
        history_text = " ".join(past_history) if past_history else "Няма намерени релевантни минали записи."
        
        enriched_prompt = f"""
        PAST MEDICAL HISTORY: {history_text}
        CURRENT DOCTOR'S NOTE: {doctor_note}
        
        Extract all conditions and medications combining both past history and the current note.
        """
        
        print("-> СТЪПКА 2: Анализ на комбинираните данни (Обогатен NLP мост)...")
        extracted_data = self.extractor.extract_entities(enriched_prompt)
        
        if "error" in extracted_data:
            return f"❌ Системна грешка при извличане: {extracted_data['error']}"

        # 3. Обединяваме лекарствата за DDI проверка
        all_medications = extracted_data.get("current_medications", []) + \
                          extracted_data.get("proposed_medications", [])

        print(f"-> СТЪПКА 3: Проверка за взаимодействия между: {all_medications}...")
        ddi_results = self.ddi_checker.check_interactions(all_medications)

        # 4. Връщаме финалния доклад
        return self._format_final_report(patient_id, extracted_data, ddi_results, past_history)

    def _format_final_report(self, patient_id: str, nlp_data: dict, ddi_data: dict, history: list) -> str:
        """Обновен метод за форматиране, който включва и паметта."""
        report = "\n" + "="*55 + "\n"
        report += f"🩺 M.A.I.A. КЛИНИЧЕН ДОКЛАД | ПАЦИЕНТ: {patient_id}\n"
        report += "="*55 + "\n\n"
        
        if history:
            report += "🧠 ИЗВЛЕЧЕНА ПАМЕТ ОТ ДОСИЕТО:\n"
            for item in history:
                report += f"  - {item}\n"
            report += "\n"
        
        report += "📋 СИНТЕЗИРАН ПРОФИЛ:\n"
        report += f"  - Всички състояния: {', '.join(nlp_data.get('active_conditions', ['Няма']))}\n"
        report += f"  - Текуща терапия: {', '.join(nlp_data.get('current_medications', ['Няма']))}\n"
        report += f"  - Предложена терапия: {', '.join(nlp_data.get('proposed_medications', ['Няма']))}\n\n"

        report += "⚠️ DDI АНАЛИЗ ЗА БЕЗОПАСНОСТ:\n"
        if ddi_data["status"] == "error":
            report += f"  [!] Грешка при връзка с базата: {ddi_data['message']}\n"
        elif ddi_data["total_interactions_found"] == 0:
            report += "  ✅ Не са открити известни лекарствени взаимодействия.\n"
        else:
            for interaction in ddi_data["interactions"]:
                icon = "🚨" if interaction["severity_level"] == "КРИТИЧНО" else "⚠️"
                report += f"  {icon} {interaction['severity_level']}: {' + '.join(interaction['drugs_involved'])}\n"
                report += f"     Причина: {interaction['clinical_description']}\n\n"

        report += "="*55
        return report

# --- Тестване на пълната екосистема ---
if __name__ == "__main__":
    maia = MAIA_Orchestrator()
    
    # 1. Записваме нещо в паметта (ако не е записано вече от предишния скрипт)
    # maia.memory.add_patient_record("P-999", "rec_1", "Пациентът е на поддържаща терапия с Варфарин.")
    
    # 2. Лекарят въвежда само НОВОТО оплакване
    current_note = "Пациентът има силни болки в гърба, ще му предпиша Ибупрофен 400мг."
    
    print("\n[Вход от лекаря]: " + current_note + "\n")
    
    # 3. Стартираме процеса
    output = maia.process_clinical_visit(patient_id="P-999", doctor_note=current_note)
    print(output)