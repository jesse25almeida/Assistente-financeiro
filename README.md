# Assistente Financeiro para WhatsApp - Webhook MVP

Projeto inicial para conectar a WhatsApp Cloud API (Meta) a um servidor Flask hospedado no Render.

## Arquivos

- `app.py`: servidor Flask com verificacao e recebimento do webhook.
- `requirements.txt`: dependencias Python.
- `Procfile`: comando de inicializacao para o Render.

## Render

Crie um Web Service apontando para este repositorio.

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

Em Environment, crie:

- Key: `VERIFY_TOKEN`
- Value: escolha um token secreto seu, por exemplo uma sequencia aleatoria longa.

Nao coloque o Access Token do WhatsApp no codigo ou no GitHub.

## Meta / WhatsApp

Depois que o Render publicar o servico, use:

- URL de callback: `https://SEU-SERVICO.onrender.com/webhook`
- Verificar token: exatamente o mesmo valor definido em `VERIFY_TOKEN` no Render.

Clique em **Verificar e salvar** na Meta.

## Teste rapido

Ao abrir `https://SEU-SERVICO.onrender.com/`, deve aparecer:

`Assistente Financeiro funcionando!`

Este MVP apenas recebe os eventos. O proximo passo sera interpretar as mensagens, registrar receitas/despesas e responder pelo WhatsApp.
