# Como rodar testes

## Testes unitarios

O conjunto padrao usa transportes simulados e nao acessa a internet:

```powershell
poetry run pytest
```

A cobertura minima configurada e 50%. Para rodar apenas os testes unitarios:

```powershell
poetry run pytest tests/unit/
```

## Integracao opcional

Os testes que chamam a OpenF1 estao marcados e excluidos da execucao padrao:

```powershell
poetry run pytest tests/integration/ -m integration --no-cov
```

Eles precisam de acesso a internet e podem falhar se a API estiver indisponivel
ou se os dados mais recentes ainda nao estiverem publicados. `--no-cov` evita
aplicar a meta de cobertura do conjunto unitario a esta execucao isolada.

## Qualidade e build da documentacao

```powershell
poetry run ruff check .
poetry run ruff format --check .
poetry run mkdocs build --strict
```
