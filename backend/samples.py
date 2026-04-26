"""
samples.py — Sample Abstracts for Demo
========================================
These appear as quick-load buttons in the UI so judges can demo
without typing anything. Pick abstracts that produce interesting interviews.
"""

from schemas import SampleText

SAMPLE_TEXTS = [
    SampleText(
        id="llm-rag",
        title="RAG-Based Knowledge System",
        preview="We built a retrieval-augmented generation system to reduce hallucinations in...",
        full_text=(
            "We developed a retrieval-augmented generation (RAG) pipeline to reduce hallucination "
            "rates in our enterprise LLM deployment. The system uses a vector database (Pinecone) "
            "to store and retrieve domain-specific embeddings at inference time, which are injected "
            "into the model's context window before generation. We evaluated on a proprietary Q&A "
            "benchmark and observed a 34% reduction in factual errors compared to a vanilla GPT-4 "
            "baseline, with latency overhead of under 200ms at p99. The architecture supports "
            "incremental index updates without full retraining, making it practical for rapidly "
            "changing knowledge bases."
        ),
    ),
    SampleText(
        id="ml-fraud",
        title="Real-Time Fraud Detection",
        preview="Our ML pipeline detects fraudulent transactions with sub-100ms latency using...",
        full_text=(
            "We present a real-time fraud detection system deployed across our payments infrastructure "
            "processing 40,000 transactions per second. The model is a gradient-boosted ensemble "
            "trained on 18 months of labeled transaction data, with features derived from behavioral "
            "biometrics, device fingerprinting, and graph-based relationship modeling between accounts. "
            "We use a two-stage architecture: a lightweight logistic regression for initial triage "
            "(sub-5ms) and a heavier XGBoost model for borderline cases. The system reduced false "
            "positive rates by 22% versus our previous rule-based system while maintaining 99.1% "
            "recall on confirmed fraud cases. Model drift is monitored via a Champion/Challenger "
            "framework with automated retraining triggers."
        ),
    ),
    SampleText(
        id="microservices",
        title="Microservices Migration",
        preview="We migrated our monolithic Rails app to a Kubernetes-orchestrated microservices...",
        full_text=(
            "Over 18 months, we decomposed a 12-year-old monolithic Ruby on Rails application into "
            "27 independently deployable microservices orchestrated on Kubernetes. The migration used "
            "a strangler fig pattern, routing traffic progressively to new services via an API gateway "
            "while keeping the monolith live. Each service owns its own PostgreSQL schema, with "
            "inter-service communication handled via gRPC for synchronous calls and Kafka for "
            "event-driven workflows. Post-migration, we achieved 99.97% uptime (up from 99.4%), "
            "reduced mean time to deploy from 45 minutes to under 3 minutes, and enabled independent "
            "team ownership of services. The primary challenge was managing distributed transactions "
            "and data consistency across service boundaries."
        ),
    ),
]
