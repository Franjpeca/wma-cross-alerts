# Scripts de Re-notificación de Alertas

Scripts para consultar y re-enviar alertas WMA Golden Cross históricas cuando el envío de correo original falló (ej. cambio de contraseña SMTP).

> **IMPORTANTE:** Estos scripts requieren Python 3.10+ y las dependencias del proyecto.
> **Ejecutar usando el entorno virtual (`venv`):**
> 
> ```bash
> # Desde la raíz del proyecto (/opt/wma-cross-alerts)
> ./venv/bin/python scripts/<nombre_script.py> ...
> ```

---

## 1. Re-enviar alertas por RANGO de fechas (`resend_alerts_range.py`)

Procesa múltiples días consecutivamente.

**Uso:**

```bash
# Modo prueba (dry-run): Muestra qué enviaría sin enviar nada
./venv/bin/python scripts/resend_alerts_range.py --start 2026-02-12 --end 2026-02-15 --dry-run

# Enviar correos reales
./venv/bin/python scripts/resend_alerts_range.py --start 2026-02-12 --end 2026-02-15
```

**Opcional:** Filtrar por mercado para ir más rápido (recomendado si usas SSHFS):
```bash
... --market sp500
```

---

## 2. Re-enviar alertas de un SOLO DÍA (`resend_alerts.py`)

Consulta un día específico. El script de rango usa este internamente.

**Uso:**

```bash
# Modo prueba
./venv/bin/python scripts/resend_alerts.py --date 2026-02-13 --dry-run

# Enviar correo real
./venv/bin/python scripts/resend_alerts.py --date 2026-02-13
```

### Argumentos comunes

| Argumento | Descripción |
| :--- | :--- |
| `--start YYYY-MM-DD` | Fecha inicio (solo en range) |
| `--end YYYY-MM-DD` | Fecha fin (solo en range) |
| `--date YYYY-MM-DD` | Fecha única (solo en single) |
| `--market <nombre>` | `sp500`, `nasdaq100`, `dowjones`, `nyse` (Opcional, filtra para agilizar) |
| `--dry-run` | Solo imprime en consola, NO envía correos |
