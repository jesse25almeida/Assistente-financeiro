import os
import re
import requests
import psycopg2
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def conectar_banco():
    return psycopg2.connect(DATABASE_URL)
    
def criar_tabela():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ativos (
            id SERIAL PRIMARY KEY,
            ativo VARCHAR(20) NOT NULL,
            quantidade NUMERIC NOT NULL,
            preco_medio NUMERIC NOT NULL
        )
    """)

    conexao.commit()
    cursor.close()
    conexao.close()
    
VERIFY_TOKEN = os.getenv(
    "VERIFY_TOKEN",
    "meu_token_financeiro_2026"
)

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")

# Deixe a versão configurável para podermos atualizar
# sem alterar o código inteiro.
META_API_VERSION = os.getenv("META_API_VERSION")


@app.route("/", methods=["GET"])
def home():
    return send_file("dashboard.html")
    
@app.route("/carteira", methods=["GET"])
def carteira():
    return send_file("carteira.html")
    
@app.route("/api/ativos", methods=["POST"])
def adicionar_ativo():
    dados = request.get_json()

    ativo = dados.get("ativo", "").strip().upper()
    quantidade = dados.get("quantidade")
    preco_medio = dados.get("preco_medio")

    if not ativo or not quantidade or not preco_medio:
        return jsonify({"erro": "Preencha todos os campos"}), 400

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO ativos (ativo, quantidade, preco_medio)
        VALUES (%s, %s, %s)
        """,
        (ativo, quantidade, preco_medio)
    )

    conexao.commit()
    cursor.close()
    conexao.close()

    return jsonify({
        "status": "ok",
        "mensagem": "Ativo salvo com sucesso"
    }), 201

@app.route("/privacidade", methods=["GET"])
def privacidade():
    return """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Política de Privacidade - Assistente Financeiro</title>
    </head>
    <body>
        <h1>Política de Privacidade</h1>
        <p>O Assistente Financeiro utiliza informações enviadas pelo usuário
        através do WhatsApp exclusivamente para fornecer as funcionalidades
        do serviço.</p>

        <p>As informações podem incluir mensagens relacionadas a receitas,
        despesas e outros registros financeiros enviados voluntariamente
        pelo usuário.</p>

        <p>Os dados não são vendidos ou compartilhados para fins publicitários.</p>

        <p>O usuário pode solicitar a exclusão de seus dados a qualquer momento.</p>

        <p>Contato: jessealmeida016@gmail.com</p>

        <p>Última atualização: 25 de setembro de 2026.</p>
    </body>
    </html>
    """, 200
# Verificação do webhook pela Meta
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado pela Meta!", flush=True)
        return challenge, 200

    return "Token de verificação inválido", 403


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


def enviar_mensagem(numero, texto):
    if not META_ACCESS_TOKEN:
        raise Exception("META_ACCESS_TOKEN não configurado")

    if not META_PHONE_NUMBER_ID:
        raise Exception("META_PHONE_NUMBER_ID não configurado")

    if not META_API_VERSION:
        raise Exception("META_API_VERSION não configurado")

    url = (
        f"https://graph.facebook.com/"
        f"{META_API_VERSION}/"
        f"{META_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": texto
        }
    }

    resposta = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=15
    )

    print(
        "Resposta da Meta:",
        resposta.status_code,
        resposta.text,
        flush=True
    )

    resposta.raise_for_status()

    return resposta.json()


@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.get_json(silent=True) or {}

    print("Webhook recebido:", dados, flush=True)

    try:
        entry = dados.get("entry", [])

        if not entry:
            return jsonify({"status": "ignored"}), 200

        changes = entry[0].get("changes", [])

        if not changes:
            return jsonify({"status": "ignored"}), 200

        value = changes[0].get("value", {})

        # A Meta também envia eventos de status
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "ignored"}), 200

        mensagem = messages[0]

        remetente = mensagem.get("from")
        tipo_mensagem = mensagem.get("type")

        if tipo_mensagem != "text":
            print(
                "Mensagem não textual ignorada:",
                tipo_mensagem,
                flush=True
            )
            return jsonify({"status": "ignored"}), 200

        texto = mensagem.get("text", {}).get("body", "").strip()

        if not remetente or not texto:
            return jsonify({"status": "ignored"}), 200

        print("Mensagem recebida:", texto, flush=True)
        print("Remetente:", remetente, flush=True)

        resposta = criar_resposta(texto)

        enviar_mensagem(remetente, resposta)

        print("Resposta enviada pela Meta!", flush=True)

    except Exception as erro:
        print(
            "ERRO NO WEBHOOK:",
            str(erro),
            flush=True
        )

    return jsonify({"status": "ok"}), 200

criar_tabela()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
