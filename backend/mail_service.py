import smtplib
import qrcode
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

EMAIL_REMITENTE = "barberia.fiuba@gmail.com"
CLAVE_APP = "ydxh pvav yktv lnoy"

def enviar_mail(destinatario, nombre, fecha, hora, barbero, servicio, qr_token, id_cita):
    asunto = "Confirmación de tu turno"

    cuerpo = f"""
    <html>
    <body>

    <h2>Peluqueria Elegance</h2>

    <p>Hola <b>{nombre}</b>,</p>

    <p>Tu turno fue reservado con éxito.</p>

    <p><b>Detalles del turno:</b></p>

    <ul>
        <li>Servicio: {servicio}</li>
        <li>Barbero: {barbero}</li>
        <li>Fecha: {fecha}</li>
        <li>Hora: {hora}</li>
    </ul>

    <p>Te adjuntamos el código QR que vas a tener que mostrar al llegar.</p>

    <p>Si no podés asistir, podés cancelar tu reserva desde el siguiente botón:</p>

    <a href="http://localhost:5000/cancelar/{id_cita}"
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

    <p>¡Te esperamos!</p>

    </body>
    </html>
    """

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_REMITENTE
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto

    mensaje.attach(MIMEText(cuerpo, "html"))

    img = qrcode.make(qr_token)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    imagen = MIMEImage(buffer.read(), name="qr_turno.png")
    mensaje.attach(imagen)

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMITENTE, CLAVE_APP)
        servidor.send_message(mensaje)
        servidor.quit()
        return True

    except Exception as e:
        print(f"Error al enviar mail: {e}")
        return False
