from wma_cross_alerts.persistence.state import already_registered
from wma_cross_alerts.persistence.storage import load_events
import logging

# Configurar logging para ver la salida
logging.basicConfig(level=logging.INFO)

symbol = "D"  # Simbolo que dio problemas
signal = "golden_cross_wma"
date = "2026-01-27"
market = "sp500"  # Mercado asumido

print(f"--- Probando load_events(symbol='{symbol}') ---")
events = load_events(symbol=symbol)
print(f"Eventos encontrados: {len(events)}")
for e in events:
    print(f" - {e['date']} {e['symbol']} {e['signal']}")

print(f"\n--- Probando already_registered('{symbol}', '{signal}', '{date}') ---")
exists = already_registered(symbol, signal, date)
print(f"Resultado: {exists}")
