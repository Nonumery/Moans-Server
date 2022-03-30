# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText



def password_recovery(to : str, text : str):
    # Create a text/plain message
    msg = MIMEText(f'This is authomatic message for password recovery. \n {text}')

# me == the sender's email address
# you == the recipient's email address
    msg['Subject'] = 'Password Recovery' #subject
    msg['From'] = 'noreply.moans@gmail.com'
    msg['To'] = 'nonum.work@gmail.com'#to

# Send the message via our own SMTP server, but don't include the
# envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail('noreply.moans@gmail.com', ['nonum.work@gmail.com'], msg.as_string())
    s.quit()