import os
import imaplib # IMAP4 client
import email # for parsing email messages
import logging # logging module for logging messages
from email.header import decode_header # for decoding email headers

host = 'imap.gmail.com'
count = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_str(s):

    return s

def main():
    user = os.environ['MAIL_USER']
    password = os.environ['MAIL_PASS']
    # connect and login
    with imaplib.IMAP4_SSL(host) as mail: # connect to the server
        # login
        try:
            mail.login(user, password)
            logger.info('IMAP login succeeded')
        except imaplib.IMAP4.error as error:
            logger.error('IMAP login failed: %s', error)
            return 1
        # select label read only
        # the label is SDP Tests because i couldn't make a burner account
        status, data = mail.select('"SDP Tests"', readonly=True)
        if status != 'OK':
            logger.error('Failed to select mailbox: %s', status)
            return 1
        # data[0] should be in bytes
        logger.info('Mailbox selected, %s messages', data[0].decode())
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())