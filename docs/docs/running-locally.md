# Como rodar localmente

## Pre-requisitos

- Python 3.12
- Poetry 2.x

## Configuracao

Na raiz do repositorio, instale as dependencias:

```powershell
poetry env use (pyenv which python)
poetry install
Copy-Item .env.example .env
```

O arquivo `.env` e opcional para a configuracao padrao. Ajuste
`OPENF1_BASE_URL`, `OPENF1_TIMEOUT`, `ENVIRONMENT` ou `LOG_LEVEL` quando
necessario. Nao adicione credenciais ao repositorio.

## Iniciar o dashboard

```powershell
poetry run streamlit run src/f1/dashboard.py
```

O Streamlit mostra o dashboard em `http://localhost:8501`. As consultas
historicas nao exigem chave de API. A OpenF1 pode limitar temporariamente o
numero de consultas; o cliente tenta novamente respeitando o cabecalho
`Retry-After`. Se o limite persistir, aguarde um pouco antes de consultar a
sessao novamente.

## Documentacao

O comando usa a virtualenv do projeto, que requer Python 3.12. Se houver outra
virtualenv ativa (por exemplo, `.venv-1` com Python 3.15), execute `deactivate`
antes de rodar os comandos Poetry.

```powershell
poetry run task docs
poetry run mkdocs serve
```
