'''Base58 encoding

Implementations of Base58 and Base58Check endcodings that are compatible
with the bitcoin network.
'''

# This module is based upon base58 snippets found scattered over many bitcoin
# tools written in python. From what I gather the original source is from a
# forum post by Gavin Andresen, so direct your praise to him.
# This module adds shiny packaging and support for python3.

from hashlib import sha256
from typing import Union

__version__ = '1.0.3'

# 58 character alphabet used
BITCOIN_ALPHABET = \
    b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
RIPPLE_ALPHABET = b'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'

# Retro compatibility
alphabet = BITCOIN_ALPHABET


def scrub_input(v: Union[str, bytes]) -> bytes:
    if isinstance(v, str):
        v = v.encode('ascii')

    return v


def b58encode_int(
    i: int, default_one: bool = True, alphabet: bytes = BITCOIN_ALPHABET
) -> bytes:
    """
    Encode an integer using Base58
    """
    if not i and default_one:
        return alphabet[0:1]
    string = b""
    while i:
        i, idx = divmod(i, 58)
        string = alphabet[idx:idx+1] + string
    return string


def b58encode(
    v: Union[str, bytes], alphabet: bytes = BITCOIN_ALPHABET
) -> bytes:
    """
    Encode a string using Base58
    """
    v = scrub_input(v)

    nPad = len(v)
    v = v.lstrip(b'\0')
    nPad -= len(v)

    p, acc = 1, 0
    for c in reversed(v):
        acc += p * c
        p = p << 8
    result = b58encode_int(acc, default_one=False, alphabet=alphabet)
    return alphabet[0:1] * nPad + result


def b58decode_int(
    v: Union[str, bytes], alphabet: bytes = BITCOIN_ALPHABET
) -> int:
    """
    Decode a Base58 encoded string as an integer
    """
    v = v.rstrip()
    v = scrub_input(v)

    decimal = 0
    for char in v:
        decimal = decimal * 58 + alphabet.index(char)
    return decimal


def b58decode(
    v: Union[str, bytes], alphabet: bytes = BITCOIN_ALPHABET
) -> bytes:
    """
    Decode a Base58 encoded string
    """
    v = v.rstrip()
    v = scrub_input(v)

    origlen = len(v)
    v = v.lstrip(alphabet[0:1])
    newlen = len(v)

    acc = b58decode_int(v, alphabet=alphabet)

    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)

    return b'\0' * (origlen - newlen) + bytes(reversed(result))


def b58encode_check(
    v: Union[str, bytes], alphabet: bytes = BITCOIN_ALPHABET
) -> bytes:
    """
    Encode a string using Base58 with a 4 character checksum
    """
    v = scrub_input(v)

    digest = sha256(sha256(v).digest()).digest()
    return b58encode(v + digest[:4], alphabet=alphabet)


def b58decode_check(
    v: Union[str, bytes], alphabet: bytes = BITCOIN_ALPHABET
) -> bytes:
    '''Decode and verify the checksum of a Base58 encoded string'''

    result = b58decode(v, alphabet=alphabet)
    result, check = result[:-4], result[-4:]
    digest = sha256(sha256(result).digest()).digest()

    if check != digest[:4]:
        raise ValueError("Invalid checksum")

    return result


def main():
    '''Base58 encode or decode FILE, or standard input, to standard output.'''

    import sys
    import argparse

    stdout = sys.stdout.buffer

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument(
        'file',
        metavar='FILE',
        nargs='?',
        type=argparse.FileType('r'),
        default='-')
    parser.add_argument(
        '-d', '--decode',
        action='store_true',
        help='decode data')
    parser.add_argument(
        '-c', '--check',
        action='store_true',
        help='append a checksum before encoding')

    args = parser.parse_args()
    fun = {
        (False, False): b58encode,
        (False, True): b58encode_check,
        (True, False): b58decode,
        (True, True): b58decode_check
    }[(args.decode, args.check)]

    data = args.file.buffer.read()

    try:
        result = fun(data)
    except Exception as e:
        sys.exit(e)

    stdout.write(result)


if __name__ == '__main__':
    main()
