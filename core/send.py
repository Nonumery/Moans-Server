# Import smtplib for the actual sending function
from email.mime.multipart import MIMEMultipart
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

from core.config import EMAIL_PASS, NOREPLY_EMAIL

def confirm_email(to : str, text : str):
    
    sender_address = NOREPLY_EMAIL
    sender_pass = EMAIL_PASS
    receiver_address = to
    subject = 'Confirm Email Address'
    # Create a text/plain message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_address
    message['To'] = receiver_address
    message.attach(MIMEText(f'This is authomatic message for registration. \n {text}'))
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(sender_address, sender_pass) #login with mail_id and password
    n_text = message.as_string()
    s.sendmail(sender_address, receiver_address, n_text)
    s.quit()

def password_recovery(to : str, text : str):
    
    sender_address = NOREPLY_EMAIL
    sender_pass = EMAIL_PASS
    receiver_address = to
    subject = 'Password Recovery'
    # Create a text/plain message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_address
    message['To'] = receiver_address
    message.attach(MIMEText(f'This is authomatic message for password recovery. \n {text}'))
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    s.sendmail(sender_address, receiver_address, text)
    s.quit()