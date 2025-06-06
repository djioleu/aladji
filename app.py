from flask import Flask, request, jsonify
from pymesomb.operations import PaymentOperation
from pymesomb.utils import RandomGenerator
from datetime import datetime, date
from dotenv import load_dotenv
from decimal import Decimal
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)

# Clés d'authentification MeSomb
APPLICATION_KEY = os.getenv("MESOMB_APPLICATION_KEY")
ACCESS_KEY = os.getenv("MESOMB_ACCESS_KEY")
SECRET_KEY = os.getenv("MESOMB_SECRET_KEY")

# Instancier l'objet PaymentOperation
operation = PaymentOperation(APPLICATION_KEY, ACCESS_KEY, SECRET_KEY)

# Configuration des options de paiement par pays
COUNTRY_CONFIG = {
    "CM": {
        "payment_methods": ["MTN", "ORANGE"],
        "phone_format": lambda phone: phone.lstrip("0"),
    },
    "NG": {
        "payment_methods": ["PAGA", "FLUTTERWAVE"],
        "phone_format": lambda phone: phone.lstrip("0"),
    },
    "SN": {
        "payment_methods": ["WARI", "ORANGE MONEY"],
        "phone_format": lambda phone: phone,
    },
}

# Fonction utilitaire pour la sérialisation JSON
def serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in vars(obj).items()}
    elif isinstance(obj, list):
        return [serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    else:
        return str(obj)

@app.route("/api/payment-options", methods=["POST"])
def payment_options():
    try:
        data = request.get_json()
        country_code = data.get("country_code")

        if not country_code:
            return jsonify({"error": "Code pays manquant"}), 400

        config = COUNTRY_CONFIG.get(country_code.upper())
        if not config:
            return jsonify({"error": "Pays non supporté"}), 400

        return jsonify({"methods": config["payment_methods"]}), 200

    except Exception as e:
        print(f"[ERREUR OPTIONS] {e}")
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

@app.route("/api/pay", methods=["POST"])
def pay():
    try:
        data = request.get_json()
        print("Données reçues :", data)

        method = data.get("method")
        amount = data.get("amount")
        phone = data.get("phone")
        country_code = data.get("country_code")
        trx_id = data.get("trx_id", RandomGenerator.nonce())

        if not all([method, amount, phone, country_code]):
            return jsonify({"error": "Paramètres manquants"}), 400

        config = COUNTRY_CONFIG.get(country_code.upper())
        if not config:
            return jsonify({"error": "Pays non supporté"}), 400

        if method.upper() not in config["payment_methods"]:
            return jsonify({"error": f"Méthode de paiement '{method}' non disponible pour {country_code.upper()}"}), 400

        formatted_phone = config["phone_format"](phone)

        collect_data = {
            "amount": amount,
            "service": method.upper(),
            "payer": formatted_phone,
            "nonce": RandomGenerator.nonce(),
            "trx_id": trx_id
        }

        print("Données de collecte :", collect_data)

        response = operation.make_collect(
            amount=collect_data["amount"],
            service=collect_data["service"],
            payer=collect_data["payer"],
            nonce=collect_data["nonce"],
            trx_id=collect_data["trx_id"]
        )

        if response.is_operation_success():
            return jsonify(serialize({
                "success": response.is_transaction_success(),
                "message": response.message,
                "status": response.status,
                "reference": response.reference,
                "transaction": response.transaction
            })), 200 if response.is_transaction_success() else 400
        else:
            return jsonify(serialize({
                "success": False,
                "message": response.message,
                "status": response.status
            })), 400

    except Exception as e:
        print(f"[ERREUR PAY] {e}")
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

@app.route("/api/deposit", methods=["POST"])
def deposit():
    try:
        data = request.get_json()
        print("Données reçues :", data)

        amount = data.get("amount")
        service = data.get("service")
        receiver = data.get("receiver")
        trx_id = data.get("trx_id", RandomGenerator.nonce())

        if not all([amount, service, receiver]):
            return jsonify({"error": "Paramètres manquants : 'amount', 'service', ou 'receiver'"}), 400

        deposit_data = {
            'amount': amount,
            'service': service.upper(),
            'receiver': receiver,
            'date': datetime.now(),
            'nonce': RandomGenerator.nonce(),
            'trx_id': trx_id
        }

        print("Données pour le dépôt :", deposit_data)

        response = operation.make_deposit(
            amount=deposit_data['amount'],
            service=deposit_data['service'],
            receiver=deposit_data['receiver'],
            nonce=deposit_data['nonce'],
            trx_id=deposit_data['trx_id']
        )

        if response.is_operation_success():
            return jsonify(serialize({
                "success": response.is_transaction_success(),
                "message": response.message,
                "status": response.status,
                "reference": response.reference,
                "transaction": response.transaction
            })), 200 if response.is_transaction_success() else 400
        else:
            return jsonify(serialize({
                "success": False,
                "message": response.message,
                "status": response.status
            })), 400

    except Exception as e:
        print(f"[ERREUR DEPOSIT] {e}")
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

@app.route("/api/transaction/<trx_id>", methods=["GET"])
def get_transaction(trx_id):
    try:
        response = operation.get_transaction_status(trx_id)

        if response:
            return jsonify(serialize({
                "success": True,
                "transaction": response
            })), 200
        else:
            return jsonify({
                "success": False,
                "message": "Transaction introuvable."
            }), 404

    except Exception as e:
        print(f"[ERREUR TRANSACTION] {e}")
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
