import os
import re
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "meu_token_financeiro_2026")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")


@app.route("/", methods=["GET"])
def home():
    return "Assistente Financeiro funcionando!", 200


# Mantemos a verificacao antiga da Meta
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Webhook funcionando", 200


def entender_mensagem(texto):
    texto_lower = texto.lower().strip()

    valor_encontrado = re.search(
        r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)",
        texto_lower
    )

    valor = None

    if valor_encontrado:
        valor = float(
            valor_encontrado.group(1).replace(",", ".")
        )

    palavras_despesa = [
        "gastei", "paguei", "comprei", "despesa"
    ]

    palavras_receita = [
        "recebi", "ganhei", "salario", "salário", "receita"
    ]

    if any(p in texto_lower for p in palavras_despesa):
        tipo = "despesa"

    elif any(p in texto_lower for p in palavras_receita):
        tipo = "receita"

    else:
        tipo = "desconhecido"

    return tipo, valor


def criar_resposta(texto):
    tipo, valor = entender_mensagem(texto)

    if tipo == "despesa" and valor is not None:
        valor_formatado = f"{valor:.2f}".replace(".", ",")

        return (
            "✅ Despesa identificada!\n\n"
            f"💰 Valor: R$ {valor_formatado}\n"
            f"📝 {texto}"
        )

    if tipo == "receita" and valor is not None:
        valor_formatado = f"{valor:.2f}".replace(".", ",")

        return (
            "💵 Receita identificada!\n\n"
            f"💰 Valor: R$ {valor_formatado}\n"
            f"📝 {texto}"
        )

    return (
        "👋 Sou seu Assistente Financeiro.\n\n"
        "Experimente:\n"
        "Gastei 50 reais no mercado\n"
        "ou\n"
        "Recebi 3000 de salário"
    )


@app.route("/webhook", methods=["POST"])
def receber_webhook():
    mensagem = request.form.get("Body", "").strip()
    remetente = request.form.get("From", "").strip()

    print("Mensagem recebida:", mensagem, flush=True)
    print("Remetente:", remetente, flush=True)

    if not mensagem or not remetente:
        return "OK", 200

    resposta = criar_resposta(mensagem)

    try:
        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

        mensagem_enviada = client.messages.create(
            body=resposta,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=remetente
        )

        print(
            "Resposta enviada pela Twilio:",
            mensagem_enviada.sid,
            flush=True
        )

    except Exception as erro:
        print(
            "ERRO AO ENVIAR:",
            str(erro),
            flush=True
        )

    return "OK", 200


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
