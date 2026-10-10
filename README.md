# Agente de Notícias

Coleta diária de notícias brasileiras (G1, CNN Brasil, Poder360, Agência Brasil,
Correio Braziliense, ANBA) com Claude + busca na web e envio do relatório em HTML
por e-mail.

## Rodar no GitHub Actions

1. Em **Settings → Secrets and variables → Actions**, crie os secrets
   `ANTHROPIC_API_KEY`, `EMAIL_FROM`, `EMAIL_PASS` (senha de app do Gmail) e `EMAIL_TO`.
2. O workflow `.github/workflows/noticias.yml` roda todo dia às 07h30 (Brasília).
   Para testar na hora: **Actions → Relatório Diário de Notícias → Run workflow**.

## Rodar localmente

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha os valores
python agent.py
```

Fontes e temas ficam no topo de `agent.py` (`SOURCES`, `TOPICS`).
