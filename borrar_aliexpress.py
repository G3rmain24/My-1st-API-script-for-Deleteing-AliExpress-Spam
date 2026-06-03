"""
🗑️ BORRADOR DE CORREOS DE ALIEXPRESS
"""

import os
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://mail.google.com/"]

QUERY = "from:@aliexpress.com"
BATCH_SIZE = 1000
MODO_PRUEBA = False


def autenticar():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("❌ No encontré 'credentials.json'")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def buscar_ids(service, query):
    print(f"\n🔍 Buscando correos con: '{query}'")
    ids = []
    page_token = None
    pagina = 1
    while True:
        print(f"   Cargando página {pagina}...", end="\r")
        resultado = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=500,
            pageToken=page_token
        ).execute()
        mensajes = resultado.get("messages", [])
        ids.extend([m["id"] for m in mensajes])
        page_token = resultado.get("nextPageToken")
        if not page_token:
            break
        pagina += 1
    print(f"\n📬 Total encontrados: {len(ids)} correos")
    return ids


def borrar_en_batch(service, ids):
    if not ids:
        print("✅ No hay correos para borrar.")
        return
    total = len(ids)
    borrados = 0
    print(f"\n🗑️  Borrando {total} correos en lotes de {BATCH_SIZE}...")
    for i in range(0, total, BATCH_SIZE):
        lote = ids[i:i + BATCH_SIZE]
        service.users().messages().batchDelete(
            userId="me",
            body={"ids": lote}
        ).execute()
        borrados += len(lote)
        progreso = (borrados / total) * 100
        print(f"   Progreso: {borrados}/{total} ({progreso:.1f}%) ✓")
        time.sleep(0.5)
    print(f"\n🎉 ¡Listo! Se borraron {borrados} correos de AliExpress.")


def main():
    print("=" * 50)
    print("  🗑️  BORRADOR DE CORREOS DE ALIEXPRESS")
    print("=" * 50)
    if MODO_PRUEBA:
        print("\n⚠️  MODO PRUEBA ACTIVADO")
        print("   Solo verás cuántos correos se borrarían.")
        print("   Cambia MODO_PRUEBA = False para borrar de verdad.\n")
    print("🔐 Autenticando con Gmail...")
    service = autenticar()
    print("   ✓ Autenticado correctamente")
    ids = buscar_ids(service, QUERY)
    if not ids:
        print("\n✅ No encontré correos de AliExpress. Inbox limpio!")
        return
    if MODO_PRUEBA:
        print(f"\n📊 RESUMEN:")
        print(f"   Se borrarían {len(ids)} correos de AliExpress")
        print(f"\n   → Cambia MODO_PRUEBA = False para borrar de verdad")
    else:
        print(f"\n⚠️  Estás a punto de borrar {len(ids)} correos PERMANENTEMENTE.")
        confirmacion = input("   ¿Confirmas? (escribe 'SI' para continuar): ")
        if confirmacion.strip().upper() == "SI":
            borrar_en_batch(service, ids)
        else:
            print("   Cancelado. No se borró nada.")


if __name__ == "__main__":
    main()