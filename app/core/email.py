import smtplib
from email.message import EmailMessage

smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "obpapiprova@gmail.com"
smtp_pass = "qzlj otkw wuev qhud"  # Password per app, NON password normale!

def send_email(to, subject, body, reply_to=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.set_content(body)
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    except Exception as e:
        raise RuntimeError(f"Errore invio email: {e}")