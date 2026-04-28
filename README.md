# FRI ReferatBot – Domain-Specific assistant for UL FRI Student Affairs Office


> A RAG-based chatbot that answers student administrative questions for the UL FRI Student Affairs Office (Referat), serving enrolled students.

---

## Project Overview

General-purpose LLMs hallucinate when asked institution-specific questions they were not trained on. This project builds a domain-specific assistant grounded in a curated corpus of UL FRI administrative documents, FAQ pages, and study regulations. The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant passages before generating an answer, ensuring factual accuracy and traceability.

**Domain:** UL FRI Student Affairs Office  
**Languages:** Slovenian and English (bilingual corpus)

---

<img width="2280" height="1342" alt="image" src="https://github.com/user-attachments/assets/1167953a-6313-4f05-86db-30e8941dc7c5" />


## Install and run

Please run the script

```bash
sbatch run.sh
```

Once you see the following text appear:
```

██████╗░███████╗███████╗███████╗██████╗░░█████╗░████████╗  ██████╗░░█████╗░████████╗
██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝
██████╔╝█████╗░░█████╗░░█████╗░░██████╔╝███████║░░░██║░░░  ██████╦╝██║░░██║░░░██║░░░
██╔══██╗██╔══╝░░██╔══╝░░██╔══╝░░██╔══██╗██╔══██║░░░██║░░░  ██╔══██╗██║░░██║░░░██║░░░
██║░░██║███████╗██║░░░░░███████╗██║░░██║██║░░██║░░░██║░░░  ██████╦╝╚█████╔╝░░░██║░░░
╚═╝░░╚═╝╚══════╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░  ╚═════╝░░╚════╝░░░░╚═╝░░░


SSH tunnel command:
ssh -L 8080:wn203.arnes.si:8080 sh8397@hpc-login.arnes.si

Then open: http://localhost:8080
init GaMS model
Loading checkpoint shards: 100%|██████████|
Device set to use cuda
2026-04-28 17:40:50,118 - INFO - Load pretrained SentenceTransformer: intfloat/multilingual-e5-base
2026-04-28 17:40:55,809 - INFO - Load pretrained SentenceTransformer: intfloat/multilingual-e5-base
INFO:     Started server process [2438809]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
Running server on 0.0.0.0:8080

```

you are ready to go. Run the tunnel command and navigate to http://localhost:8080 to access the chatbot interface.

[Zaslonski_video_20260428_180534.webm](https://github.com/user-attachments/assets/f1a1b2a2-4ad5-4d21-a416-f5881379a9d8)



## Project status

* 20/03/2026: [Report #1](./report/report-1.pdf)


## Related Work

- [Lewis et al. (2020) — RAG original paper](https://arxiv.org/abs/2005.11401)
- [Gao et al. (2023) — RAG survey](https://arxiv.org/abs/2312.10997)
- [Es et al. (2023/2024) — RAGAS evaluation framework](https://arxiv.org/abs/2309.15217)
- [Neupane et al. (2024) — University chatbot with RAG (RAGAS score 0.96)](https://arxiv.org/abs/2405.08120)
- [Nguyen & Quan (2025) — URAG for university admissions](https://arxiv.org/abs/2501.16276)
- [UL FS chatbot — existing example at UL](https://www.fs.uni-lj.si)

---
