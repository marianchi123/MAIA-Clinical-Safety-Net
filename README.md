# M.A.I.A. – A Hybrid Neuro-Symbolic Clinical Safety Net

## The Inspiration
Doctors today are completely overwhelmed. When you have only 10 minutes per patient, it’s terrifyingly easy to overlook a past allergy or miss a complex Drug-Drug Interaction (DDI). These human errors can be fatal, but they are entirely preventable. I wanted to build an AI "co-pilot" that acts as an invisible safety net for doctors. However, I had one absolute non-negotiable rule: patient data must never leave the room. Sending sensitive health records to a cloud API wasn't an option.

## What it does
M.A.I.A. (Medical Artificial Intelligence Assistant) is an intelligent, air-gapped EHR interface that utilizes a Hybrid Neuro-Symbolic architecture. A doctor simply types in their clinical notes and proposed treatments. In the background, M.A.I.A.:

1. Extracts active conditions and medications using local NLP.
2. Checks the patient's long-term vector memory for past visits and undocumented allergies.
3. The Deterministic Gate: Passes the data through a hardcoded Knowledge Graph for zero-fault medical logic.
4. The Probabilistic Inspector: Runs a secondary semantic AI check for edge-case interactions.

If a doctor prescribes Ibuprofen to a patient whose past records show Bronchial Asthma, M.A.I.A.’s deterministic gate slams on the brakes. It then uses a precise RAG system to scan official medical protocol PDFs and suggests a safe alternative (like Paracetamol) on the spot.

## How I built it
I wanted to prove that enterprise-level AI healthcare solutions don't need massive server farms. I built the entire architecture to run 100% locally on my ASUS TUF A15 laptop. The frontend is built with Streamlit for a clean, responsive UI. The brain is powered by Llama 3.1, hosted locally via Ollama. For the memory, I designed a dual-database architecture using ChromaDB: one vector space acts as the patient's persistent medical record (EHR), and the second acts as the medical guideline library (RAG). A custom Python orchestrator ties the neural networks (NLP, RAG) and symbolic logic (Knowledge Graph) together.

## Challenges I ran into
The biggest headache was a fundamental realization: LLMs are inherently probabilistic, but medical safety requires determinism. Early in development, the system relied purely on Vector Search (RAG) to catch Drug-Drug Interactions. I quickly realized that a 99% accuracy rate isn't good enough in healthcare; AI hallucinations or poor cosine similarity matches could be fatal. This led to a major architectural pivot. I stopped relying on the AI for strict logical blocks and engineered the Hybrid Neuro-Symbolic gate. Now, critical contraindications are enforced by a rigid, hardcoded dictionary, relegating the Llama 3.1 model strictly to parsing text and summarizing advisory clinical guidelines at temperature 0.0.

## What's next for M.A.I.A.
The immediate next step is expanding M.A.I.A.'s modular hierarchy. I want to integrate an offline Voice-to-Text module so doctors can simply dictate their notes hands-free. Architecturally, I plan to transition the deterministic safety gate to utilize full, industry-standard medical ontologies like RxNorm and SNOMED CT. Finally, while running on edge hardware proves the air-gapped concept, the ultimate production goal is deploying M.A.I.A. on local, On-Premise hospital server clusters to eliminate thermal throttling and achieve sub-second latency at scale.
