import os
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "meu_token_financeiro_2026")


@app.route("/", methods=["GET"])
def home():
    return "Assistente Financeiro funcionando!", 200


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token de verificacao invalido", 403


def entender_mensagem(texto):
    texto_original = texto
    texto = texto.lower().strip()

    # Procura valores como:
    # 50
    # 50,90
    # R$ 50
    valor_encontrado = re.search(
        r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)",
        texto
    )

    valor = None

    if valor_encontrado:
        valor = float(
            valor_encontrado.group(1).replace(",", ".")
        )

    palavras_despesa = [
        "gastei",
        "paguei",
        "comprei",
        "despesa"
    ]

    palavras_receita = [
        "recebi",
        "ganhei",
        "salario",
        "salário",
        "receita"
    ]

    if any(palavra in texto for palavra in palavras_despesa):
        tipo = "despesa"

    elif any(palavra in texto for palavra in palavras_receita):
        tipo = "receita"

    else:
        tipo = "desconhecido"

    return {
        "mensagem": texto_original,
        "tipo": tipo,
        "valor": valor
    }


@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.get_json(silent=True) or {}

    print("Evento recebido da Meta:", dados, flush=True)

    # Por enquanto apenas recebemos o evento.
    # Quando a conta da Meta for reativada,
    # vamos extrair a mensagem e responder pelo WhatsApp.

    return jsonify({"status": "EVENT_RECEIVED"}), 200


@app.route("/teste", methods=["POST"])
def testar_assistente():
    dados = request.get_json(silent=True) or {}

    mensagem = dados.get("mensagem", "")

    resultado = entender_mensagem(mensagem)

    return jsonify(resultado), 200


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
