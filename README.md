# FRI ReferatBot – Domain-Specific assistant for UL FRI Student Affairs Office


> A RAG-based chatbot that answers student administrative questions for the UL FRI Student Affairs Office (Referat), serving enrolled students.

---

## Project Overview

General-purpose LLMs hallucinate when asked institution-specific questions they were not trained on. This project builds a domain-specific assistant grounded in a curated corpus of UL FRI administrative documents, FAQ pages, and study regulations. The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant passages before generating an answer, ensuring factual accuracy and traceability.

**Domain:** UL FRI Student Affairs Office  
**Languages:** Slovenian and English (bilingual corpus)

---


## Related Work

- [Lewis et al. (2020) — RAG original paper](https://arxiv.org/abs/2005.11401)
- [Gao et al. (2023) — RAG survey](https://arxiv.org/abs/2312.10997)
- [Neupane et al. (2024) — University chatbot with RAG (RAGAS score 0.96)](https://arxiv.org/abs/2405.08120)
- [Nguyen & Quan (2025) — URAG for university admissions](https://arxiv.org/abs/2501.16276)
- [Es et al. (2023/2024) — RAGAS evaluation framework](https://arxiv.org/abs/2309.15217)
- [UL FS chatbot — existing example at UL](https://www.fs.uni-lj.si)
