import io
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import qrcode

EMAIL_REMITENTE = os.environ.get("MAIL_USERNAME")
CLAVE_APP = os.environ.get("MAIL_APP_PASSWORD")
SMTP_HOST = os.environ.get("MAIL_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("MAIL_SMTP_PORT", "587"))
FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "https://frontend-gestor-de-turnos-ids.onrender.com"
).rstrip("/")


def enviar_mail(destinatario, nombre, fecha, hora, barbero, servicio, qr_token, id_cita):
    if not EMAIL_REMITENTE or not CLAVE_APP:
        print("Mail no configurado: faltan MAIL_USERNAME o MAIL_APP_PASSWORD")
        return False

    asunto = "Confirma tu turno"
    confirmar_url = f"{FRONTEND_URL}/confirmar/{qr_token}"
    cancelar_url = f"{FRONTEND_URL}/cancelar/{id_cita}"
    qr_url = f"{FRONTEND_URL}/qr/{qr_token}"

    cuerpo = f"""
    <html>
    <body>

    <h2>Peluqueria Elegance</h2>

    <p>Hola <b>{nombre}</b>,</p>

    <p>Tu solicitud de turno fue registrada.</p>
    <p><b>Para confirmar el turno, toca el siguiente boton:</b></p>

    <a href="{confirmar_url}"
    style="
    background-color:#7c3aed;
    color:white;
    padding:12px 20px;
    text-decoration:none;
    border-radius:5px;
    font-weight:bold;">
    Confirmar turno
    </a>

    <p><b>Detalles del turno:</b></p>

    <ul>
        <li>Servicio: {servicio}</li>
        <li>Barbero: {barbero}</li>
        <li>Fecha: {fecha}</li>
        <li>Hora: {hora}</li>
    </ul>

    <p>Te adjuntamos el codigo QR que vas a tener que mostrar al llegar.</p>
    <p>El QR solo sera valido si antes confirmaste el turno desde este mail.</p>

    <p>Si no podes asistir, podes cancelar tu reserva desde el siguiente boton:</p>

    <a href="{cancelar_url}"
    style="
    background-color:#dc3545;
    color:white;
    padding:12px 20px;
    text-decoration:none;
    border-radius:5px;
    font-weight:bold;">
    Cancelar reserva
    </a>

    <br><br>

    <p>Te esperamos.</p>

    </body>
    </html>
    """

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_REMITENTE
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "html"))

    img = qrcode.make(qr_url)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    imagen = MIMEImage(buffer.read(), name="qr_turno.png")
    mensaje.attach(imagen)

    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(EMAIL_REMITENTE, CLAVE_APP)
        servidor.send_message(mensaje)
        servidor.quit()
        return True
    except Exception as exc:
        print(f"Error al enviar mail: {exc}")
        return False
