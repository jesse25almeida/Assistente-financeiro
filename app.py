import os
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
@app.route("/api/ativos", methods=["GET"])

def listar_ativos():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, ativo, quantidade, preco_medio
        FROM ativos
        ORDER BY id
    """)

    registros = cursor.fetchall()

    cursor.close()
    conexao.close()

    ativos = []

    for registro in registros:
        ativos.append({
            "id": registro[0],
            "ativo": registro[1],
            "quantidade": float(registro[2]),
            "preco_medio": float(registro[3])
        })

    return jsonify(ativos), 200
    
criar_tabela()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
