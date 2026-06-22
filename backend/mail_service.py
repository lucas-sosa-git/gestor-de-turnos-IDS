import io
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import qrcode

EMAIL_REMITENTE = "barberia.fiuba@gmail.com"
CLAVE_APP = "ydxh pvav yktv lnoy"
DEFAULT_FRONTEND_URL = "https://frontend-gestor-de-turnos-ids.onrender.com"


def enviar_mail(destinatario, nombre, fecha, hora, barbero, servicio, qr_token, id_cita, frontend_url=None):
    asunto = "Confirma tu turno"
    frontend_url = (frontend_url or DEFAULT_FRONTEND_URL).rstrip("/")
    confirmar_url = f"{frontend_url}/confirmar/{qr_token}"
    cancelar_url = f"{frontend_url}/cancelar/{id_cita}"
    qr_url = f"{frontend_url}/qr/{qr_token}"

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
        servidor = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        servidor.starttls()
        servidor.login(EMAIL_REMITENTE, CLAVE_APP)
        servidor.send_message(mensaje)
        servidor.quit()
        return True
    except Exception as exc:
        print(f"Error al enviar mail: {exc}")
        return False
