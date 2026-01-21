import os
import ssl
import smtplib
from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv

from wma_cross_alerts.utils.logger import get_logger

load_dotenv()

logger = get_logger("email_notifier")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_recipients(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _get_smtp_config():
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM")

    if not all([smtp_host, smtp_user, smtp_password, email_from]):
        raise RuntimeError("Faltan variables SMTP en el entorno")

    return smtp_host, smtp_port, smtp_user, smtp_password, email_from


# =====================================================
# EMAIL RESUMEN DIARIO (ALERTAS)
# =====================================================

def send_cross_alert_email(
    exec_date: str,
    golden_crosses: list[dict],
    invalid_symbols: list[tuple],
    processing_errors: list[tuple],
) -> None:
    if not _env_bool("EMAIL_ENABLED", False):
        logger.info("EMAIL_ENABLED=false, no se envia correo de alertas")
        return

    email_to_raw = os.getenv("EMAIL_TO_ALERTS")
    if not email_to_raw:
        raise RuntimeError("EMAIL_TO_ALERTS no esta definido")

    recipients = _parse_recipients(email_to_raw)
    smtp_host, smtp_port, smtp_user, smtp_password, email_from = _get_smtp_config()

    subject = f"📈 Alerta Golden Cross WMA | {exec_date} | {len(golden_crosses)} señales"

    blocks = []
    for i, gc in enumerate(golden_crosses, 1):
        blocks.append(f"""
        <div style="margin-bottom:22px;">
            <h3>{i}. {gc['symbol']} <span style="color:#666;">({gc['market']})</span></h3>
            <ul>
                <li><b>Fecha:</b> {gc['date']}</li>
                <li><b>WMA corta:</b> {gc['wma_short']:.4f}</li>
                <li><b>WMA larga:</b> {gc['wma_long']:.4f}</li>
                <li><b>Diferencia:</b> <b>{gc['difference']:.4f}</b></li>
            </ul>
        </div>
        """)


    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Alerta - Golden Cross WMA (30 / 200)</h2>
        <p><b>Fecha evaluada:</b> {exec_date}</p>
        <p><b>Total de cruces detectados:</b> {len(golden_crosses)}</p>
        <hr>
        {''.join(blocks)}
        <hr>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content("Este correo contiene contenido HTML.")
    msg.add_alternative(html_body, subtype="html")

    for gc in golden_crosses:
        path = gc.get("chart_path")
        if path and Path(path).exists():
            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="png",
                    filename=Path(path).name,
                )

    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    logger.info(f"Email de alertas enviado ({len(golden_crosses)} cruces)")


# =====================================================
# EMAIL DE ERRORES DEL SISTEMA
# =====================================================

def send_error_report_email(
    exec_date: str,
    processing_errors: list[tuple],
    invalid_symbols: list[tuple],
) -> None:
    if not _env_bool("EMAIL_ENABLED", False):
        logger.info("EMAIL_ENABLED=false, no se envia correo de errores")
        return

    email_to_raw = os.getenv("EMAIL_TO_ERRORS")
    if not email_to_raw:
        raise RuntimeError("EMAIL_TO_ERRORS no esta definido")

    recipients = _parse_recipients(email_to_raw)
    smtp_host, smtp_port, smtp_user, smtp_password, email_from = _get_smtp_config()

    subject = f"🚨 Errores en el sistema WMA | {exec_date}"

    # Construcción de HTML para errores de procesamiento
    errors_html = ""
    if processing_errors:
        errors_html = f"<h3 style='color:#d32f2f;'>❌ Errores de procesamiento ({len(processing_errors)})</h3><ul>"
        for i, (symbol, market, error) in enumerate(processing_errors, 1):
            errors_html += f"<li><b>{i}. {symbol}</b> ({market})<br><span style='color:#d32f2f;'>{error}</span></li>"
        errors_html += "</ul>"

    # Construcción de HTML para símbolos inválidos
    invalid_html = ""
    if invalid_symbols:
        invalid_html = f"<h3 style='color:#f57c00;'>⚠️ Símbolos con datos insuficientes ({len(invalid_symbols)})</h3><ul>"
        for symbol, market, reason in invalid_symbols:
            invalid_html += f"<li><b>{symbol}</b> ({market}) – {reason}</li>"
        invalid_html += "</ul>"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>🚨 Reporte de Errores del Sistema</h2>
        <p><b>Fecha evaluada:</b> {exec_date}</p>
        <hr>
        
        {errors_html}
        
        {invalid_html}
        
        <hr>
        <p style="font-size:12px; color:#666;">
            Sistema automático de alertas WMA Golden Cross
        </p>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content("Este correo contiene contenido HTML.")
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    logger.info("Email de errores enviado correctamente")
