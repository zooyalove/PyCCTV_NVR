'''
Created on 2016. 4. 19.

@author: Administrator
'''
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class UserInfoError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return repr('Set up to Userinfo by function => set_userinfo')


class GmailSender():
    '''
    classdocs
    '''
    COMMASPACE = ', '

    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587):
        '''
        @param smtp_server: smtp server address
        @param smtp_port: smtp server port
        '''
        self._svraddr = smtp_server
        self._svrport = smtp_port
        self._server = None

    def set_username(self, email_addr):
        self._username = email_addr

    def set_password(self, email_pass):
        self._userpass = email_pass

    def set_userinfo(self, username, userpass):
        self.set_username(username)
        self.set_password(userpass)

    def set_subject(self, subject):
        self._subject = subject

    def set_body(self, body_text, html=False):
        if html:
            self._body = MIMEText(body_text, 'html')
        else:
            self._body = MIMEText(body_text)

    '''
    @param filename: absolute path included file name
    '''
    def send(self, recipients, subject="", body="", filename=None):
        msg = MIMEMultipart()
        if not self._username or not self._userpass:
            raise UserInfoError()

        if isinstance(recipients, str):
            recipients = [recipients]

        msg['From'] = self._username
        msg['To'] = self.COMMASPACE.join(recipients)

        if subject == "":
            msg['Subject'] = self._subject
        else:
            msg['Subject'] = subject

        if body == "":
            body = self._body
        else:
            body = MIMEText(body)

        msg.attach(body)

        if filename is not None:
            import os
            import mimetypes

            file_basename = os.path.basename(filename)
            ctype, encoding = mimetypes.guess_type(filename)

            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/')

            if maintype == 'image':
                from email.mime.image import MIMEImage
                with open(filename, 'rb') as fp:
                    part = MIMEImage(fp.read(), _subtype=subtype)
            else:
                from email.mime.base import MIMEBase
                from email import encoders
                with open(filename, 'rb') as fp:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(fp.read())
                encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=file_basename)
            msg.attach(part)

        try:
            self._initialize()
            self._sendmail(recipients, msg)
        except smtplib.SMTPAuthenticationError as e:
            print(str(e))
        except smtplib.SMTPConnectError as e:
            print(str(e))
        except smtplib.SMTPServerDisconnected as e:
            print(str(e))
            self._server = None
            self._initialize()
            self._sendmail(recipients, msg)
        except smtplib.SMTPException as e:
            print(str(e))
        else:
            print("Sent mail from %s to %s, Success!!" % (self._username, recipients))

    def _initialize(self):
        if self._server is None:
            self._server = smtplib.SMTP(self._svraddr, self._svrport)
            self._server.ehlo()
            self._server.starttls()
            self._server.ehlo()
            self._server.login(self._username, self._userpass)

    def _sendmail(self, recipients, msg):
        self._server.sendmail(self._username, recipients, msg.as_string())
        self._server.quit()

if __name__ == '__main__':
    import os
    sender = GmailSender()
    sender.set_userinfo('dorry457@gmail.com', 'qkrrudqhd80!')
    sender.set_body('Hi~! everybody')
    sender.set_subject('Hi~! This mail is test mail by python~!')
    sender.send(['pj3112@nate.com', 'dorry457@gmail.com'], filename=os.path.abspath('taehui_gray.jpg'))
