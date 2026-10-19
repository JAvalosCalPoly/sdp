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
    if s is None:
        return ''
    pieces = []
    for part, encoding in decode_header(s):
        if isinstance(part, bytes): 
            if encoding is None:
                # assume utf-8
                part = part.decode('utf-8', errors='replace')
            else:
                part = part.decode(encoding, errors='replace')
        pieces.append(part)
    s = ''.join(pieces)
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
        # find message ids
        status, data = mail.search(None, 'ALL')
        # take data[0]
        # split it to get list of bytes
        # keep the last count with a slice
        message_ids = data[0].split()[-count:]
        logger.info('Found %d messages', len(message_ids))
        for message_id in reversed(message_ids):
            # fetch the message by id
            status, data = mail.fetch(message_id, 'BODY.PEEK[HEADER]')
            if status != 'OK':
                logger.error('Failed to fetch message %s: %s', message_id.decode(), status)
                continue
            # data[0] is a tuple (b'1 (RFC822 {1234}', b'...raw email...')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = decode_str(msg['Subject'])
            date = decode_str(msg['Date'])
            sender = decode_str(msg['From'])
            logger.info('%s | %s | %s', date, sender, subject)    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())