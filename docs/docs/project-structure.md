# Estrutura do projeto

```text
.
├── docs/
│   ├── docs/                 # Paginas deste site MkDocs
│   ├── .claude/              # Plano e referencias da OpenF1
│   └── dashboard.py          # Compatibilidade com o MVP anterior
├── src/f1/
│   ├── dashboard.py          # Composition root Streamlit
│   ├── domain/
│   │   ├── models.py         # Entidades e projecoes
│   │   ├── repositories.py  # Contratos dos repositorios
│   │   └── services.py      # Servico de dashboard
│   ├── ingestion/
│   │   ├── http_client.py    # Transporte HTTP e retry
│   │   └── openf1_client.py  # Adaptadores para a OpenF1
│   ├── processing/
│   │   └── lap_processor.py  # Transformacoes puras de voltas
│   └── utils/
│       ├── config.py         # Configuracao via ambiente
│       └── logger.py         # Logging padronizado
├── tests/
│   ├── integration/          # Testes opcionais contra a API real
│   └── unit/                 # Testes isolados
├── .env.example
├── mkdocs.yml
└── pyproject.toml
```

O pacote usa o layout `src/`; os testes nao dependem de arquivos locais ou da
disponibilidade da API.
