# Como contribuir

1. Crie uma branch para a alteracao; nao faca merge direto em `main`.
2. Mantenha as dependencias entre UI, dominio e infraestrutura conforme
   [Arquitetura](architecture.md).
3. Adicione testes unitarios para comportamento novo e atualize a documentacao.
4. Execute lint, formatacao, testes e build de documentacao antes do pull request.
5. Nao inclua `.env`, chaves ou outros dados sensiveis.

## Checklist do pull request

- [ ] `poetry run ruff check .` passou.
- [ ] `poetry run ruff format --check .` passou.
- [ ] `poetry run pytest` passou com cobertura minima de 50%.
- [ ] `poetry run mkdocs build --strict` passou.
- [ ] Documentacao atualizada para mudancas de comportamento ou arquitetura.
- [ ] Nenhum secret foi adicionado.
