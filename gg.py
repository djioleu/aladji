from pymesomb.operations import PaymentOperation
import os

# Clés d'authentification MeSomb (assurez-vous de les garder confidentielles)
APPLICATION_KEY = '5464564e357be99b5fa7fd995ec6d0544d8e50b5'
ACCESS_KEY = 'b262395b-eeb3-4a31-b725-0ce1e7223e11'
SECRET_KEY = '7d244bbc-1b9e-41fc-8aae-63478a1a7ab8'

# ID de la transaction à récupérer
trx_id = 'Wchrkv78YpTMqZhQvdlNIAU4r51WtpNVlfR5Fg0F'

# Initialisation de l'objet PaymentOperation
operation = PaymentOperation(APPLICATION_KEY, ACCESS_KEY, SECRET_KEY)

try:
    # Récupération des transactions
    transactions = operation.get_transactions([trx_id])
    
    # Si des transactions sont retournées, on les affiche sous forme brute
    if transactions:
        for trx in transactions:
            try:
                # Afficher la transaction brute pour comprendre la structure
                print("[DEBUG] Transaction brute:", trx)
                # Tentative de conversion en JSON (si possible)
                print("[DEBUG] Transaction JSON:", trx.to_json())
            except AttributeError as e:
                print(f"[ERROR] Impossible de convertir la transaction en JSON : {e}")
                print("[DEBUG] Transaction brute:", trx)
    else:
        print("[ERROR] Aucune transaction trouvée pour cet ID.")
        
except Exception as e:
    print("[ERROR] Erreur lors de la récupération de la transaction :", e)
