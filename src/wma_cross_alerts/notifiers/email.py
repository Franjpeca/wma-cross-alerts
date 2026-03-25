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
    mode: str = "normal",
) -> None:
    if not _env_bool("EMAIL_ENABLED", False):
        logger.info("EMAIL_ENABLED=false, no se envia correo de alertas")
        return

    if mode == "revalidation":
        # En revalidacion, las nuevas alertas van al correo de errores/admin
        email_to_raw = os.getenv("EMAIL_TO_ERRORS")
        if not email_to_raw:
             raise RuntimeError("EMAIL_TO_ERRORS no esta definido")
    else:
        email_to_raw = os.getenv("EMAIL_TO_ALERTS")
        if not email_to_raw:
            raise RuntimeError("EMAIL_TO_ALERTS no esta definido")

    recipients = _parse_recipients(email_to_raw)
    smtp_host, smtp_port, smtp_user, smtp_password, email_from = _get_smtp_config()

    if mode == "revalidation":
        subject = f"🔍 Golden Cross RECUPERADO [REVALIDACIÓN] | {exec_date} | {len(golden_crosses)} nuevas"
    else:
        subject = f"📈 Alerta Golden Cross WMA | {exec_date} | {len(golden_crosses)} señales"

    blocks = []
    for i, gc in enumerate(golden_crosses, 1):
        blocks.append(f"""
        <div style="margin-bottom:22px;">
            <h3>{i}. {gc['symbol']} <span style="color:#666;">({gc['market']})</span></h3>
            <ul>
                <li><b>Fecha:</b> {gc['date']}</li>
                <li><b>WMA corta (30):</b> {gc['wma_short']:.4f}</li>
                <li><b>WMA larga (200):</b> {gc['wma_long']:.4f}</li>
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
    mode: str = "normal",
) -> None:
    if not _env_bool("EMAIL_ENABLED", False):
        logger.info("EMAIL_ENABLED=false, no se envia correo de errores")
        return

    email_to_raw = os.getenv("EMAIL_TO_ERRORS")
    if not email_to_raw:
        raise RuntimeError("EMAIL_TO_ERRORS no esta definido")

    recipients = _parse_recipients(email_to_raw)
    smtp_host, smtp_port, smtp_user, smtp_password, email_from = _get_smtp_config()

    if mode == "revalidation":
        subject = f"🔍 Errores en REVALIDACIÓN | {exec_date}"
    else:
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


# =====================================================
# EMAIL DE CONFIRMACION DE EJECUCION (SUCCESS)
# =====================================================

def send_success_execution_email(
    exec_date: str,
    market_stats: dict[str, dict[str, int]],
    golden_crosses_count: int,
    mode: str = "normal",
    confirmed_crosses_count: int = 0,
) -> None:
    if not _env_bool("EMAIL_ENABLED", False):
        logger.info("EMAIL_ENABLED=false, no se envia correo de confirmacion")
        return

    # Usamos el mismo destinatario que para los errores (admin/monitoring)
    email_to_raw = os.getenv("EMAIL_TO_ERRORS")
    if not email_to_raw:
        logger.warning("EMAIL_TO_ERRORS no definido, omitiendo correo de confirmacion")
        return

    recipients = _parse_recipients(email_to_raw)
    smtp_host, smtp_port, smtp_user, smtp_password, email_from = _get_smtp_config()

    if mode == "revalidation":
        subject = f"✅ Revalidación Correcta [REVALIDACIÓN SUCCESS] | {exec_date}"
    else:
        subject = f"✅ Ejecucion Correcta [SUCCESS] | {exec_date}"

    # Construir tabla resumen de mercados
    stats_rows = ""
    for market, stats in market_stats.items():
        stats_rows += f"<tr><td>{market}</td><td>{stats['scanned']}</td><td>{stats['found']}</td></tr>"

    if mode == "revalidation":
        # Determinar estado de la revalidación
        if golden_crosses_count > 0:
            status_icon = "⚠️"
            status_text = "Alertas perdidas recuperadas"
            status_color = "#ff6f00"
        else:
            status_icon = "✅"
            status_text = "Sin problemas"
            status_color = "#2e7d32"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color:#1976d2;">🔍 Revalidación Finalizada Correctamente</h2>
            <p><b>Fecha revalidada:</b> {exec_date}</p>
            <p>Se ha completado la revalidación del día anterior para detectar posibles alertas perdidas.</p>
            
            <h3>Resumen de hallazgos</h3>
            <ul style="font-size: 16px;">
                <li><b>Nuevas alertas recuperadas:</b> <span style="color:#d32f2f; font-weight:bold;">{golden_crosses_count}</span></li>
                <li><b>Alertas ya registradas (confirmadas):</b> <span style="color:#2e7d32; font-weight:bold;">{confirmed_crosses_count}</span></li>
                <li><b>Estado:</b> <span style="color:{status_color}; font-weight:bold;">{status_icon} {status_text}</span></li>
            </ul>
            
            <h3>Detalle por mercado</h3>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                    <tr style="background-color:#f0f0f0;">
                        <th>Mercado</th>
                        <th>Escaneadas</th>
                        <th>Alertas</th>
                    </tr>
                </thead>
                <tbody>
                    {stats_rows}
                </tbody>
            </table>
            
            <hr>
            <p style="font-size:12px; color:#666;">
                Sistema automático de alertas WMA Golden Cross - Modo Revalidación
            </p>
          </body>
        </html>
        """
    else:
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color:#2e7d32;">✅ Ejecución Finalizada Correctamente</h2>
            <p><b>Fecha evaluada:</b> {exec_date}</p>
            <p>El sistema ha completado el análisis de todos los mercados configurados sin errores críticos.</p>
            
            <h3>Resumen de actividad</h3>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                    <tr style="background-color:#f0f0f0;">
                        <th>Mercado</th>
                        <th>Escaneadas</th>
                        <th>Alertas</th>
                    </tr>
                </thead>
                <tbody>
                    {stats_rows}
                </tbody>
            </table>
            
            <p><b>Total alertas Golden Cross:</b> {golden_crosses_count}</p>
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
    msg.set_content("Ejecucion finalizada correctamente. Ver contenido HTML.")
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    logger.info(f"Email de confirmacion enviado a {recipients}")
