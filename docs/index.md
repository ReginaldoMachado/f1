# F1 Explorer

O F1 Explorer é um dashboard Streamlit para explorar dados históricos da
[OpenF1](https://openf1.org/docs/).

## Funcionalidades do MVP

- Seleção de temporada, Grande Prêmio e sessão.
- Consulta de pilotos e resultado final publicado.
- Consulta dos tempos de volta e setores disponíveis.
- Mensagens explícitas para falhas da API e dados ainda indisponíveis.

O projeto consulta os endpoints `meetings`, `sessions`, `drivers`, `session_result`
e `laps`. Dados históricos a partir de 2023 são gratuitos; dados ao vivo exigem
assinatura e não estão incluídos. Alguns endpoints podem ainda não ter dados para
uma sessão, por exemplo, antes da publicação do resultado oficial.

## Iniciar

Consulte o [guia de desenvolvimento](development.md) para instalar dependências,
executar o dashboard e validar alterações.
