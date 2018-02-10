"""
Module designed to make creating and sending emails easy.

1.  Email
    - Uses the Python 3 standard library MIMEMultipart email
      object to construct the email.
"""

import smtplib
from collections import deque
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from ._eventloop import MESSAGELOOP
from ._interface import Message


class Email(Message):
    """
    Create and send emails using the built-in email package.

    Args:
        :server_name: str, i.e. 'smtp.gmail.com'
        :server_port: int, i.e. 465
        :password: str
        :from_: str, i.e. 'me@here.com'
        :to: str or list, i.e. 'you@there.com' or
            ['her@there.com', 'him@there.com']
        :cc: str or list
        :bcc: str or list
        :subject: str
        :body: str, body text of the message to send
        :attachments: str or list, i.e. './file1',
            ['/home/you/file1.txt', '/home/you/file2.pdf']

    Attributes:
        :message: MIMEMultipart, current form of the message to be constructed
        :sent_messages: deque, all messages sent with current SlackWebHook
            object, acting as a log of messages sent in the current session.

    Usage:
        Create an email object with required Args above.
        Send email with self.send() or self.send_async() methods.

    Note:
        Some email servers may require you to modify security setting, such as
        gmail allowing "less secure apps" to access the account.  Otherwise
        failure may occur when attempting to send.
    """

    def __init__(self, server_name, server_port, password, from_,
                 to, cc, bcc, subject, body, attachments):
        self.server_name = server_name
        self.server_port = server_port
        self.password = password
        self.from_ = from_
        self.to = to
        self.cc = cc
        self.bcc = bcc
        self.subject = subject
        self.body = body
        self.attachments = attachments
        self.message = None
        self.sent_messages = deque()


    def __str__(self):
        """print(Email(**args)) method."""
        return('MIMEMultipart Email:'
               '\n\tServer: {}:{}'
               '\n\tFrom: {}'
               '\n\tTo: {}'
               '\n\tCc: {}'
               '\n\tBcc: {}'
               '\n\tSubject: {}'
               '\n\tbody: {}...'
               '\n\tattachments: {}'
               .format(self.server_name, self.server_port, self.from_, self.to,
                       self.cc, self.bcc, self.subject, self.body[0:40],
                       self.attachments))


    @staticmethod
    def list_to_string(recipient):
        """
        Format the recipient for the MIMEMultipart() email type.
        If the recipient is a list, then it returns the list as a
        comma separated string.
        example: input=['you@here.com', 'her@there.com']
                 output='you@there.com, her@there.com'
        """
        if recipient:
            if isinstance(recipient, list):
                return ', '.join(recipient)
            return recipient


    def generate_email(self):
        """Put the parts of the email together."""
        self.message = MIMEMultipart()
        self.add_header()
        self.add_body()
        self.add_attachments()


    def add_header(self):
        """Add email header info."""
        self.message['From'] = self.from_
        self.message['Subject'] = self.subject


    def add_body(self):
        """Add body content of email."""
        if self.body:
            b = MIMEText('text', 'plain')
            b.set_payload(self.body)
            self.message.attach(b)


    def add_attachments(self):
        """Add required attachments."""
        num_attached = 0
        if self.attachments:
            if isinstance(self.attachments, str):
                self.attachments = [self.attachments]

            for item in self.attachments:
                doc = MIMEApplication(open(item, 'rb').read())
                doc.add_header('Content-Disposition', 'attachment',
                               filename=item)
                self.message.attach(doc)
                num_attached += 1
        return num_attached


    def get_session(self):
        """Start session with email server."""
        session = smtplib.SMTP_SSL(self.server_name, self.server_port)
        session.login(self.from_, self.password)
        return session


    def send(self):
        """
        Send the message.
        Append the repr(self) to self.sent_messages as a history.
        """
        self.generate_email()
        session = self.get_session()

        recipients = []
        if self.to:
            self.message['To'] = self.list_to_string(self.to)
            recipients.append(self.to)
        if self.cc:
            self.message['Cc'] = self.list_to_string(self.cc)
            recipients.append(self.cc)
        if self.bcc:
            self.message['Bcc'] = self.list_to_string(self.bcc)
            recipients.append(self.bcc)

        session.sendmail(self.from_, recipients, self.message.as_string())
        session.quit()
        print('Message sent...')
        self.sent_messages.append(repr(self))


    def send_async(self):
        """Send message asynchronously."""
        MESSAGELOOP.add_message(self)
