from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration par pays
COUNTRY_CONFIG = {
    "CM": {
        "payment_methods": ["MTN", "Orange"],
        "phone_format": lambda phone: phone.lstrip("0"),
    },
    "NG": {
        "payment_methods": ["Paga", "Flutterwave"],
        "phone_format": lambda phone: phone.lstrip("0"),
    },
    "SN": {
        "payment_methods": ["Wari", "Orange Money"],
        "phone_format": lambda phone: phone,
    },
}

@app.route("/api/payment-options", methods=["POST"])
def payment_options():
    data = request.get_json()
    country_code = data.get("country_code")

    if not country_code:
        return jsonify({"error": "Code pays manquant"}), 400

    country_config = COUNTRY_CONFIG.get(country_code.upper())
    if not country_config:
        return jsonify({"error": "Pays non supporté"}), 400

    return jsonify({"methods": country_config["payment_methods"]})
@app.route("/api/pay", methods=["POST"])
def pay():
    try:
        data = request.get_json()
        print("Données reçues :", data)  # Affiche les données reçues pour débogage

        # Extraction des paramètres
        method = data.get("method")
        amount = data.get("amount")
        phone = data.get("phone")
        country_code = data.get("country_code")

        # Vérification des paramètres
        if not all([method, amount, phone, country_code]):
            print("Erreur : Paramètres manquants")  # Débogage
            return jsonify({"error": "Paramètres manquants"}), 400

        # Vérification du pays
        country_config = COUNTRY_CONFIG.get(country_code.upper())
        if not country_config:
            print(f"Erreur : Pays non supporté ({country_code})")  # Débogage
            return jsonify({"error": "Pays non supporté"}), 400

        # Vérification de la méthode de paiement
        if method.upper() not in country_config["payment_methods"]:
            print(f"Erreur : Méthode non supportée ({method})")  # Débogage
            return jsonify({"error": f"Méthode '{method}' non supportée"}), 400

        # Formatage du numéro de téléphone
        formatted_phone = country_config["phone_format"](phone)
        print("Numéro formaté :", formatted_phone)  # Débogage

        # Appel à l'API MeSomb
        url = "https://mesomb.hachther.com/api/v1.1/payment/collect/"
        headers = {
            "X-MeSomb-Application": os.getenv("MESOMB_APPLICATION_KEY"),
            "X-MeSomb-AccessKey": os.getenv("MESOMB_ACCESS_KEY"),
            "X-MeSomb-SecretKey": os.getenv("MESOMB_SECRET_KEY"),
            "Content-Type": "application/json",
        }
        payload = {
            "amount": amount,
            "service": method.upper(),
            "payer": formatted_phone,
            "nonce": os.urandom(16).hex(),
            "description": f"Paiement depuis {country_code}",
        }

        print("Payload envoyé : ", payload)  # Débogage

        # Envoi de la requête à MeSomb
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Code de statut MeSomb :", response.status_code)  # Débogage
        print("Réponse brute MeSomb :", response.text)  # Débogage
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success", False):
            return jsonify({"success": True, "message": "Paiement effectué avec succès"}), 200
        else:
            return jsonify({"error": response_data.get("message", "Échec du paiement")}), 400

    except requests.exceptions.ConnectionError as e:
        print(f"Erreur de connexion à MeSomb : {e}")
        return jsonify({"error": "Impossible de se connecter à MeSomb.", "details": str(e)}), 503
    except requests.exceptions.Timeout as e:
        print(f"Erreur de timeout avec MeSomb : {e}")
        return jsonify({"error": "La requête à MeSomb a expiré. Réessayez plus tard."}), 504
    except Exception as e:
        print(f"Erreur interne côté serveur : {e}")
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))