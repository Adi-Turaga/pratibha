"""Per-entry authenticated encryption. Passwords and keys are never persisted."""
import base64
import hashlib
import json
import os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def key_for(password, salt):
    if not password:
        raise ValueError('A password is required for this entry.')
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)


def encrypt(password, salt, location, descriptor, body):
    nonce = os.urandom(12)
    payload = json.dumps(dict(location=location, descriptor=descriptor, body=body), ensure_ascii=False).encode('utf-8')
    return base64.b64encode(nonce + AESGCM(key_for(password, salt)).encrypt(nonce, payload, b'Pratibha-entry-v1')).decode('ascii')


def decrypt(password, salt, ciphertext):
    try:
        data = base64.b64decode(ciphertext, validate=True)
        return json.loads(AESGCM(key_for(password, salt)).decrypt(data[:12], data[12:], b'Pratibha-entry-v1'))
    except (InvalidTag, ValueError, KeyError, UnicodeError) as error:
        raise ValueError('Incorrect password, or this entry is damaged.') from error
