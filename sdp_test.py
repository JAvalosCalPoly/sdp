import os
import imaplib # IMAP4 client
import email # for parsing email messages
import logging # logging module for logging messages
from email.header import decode_header # for decoding email headers
from html.parser import HTMLParser

host = 'imap.gmail.com'
count = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []# (text, href)
        self.href = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((''.join(self.text).strip(), self.href))
            self.href = None

'''
This one parses the email and extracts the headers into a dictionary
the result is a dictionary containing the decoded email headers.
'''

def parse_email(raw):
    msg = email.message_from_bytes(raw)
    result = {}
    result['headers'] = {
        'from': decode_str(msg['From']),
        'subject': decode_str(msg['Subject']),
        'date': decode_str(msg['Date']),
        'reply_to': decode_str(msg['Reply-To']),
        'to': decode_str(msg['To']),
        'return_path': decode_str(msg['Return-Path']),
        'auth_results': decode_str(msg['Authentication-Results'])
    }
    result['headers']['received'] = [decode_str(received) for received in msg.get_all('Received', [])]
    text_parts = []
    html_parts = []
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            continue  # skip files
        content_type = part.get_content_type()
        if content_type not in ('text/plain', 'text/html'):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue  # empty part
        charset = part.get_content_charset() or 'utf-8'
        body = payload.decode(charset, errors='replace')
        if content_type == 'text/plain':
            text_parts.append(body)
        else:
            html_parts.append(body)
    result['text'] = '\n'.join(text_parts)
    result['html'] = '\n'.join(html_parts)
    parser = LinkParser()
    parser.feed(result['html'])
    result['links'] = parser.links
    return result

'''
For this one, we are decoding email header strings that could be encoded differently
I assume utf-8 and replace errors with a placeholder
then join them into the string :)
'''

def decode_str(s):
    if s is None:
        return ''
    pieces = []
    for part, encoding in decode_header(s):
        if isinstance(part, bytes): 
            if encoding is None:
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
            status, data = mail.fetch(message_id, '(BODY.PEEK[])')
            if status != 'OK':
                logger.error('Failed to fetch message %s: %s', message_id.decode(), status)
                continue
            # data[0] is a tuple (b'1 (RFC822 {1234}', b'...raw email...')
            raw_email = data[0][1]
            parsed = parse_email(raw_email)
            h = parsed['headers']
            logger.info('%s | %s | %s', h['date'], h['from'], h['subject'])
            logger.info('auth: %s', h['auth_results'])  # temp  
            logger.info('text: %d chars, html: %d chars', len(parsed['text']), len(parsed['html']))  # temp
            logger.info('text preview: %r', parsed['text'][:100])  # temp
            logger.info('links: %s', parsed['links'])  # temp
    return 0

if __name__ == '__main__':
    raise SystemExit(main())