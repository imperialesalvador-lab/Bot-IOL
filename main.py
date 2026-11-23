import os, time, requests, datetime
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
keep_alive()
# CONFIGURACION FINAL
MONTO_POR_TIRO = 700000
MAX_EN_CANCHA = 5
VENTA_PORCENTAJE = 0.03  # +3%
HORA_INICIO = "11:00"

# TUS 10 VOLATILES - los podes cambiar
TICKERS = ["GGAL","YPFD","PAMP","TXAR","ALUA","BMA","CEPU","EDN","TRAN","MIRG"]

IOL_USER = os.getenv("IOL_USER")
IOL_PASS = os.getenv("IOL_PASS")

def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}", flush=True)

def get_token():
    r = requests.post("https://api.invertironline.com/token",
        data={"username": IOL_USER, "password": IOL_PASS, "grant_type": "password"},
        timeout=20)
    return r.json().get("access_token")

def get_precio(token, ticker):
    try:
        r = requests.get(f"https://api.invertironline.com/api/v2/{ticker}/Cotizacion",
            headers={"Authorization": f"Bearer {token}"}, timeout=20)
        d = r.json()
        return d.get("ultimoPrecio") or d.get("ultimoPrecioCompra")
    except:
        return None

def comprar(token, ticker, precio):
    cantidad = int(MONTO_POR_TIRO // precio)
    if cantidad <= 0:
        return None
    log(f"COMPRANDO {ticker} x{cantidad} a ${precio}")
    # ACA VA LA ORDEN REAL - por ahora simulamos para probar
    # Descomentar cuando quieras operar de verdad
    return {"ticker": ticker, "precio_compra": precio, "cantidad": cantidad}

def main():
    log("BOT INICIADO - Esperando 11:00")
    cartera = {}
    while True:
        ahora = datetime.datetime.now().strftime("%H:%M")
        if ahora >= HORA_INICIO:
            token = get_token()
            if not token:
                log("Error token, reintento en 60s")
                time.sleep(60)
                continue
            # 1. VENDER SI SUBIO +3% Y NUNCA EN PERDIDA
            for t in list(cartera.keys()):
                precio = get_precio(token, t)
                if precio:
                    compra = cartera[t]["precio_compra"]
                    ganancia = (precio - compra) / compra
                    if ganancia >= VENTA_PORCENTAJE:
                        log(f"VENDIENDO {t} a ${precio} ganancia {ganancia*100:.2f}%")
                        del cartera[t]
            # 2. COMPRAR HASTA 5 EN CANCHA
            if len(cartera) < MAX_EN_CANCHA:
                for t in TICKERS:
                    if t not in cartera and len(cartera) < MAX_EN_CANCHA:
                        precio = get_precio(token, t)
                        if precio:
                            op = comprar(token, t, precio)
                            if op:
                                cartera[t] = op
                                time.sleep(2)
            log(f"En cancha: {list(cartera.keys())}")
            time.sleep(60)
        else:
            time.sleep(30)

if __name__ == "__main__":
    main()
