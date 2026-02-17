# **Shukraditya Bose**

Kolkata, IN | [LinkedIn](https://www.linkedin.com/in/shukraditya-bose-074764247/) | \+91-7003693207| [shukra12bose@gmail.com](mailto:shukra12bose@gmail.com) | [https://github.com/shukraditya](https://github.com/shukraditya)   
**EDUCATION**  
**Vellore Institute of Technology**	**Vellore, IN**  
*Integrated M.Tech.  in Computer Science with Specialisation in Data Science* 	

* Cumulative GPA: **9.05/10.00**  
* Awards: Department Merit List

**WORK EXPERIENCE**  
**Memfold AI	Bangalore, IN**  
*AI Engineering Intern	August 2025-December 2025*

* **Developed** a standalone retrieval‑augmented generation (RAG) pipeline with a Dockerized local vector database, **integrated** BM25‑based lexical retrieval with dense embeddings, and **implemented** hybrid search and reranking to significantly reduce irrelevant context for multi‑hop, knowledge‑heavy queries.  
* **Diagnosed** low‑confidence, noisy retrieval by **evaluating** chunking, BM25 scores, similarity thresholds, and rerank signals, then **devised** query‑understanding and rerank layers that improved answer precision and confidence calibration for internal users.  
* **Integrated** and **debugged** the Tiptap rich‑text editor with the RAG backend, **designed** custom extensions and persistence to enable structured authoring of knowledge content that feeds directly into the retrieval pipeline.  
* **Built** Slack, Discord, and Gmail bots that **utilized** the RAG services to deliver contextual answers inside user workflows, **coordinated** API/webhook integrations, and **analyzed** interaction logs to iteratively **improve** retrieval behavior and response quality

**Sarvam AI	Bangalore, IN**  
*Vision Language Model Intern	May 2025-August 2025*

* **Architected** end-to-end multilingual OCR pipeline for Indic scripts, orchestrating data transformation workflows across Qwen 2.5VL and Gemma 3 models while systematizing annotation processes for 120k+ pages spanning 12 languages.  
* **Engineered** **Policy Optimisation** reward systems and fine-tuned YOLO models for Gujarati handwritten text recognition, **implementing** PyTorch/HuggingFace training pipelines and **benchmarking** model performance using Character Error Rate metrics to optimize accuracy by 15%  
* Integrated Langfuse observability platform with existing ClickHouse infrastructure, replacing legacy `@aspan_trace` decorators across 15+ microservices and streamlining distributed tracing workflows to enhance system monitoring and error detection capabilities  
* **Developed** experimental **Knowledge Graph-enhanced RAG** system, combining structured graph reasoning with semantic vector search to improve retrieval accuracy and facilitate contextually-aware question answering for domain-specific knowledge queries

**Samsung R\&D Institute	 Bangalore, IN**  
*Virtual Intern	January 2025-June 2025*

* **Developed and implemented an adaptive regularization algorithm for continual learning,** enhancing neural network performance by dynamically balancing stability and plasticity using Fisher information matrices.  
* Optimized and validated model training processes by integrating online exponential moving average (EMA) updates, resulting in improved resistance to catastrophic forgetting across sequential tasks.  
* Benchmarked and compared the proposed method against established **baselines (EWC, MAS),** demonstrating superior adaptability and efficiency through rigorous experimental evaluation and hyperparameter tuning.

**KalkiNi	 Vellore, IN**  
*Machine Learning Intern	March 2024-December 2024*

* **Led the development** of a violence detection system utilising CCTV footage, employing deep learning techniques. Engineering a model integrating MobileNet and Bi-Directional LSTM, achieving **significant enhancement in accuracy from 84% to 92%.**  
* **Conducted extensive literature review** to identify shortcomings in existing models, informing strategic improvements. Tested and refined implementations, **reducing local running time by over 15%**, with further optimization planned for cloud deployment.

**PROJECTS**  
**Skin Cancer Detection	\[[https://github.com/shukraditya/skin-cancer-detection](https://github.com/shukraditya/skin-cancer-detection)**\]

* **Engineered a robust skin cancer detection** system using machine learning frameworks, including OpenCV, Keras, PyTorch, and TensorFlow. Utilised models such as VGG16 and ResNet, achieving an accuracy **milestone of 85.02%** through meticulous optimization and innovation.  
* **Innovated** by integrating advanced techniques like Sobel Operator and Gradient Filling for area masking and selection, **significantly reducing processing time** while maintaining high accuracy.   
* Conducted thorough **literature review** to pinpoint existing challenges and implemented enhancements, resulting in **over 4% improvement** in accuracy metrics.  
* **Planned future deployment** of the skin cancer detection system on cloud infrastructure to facilitate real-time assistance for doctors during diagnosis. This initiative aims to **enhance accessibility and scalability**, ensuring **timely and accurate medical insights** in clinical settings.

**Self Improving Conversational Agent Framework \[[https://github.com/shukraditya/self-improving-agent](https://github.com/shukraditya/self-improving-agent)\]**

* Built a **self-improving conversational agent framework** executing multi-turn debt collection simulations across 12 behavioral and quality metrics, delivering **40–50% performance gains in extended runs** while maintaining full experimental reproducibility through structured artifacts.  
* **Engineered a hierarchical memory architecture** combining fine-grained episodic traces with long-term semantic compression, enabling the agent to reuse stable dialog strategies and achieve \~35% faster adaptation to new conversation styles and failure modes.  
* **Designed and deployed a DGM-inspired evolutionary optimization loop** where top-performing prompt “parents” generate multiple “child” variants; low performers pruned and high performers retained, **automating prompt improvement efficiency** by 4× over manual tuning cycles.  
* **Conducted** a 2-iteration, 4-persona experimental study on Indian debt-collection dialogs using Gemini 2.5 Flash (\~48 minutes end-to-end), achieving **\+2.0% score increase** (0.921 → 0.940), 62% reduction in repetitive phrasing, **14% boost in conversation quality**, and ≥0.95 consistency across 10 of 12 key metrics including empathy, engagement, and resolution.

**Chain-of-Thought Steering via Supervised Finetuning for addition operation (Blog Link: [Can LLMs do math?](https://shukraditya.notion.site/can-llms-do-math?pvs=74))\[[https://github.com/shukraditya/arithmeticLLM](https://github.com/shukraditya/arithmeticLLM)\]**

* **Investigated why small (\<50B) LLMs struggle with arithmetic** by decomposing failure modes into tokenization effects, length generalization limits, and parameter-efficiency tradeoffs, positioning LLMs as pattern recognizers rather than true algorithmic solvers.​  
* Built a 1,465-example multi-addend dataset using DeepSeek-R1 1.5B and isolated 1,176 incorrect completions with full thought traces and structured error annotations, enabling fine-grained diagnosis of addition mistakes.​  
* **Deployed a critic pipeline with Gemini 2.0 Flash (thinking)** on the 1,176 error cases, recovering correct answers for 1,051 examples and **generating corrected Chain-of-Thought traces** that explicitly fix place-value and carry-over reasoning.​  
* **Constructed supervised finetuning datasets** for DeepSeek-R1 Qwen 1.5B and Llama 8B distills, training only on response tokens so models learn to transform faulty reasoning into correct reasoning and answers, and **showed that the finetuned 1.5B model’s errors shrink to mostly single-digit deviations** while **outperforming the 8B model** on held-out additions.​  
* Incorporated recent interpretability results showing that **reasoning models often produce unfaithful, post-hoc CoT and that RL-based “honesty training”** quickly plateaus, arguing that naïve CoT steering has hard limits and motivating architectures and tokenization changes over pure prompt- or RL-only fixes

**Bengali Subword Tokenizer \[[https://github.com/shukraditya/bangla-tokenizer](https://github.com/shukraditya/bangla-tokenizer)\]**

* **Trained a Bangla-specific BPE/WordPiece tokenizer** on 417k+ bdnews24 news articles spanning politics, sports, and world news, ensuring broad coverage of real-world Bengali usage and morphology.​  
* **Learned a dedicated subword vocabulary tailored to Bengali script** and compounding, significantly reducing reliance on generic multilingual tokenization that often over-fragments words and harms downstream model efficiency.​  
* **Cleaned and structured the corpus by extracting** and using both titles and contents fields, creating a high-signal training set for robust Bangla tokenization rather than relying on small or synthetic datasets.​  
* Focused on Bengali as a mother tongue to **address underrepresentation of low-resource languages** in mainstream LLM tooling, improving token-level treatment for Bangla users who otherwise inherit suboptimal English-centric tokenizers.

**SKILLS & INTERESTS**  
**Skills:** Tensorflow, PyTorch, Keras | OpenCV, YOLO  | Transformers| Natural Language Processing | Numpy, Pandas, Matplotlib, Seaborn | R | Java | C/C++ | SQL, Postgres | Tableau | AWS, GCP | Docker

**Interests:** Photography | Cybersecurity | STEM Outreach | Football
