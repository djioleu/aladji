import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()  # charge .env

app = Flask(__name__)

# 1) Endpoint pour renvoyer les méthodes disponibles
@app.route("/api/payment-options", methods=["POST"])
def payment_options():
    data = request.get_json()
    lat, lng = data.get("lat"), data.get("lng")

    # Ici, tu peux raffiner selon la zone
    methods = ["mtn", "orange"]  # Exemple : tout le Cameroun
    return jsonify({"methods": methods})

# 2) Endpoint pour lancer un paiement via Mesomb
@app.route("/api/pay", methods=["POST"])
def pay():
    data = request.get_json()
    method = data.get("method")    # 'mtn' ou 'orange'
    amount = data.get("amount")    # en FCFA
    phone = data.get("phone")      # numéro mobile

    # Prépare ta requête à Mesomb
    url = f"https://api.mesomb.cm/v1/collections/{method}"
    headers = {"Authorization": f"Bearer {os.getenv('MESOMB_API_SECRET')}"}
    payload = {
      "amount": amount,
      "msisdn": phone,
      "description": "Paiement App Flutter"
    }

    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        return jsonify(resp.json()), 200
    else:
        return jsonify({"error": resp.text}), resp.status_code

# 3) Route racine pour vérifier le déploiement
@app.route("/")
def home():
    return "API Paiement Cameroon OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
