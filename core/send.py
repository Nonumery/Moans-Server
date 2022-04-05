from core.config import EMAIL_PASS, NOREPLY_EMAIL
from core.gmail import Create_Service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



CLIENT_SECRET_FILE = 'core/credentials.json'
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)


def confirm_email(to : str, text : str):
    
    sender_address = NOREPLY_EMAIL
    receiver_address = NOREPLY_EMAIL#to
    subject = 'Confirm Email Address'
    # Create a text/plain message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_address
    message['To'] = receiver_address
    message.attach(MIMEText(f'This is authomatic message for registration. \n {text}'))
    raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': raw_string}).execute()
    
    
    
    

def password_recovery(to : str, text : str):
    
    sender_address = NOREPLY_EMAIL
    receiver_address = to
    subject = 'Password Recovery'
    # Create a text/plain message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_address
    message['To'] = receiver_address
    message.attach(MIMEText(f'This is authomatic message for password recovery. \n {text}'))
    raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    
    
def get_html(platform_os:bool, id:int, name:str):
    a_href = f"intent://open/{id}#Intent;scheme=moans;package=com.example.moans;end"
    if platform_os:
        a_href = f"moans://open/{id}"
    return f"""<!DOCTYPE html>
<html>
<h3>{name}</h3>
    <div>
        <button style="width:200px; height:200px">
            <a href={a_href}> Open track </a>
        </button>
    </div>
</html>
    """