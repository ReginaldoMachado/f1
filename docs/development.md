# Desenvolvimento

## Ambiente

O projeto usa Python 3.12.10, Poetry 2.x e uma virtualenv local em `.venv`.
No PowerShell, na raiz do repositório:

```powershell
pyenv local 3.12.10
poetry config virtualenvs.in-project true --local
poetry env use (pyenv which python)
poetry install
```

## Dashboard

```powershell
.\.venv\Scripts\Activate.ps1
python --version  # deve mostrar Python 3.12.10
poetry run streamlit run src/f1/dashboard.py
```

Se outra virtualenv estiver ativa, saia dela com `deactivate` antes de ativar
`.venv`. O Poetry usa a virtualenv ativa do terminal; por isso, uma virtualenv
com Python 3.15 causa erro mesmo que a `.venv` do projeto esteja configurada.

O dashboard chama a API pública `https://api.openf1.org/v1/`. Não é necessário
configurar credenciais para dados históricos gratuitos a partir de 2023. A API
usa timestamps UTC; dados ao vivo exigem assinatura e não fazem parte do MVP.

## Testes e qualidade

```powershell
poetry run task test
poetry run task lint
poetry run task format
poetry run task docs
```

`format` aplica a formatação do Ruff aos arquivos; `docs` valida e gera o site
MkDocs. Para visualizar a documentação durante a edição, use
`poetry run mkdocs serve`.

Os testes usam substitutos da rede para verificar filtros, respostas e erros do
cliente sem depender da disponibilidade da API. O pytest-cov exige pelo menos
50% de cobertura do pacote `f1`.

## Organização

- `src/f1/api.py`: cliente HTTP e tratamento de erros da OpenF1.
- `src/f1/dashboard.py`: interface Streamlit e apresentação dos dados.
- `tests/`: testes do cliente e das transformações usadas pelo dashboard.
