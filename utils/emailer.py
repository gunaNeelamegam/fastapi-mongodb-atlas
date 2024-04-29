import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
from typing import Union, List
from utils.logger import log
from utils.decorator import error_handler

@error_handler(message = "SENDING MAIL FAILED")
def send_mail(link:str, context: str , receiver_mail: Union[str, List[str]],setting = settings(), console = log()):
    message = MIMEMultipart("alternative")
    message["From"] = setting.smtp_user
    if isinstance(receiver_mail, str):
        message["To"] = receiver_mail
    if isinstance(receiver_mail, list):
        message["To"] = ", ".join(receiver_mail)
    
    # creating the email subject
    message["Subject"] = "Auth Testing"
    html_content = """
    <html>
  <body>
    <p>This is a test <b>HTML</b> email sent from <span style="color:blue;">Auth School</span>.</p>
    <a href="{link}">Click Here to {context}</a>
      </body>
</html>
"""
    html_content = html_content.format(link = link, context = context)
    html_content = MIMEText(html_content, "html")
    message.attach(html_content)
    server = smtplib.SMTP(setting.smtp_host, setting.smtp_port)
    server.starttls()
    server.login(setting.smtp_user, setting.smtp_pass)
    text = message.as_string()
    server.sendmail(setting.smtp_user, receiver_mail, text)
    console.print("EMAIL SENDED SUCCESSFULLY")
    return True
    