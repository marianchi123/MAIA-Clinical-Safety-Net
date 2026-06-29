# 🩺 M.A.I.A. | Medical Artificial Intelligence Assistant

**A Hybrid Neuro-Symbolic Clinical Safety Net**

M.A.I.A. is an entirely air-gapped, privacy-first Electronic Health Record (EHR) interface. It acts as a safety net for doctors, preventing fatal Drug-Drug Interactions (DDIs) by combining deterministic medical logic with probabilistic AI reasoning.

## 🚀 Key Features
* **100% Local Execution:** No patient data ever leaves the room. Powered entirely on edge hardware.
* **Hybrid Neuro-Symbolic Gate:** Uses a hardcoded, zero-fault Knowledge Graph to block critical contraindications instantly, independent of LLM hallucinations.
* **Semantic AI Inspector:** A secondary Llama 3.1 module that analyzes edge cases and complex interactions.
* **RAG-based CDSS:** Queries clinical guideline PDFs locally to suggest safe alternative treatments.

## 🛠️ Architecture & Tech Stack
* **Frontend:** Streamlit
* **LLM Engine:** Ollama (Llama 3.1)
* **Vector Storage:** ChromaDB (Dual-database setup for Patient EHR & Medical Protocols)
* **Logic:** Python

## ⚙️ Installation & Usage
1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/MAIA-Clinical-Safety-Net.git](https://github.com/your-username/MAIA-Clinical-Safety-Net.git)
   cd MAIA-Clinical-Safety-Net