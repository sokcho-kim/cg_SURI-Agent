# cg_SURI-Agent
병원 보험심사팀을 위한 AI 기반 RAG Assistant – 수가, 고시, 지침 자동 질의응답 지원

```
suri-agent/
├── README.md
├── .gitignore
├── data_pipeline/
│   ├── crawler/         # 심평원/요양기관 포털 크롤러
│   ├── cleaner/         # 기준 정제, 최신 기준 비교 모듈
│   └── db_schema/       # 수가/지침/사례 DB 구조 정의
├── rag_engine/
│   ├── embedder/        # 임베딩 및 벡터 저장
│   ├── retriever/       # hybrid search 구현
│   └── generator/       # LLM 응답 처리
├── app_interface/
│   ├── cli_demo/        # 콘솔용 데모
│   └── streamlit_demo/  # 학회 시연용 프론트
├── scripts/
│   └── run_pipeline.sh  # 전체 파이프라인 실행 스크립트
└── docs/
    └── 발표자료, 시스템 구성도 등
```