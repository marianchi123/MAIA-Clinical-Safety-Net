import json
from nlp_bridge import ClinicalEntityExtractor
from ddi_checker import DDIChecker

class MAIA_Orchestrator:
    def __init__(self):
        print("[M.A.I.A.] Инициализиране на системните модули...")
        self.extractor = ClinicalEntityExtractor(model_name="llama3")
        self.ddi_checker = DDIChecker()
        print("[M.A.I.A.] Системата е готова за работа.\n")

    def process_clinical_note(self, doctor_text: str) -> str:
        """
        Основен пайплайн: Приема свободен текст, извлича данни и проверява за рискове.
        """
        print("-> СТЪПКА 1: Анализ на клиничния текст (NLP)...")
        extracted_data = self.extractor.extract_entities(doctor_text)
        
        # Проверка за грешки от езиковия модел
        if "error" in extracted_data:
            return f"❌ Системна грешка при извличане: {extracted_data['error']}"

        # Обединяваме всички лекарства (текущи и предложени) за DDI проверка
        all_medications = extracted_data.get("current_medications", []) + \
                          extracted_data.get("proposed_medications", [])

        print(f"-> СТЪПКА 2: Извлечени медикаменти за проверка: {all_medications}")
        print("-> СТЪПКА 3: Проверка за лекарствени взаимодействия (NIH Database)...")
        
        # Подаваме списъка към модула за взаимодействия
        ddi_results = self.ddi_checker.check_interactions(all_medications)

        return self._format_final_report(extracted_data, ddi_results)

    def _format_final_report(self, nlp_data: dict, ddi_data: dict) -> str:
        """Форматира данните в лесен за четене медицински рапорт."""
        report = "\n" + "="*50 + "\n"
        report += "🩺 ДОКЛАД ОТ M.A.I.A. (Medical AI Assistant)\n"
        report += "="*50 + "\n\n"
        
        report += "📋 ПАЦИЕНТСКИ ПРОФИЛ (Извлечен):\n"
        report += f"  - Активни състояния: {', '.join(nlp_data.get('active_conditions', ['Няма данни']))}\n"
        report += f"  - Текуща терапия: {', '.join(nlp_data.get('current_medications', ['Няма']))}\n"
        report += f"  - Предложена терапия: {', '.join(nlp_data.get('proposed_medications', ['Няма']))}\n\n"

        report += "⚠️ АНАЛИЗ ЗА БЕЗОПАСНОСТ:\n"
        if ddi_data["status"] == "error":
            report += f"  [!] Грешка при връзка с базата данни: {ddi_data['message']}\n"
        elif ddi_data["total_interactions_found"] == 0:
            report += "  ✅ Не са открити известни лекарствени взаимодействия.\n"
        else:
            for interaction in ddi_data["interactions"]:
                icon = "🚨" if interaction["severity_level"] == "КРИТИЧНО" else "⚠️"
                report += f"  {icon} {interaction['severity_level']}: {' + '.join(interaction['drugs_involved'])}\n"
                report += f"     Описание: {interaction['clinical_description']}\n"
                report += f"     Източник: {interaction['source']}\n\n"
        
        if ddi_data.get("unmatched_drugs"):
            report += f"\n  [?] Неразпознати медикаменти: {', '.join(ddi_data['unmatched_drugs'])}\n"

        report += "="*50
        return report

# --- Стартиране на M.A.I.A. ---
if __name__ == "__main__":
    maia = MAIA_Orchestrator()
    
    # Симулираме реално диктуване от лекар
    clinical_input = """
    Днес преглеждам пациентка на 68 години. Тя има ревматоиден артрит и приема 
    Метотрексат (Methotrexate) всяка седмица. Има лека инфекция на дихателните 
    пътища, затова ще ѝ изпиша Триметоприм/Сулфаметоксазол (Trimethoprim).
    """
    
    print("Лекар: " + clinical_input.strip() + "\n")
    
    final_output = maia.process_clinical_note(clinical_input)
    print(final_output)