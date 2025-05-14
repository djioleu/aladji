import hashlib
import hmac
import base64
import time
from urllib.parse import urlencode


def sha1_hash(payload):
    """
    Calcule le hash SHA1 d'une charge utile et retourne sa représentation hexadécimale.
    """
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def hmac_sha1(secret_key, string_to_sign):
    """
    Calcule la signature HMAC-SHA1 en utilisant la clé secrète et la chaîne à signer.
    """
    signature = hmac.new(
        secret_key.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1
    ).digest()

    return base64.b64encode(signature).decode("utf-8")


def generate_canonical_request(method, url, query_params, headers, payload):
    """
    Génère une requête canonique.
    """
    # Méthode HTTP
    canonical_http_method = method.upper()

    # URI Canonique (chemin absolu)
    canonical_uri = "/"

    # Chaîne de requête canonique (triée par ordre alphabétique)
    canonical_query_string = ""
    if query_params:
        canonical_query_string = "&".join(
            [f"{urlencode({k})}={urlencode({v})}" for k, v in sorted(query_params.items())]
        )

    # En-têtes canoniques
    canonical_headers = "\n".join(
        [f"{k.lower()}:{str(v).strip()}" for k, v in sorted(headers.items())]
    ) + "\n"

    # En-têtes signés
    signed_headers = ";".join(sorted([k.lower() for k in headers.keys()]))

    # Hash de la charge utile
    hashed_payload = sha1_hash(payload)

    # Combinaison de toutes les parties
    canonical_request = (
        f"{canonical_http_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_query_string}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{hashed_payload}"
    )

    return canonical_request


def generate_string_to_sign(canonical_request, timestamp, scope):
    """
    Génère la chaîne à signer pour la signature MeSomb.
    """
    hashed_canonical_request = sha1_hash(canonical_request)

    string_to_sign = (
        f"HMAC-SHA1\n"
        f"{timestamp}\n"
        f"{scope}\n"
        f"{hashed_canonical_request}"
    )

    return string_to_sign


def generate_mesomb_signature(method, url, query_params, headers, payload, access_key, secret_key, service):
    """
    Génère la signature MeSomb et retourne la valeur de l'en-tête Authorization.
    """
    # Générer l'horodatage actuel
    timestamp = str(int(time.time()))
    headers["x-mesomb-date"] = timestamp
    headers["x-mesomb-nonce"] = hashlib.sha1(str(time.time()).encode("utf-8")).hexdigest()

    # Générer la requête canonique
    canonical_request = generate_canonical_request(method, url, query_params, headers, payload)

    # Générer le scope
    date = time.strftime("%Y%m%d")
    scope = f"{date}/{service}/mesomb_request"

    # Générer la chaîne à signer
    string_to_sign = generate_string_to_sign(canonical_request, timestamp, scope)

    # Calculer la signature
    signature = hmac_sha1(secret_key, string_to_sign)

    # Générer l'en-tête Authorization
    authorization_header = (
        f"HMAC-SHA1 Credential={access_key}/{scope}, "
        f"SignedHeaders={';'.join(sorted([k.lower() for k in headers.keys()]))}, "
        f"Signature={signature}"
    )

    return authorization_header