import qrcode

def generar_qr(id_reserva):

    url = f"http://peluqueriaflow.com/checkin/reserva_{id_reserva}"

    img = qrcode.make(url)

    img.save("qr_reserva.png")
