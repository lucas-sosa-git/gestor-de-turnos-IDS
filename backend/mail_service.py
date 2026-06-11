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
    Hola {nombre},

    Tu turno fue reservado con éxito.

    Detalles del turno:
    - Servicio: {servicio}
    - Barbero: {barbero}
    - Fecha: {fecha}
    - Hora: {hora}

    Te adjuntamos el código QR que vas a tener que mostrar al llegar.

    ¡Te esperamos!
    """

    mensaje = MIMEMultipart()
    mensaje["From"]    = EMAIL_REMITENTE
    mensaje["To"]      = destinatario
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain"))

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
