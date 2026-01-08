#!/bin/bash
set -euo pipefail

PROJECT_DIR="../"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env"
LOG_FILE="$PROJECT_DIR/logs/app.log"

cd "$PROJECT_DIR"

# -------------------------
# Cargar variables de entorno
# -------------------------
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "ERROR: .env no encontrado"
  exit 1
fi

# -------------------------
# Activar entorno virtual
# -------------------------
source "$VENV_DIR/bin/activate"

# -------------------------
# Ejecutar aplicacion
# -------------------------
if ! python src/wma_cross_alerts/main.py >> "$LOG_FILE" 2>&1; then
  echo "ERROR: fallo en la ejecucion del sistema" >> "$LOG_FILE"

  python - <<EOF
import os
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "ERROR en ejecucion WMA Golden Cross"
msg["From"] = os.environ["EMAIL_FROM"]
msg["To"] = os.environ["EMAIL_TO"]
msg.set_content(
    "La ejecucion diaria ha fallado.\n\n"
    "Revisa el log:\n"
    f"{os.environ.get('HOSTNAME', 'host')}\n\n"
    "Ultimas lineas del log:\n\n"
)

with open("$LOG_FILE", "r", encoding="utf-8") as f:
    lines = f.readlines()[-50:]
    msg.set_content(msg.get_content() + "".join(lines))

with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as s:
    s.starttls()
    s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    s.send_message(msg)
EOF

  exit 1
fi

exit 0
