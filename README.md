# F1 Explorer

Dashboard em Python para explorar dados historicos da Formula 1 usando a
[API OpenF1](https://openf1.org/docs/). Selecione temporada, Grande Premio e
sessao para consultar as dez voltas validas mais rapidas e estatisticas da sessao.

Dados historicos a partir de 2023 sao disponibilizados sem autenticacao. O acesso
em tempo real exige uma assinatura OpenF1 e nao faz parte deste projeto.

## Requisitos

- Python 3.12
- Poetry 2.x

## Instalacao e execucao

Na raiz do repositorio, configure o ambiente e instale as dependencias:

```powershell
pyenv local 3.12.10
poetry config virtualenvs.in-project true --local
poetry env use (pyenv which python)
poetry install
```

Inicie o dashboard:

```powershell
.\.venv\Scripts\Activate.ps1
python --version  # deve mostrar Python 3.12.10
poetry run streamlit run src/f1/dashboard.py
```

Se o terminal estiver usando outra virtualenv (por exemplo, `.venv-1` com
Python 3.15), saia dela com `deactivate` e ative a `.venv` do projeto antes de
executar os comandos.

## Desenvolvimento

```powershell
poetry run task test
poetry run task lint
poetry run task format
poetry run task docs
```

Para visualizar a documentação localmente durante a edição, execute
`poetry run mkdocs serve`.

Os testes padrao nao dependem da rede; as respostas HTTP sao simuladas. A
cobertura minima configurada para o pacote `f1` e 50%. Os testes de integracao
com a API real sao opcionais:

```powershell
poetry run pytest tests/integration/ -m integration --no-cov
```

Consulte a [documentacao do projeto](docs/docs/index.md) e o
[guia de desenvolvimento](docs/development.md) para detalhes.
