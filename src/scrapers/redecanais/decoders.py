# functions to decode obfuscated files and scripts

import base64
import re

from .exceptions import *
from bs4 import BeautifulSoup
import aiohttp


def decode_redecanais(payload: list[str], key: int):
    try:
        final_chars = []
        for b64_str in payload:
            # decode the base 64 string back to utf8
            decoded_str = base64.b64decode(b64_str).decode()

            # extract the integer representing the character
            encoded_char = int(re.sub(r"\D", "", decoded_str))

            # subtract the key to get the unicode value for the character
            encoded_char -= key

            # append charcter to final string
            final_chars.append(chr(encoded_char))

        # return the decoded content
        try:
            return "".join(final_chars).encode("latin1").decode("utf8")
        except UnicodeDecodeError:
            return "".join(final_chars)
    except:
        msg = "Something went wrong when decoding with the given payload and key."
        raise DecoderError(msg)


def parse_payload_str(payload_str: str):
    try:
        b64_list = []

        # ignore the portion of code that comes before the list of encoded chars
        b64_list_str = payload_str.split("[")[1]

        # isolate the list of encoded chars and save the leftover code that comes after it
        b64_list_str, leftover = b64_list_str.split("]")

        # extract all b64 strings from the raw list of encoded chars
        b64_strs = re.findall(r"\"((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=))\"", b64_list_str)

        # save all b64 strings to a python list
        [b64_list.append(s) for s in b64_strs]

        # extract key from the leftover code after the list of encoded chars
        key = re.findall(r".replace.* *?- *?(\d+)\)", leftover)
        if key:
            key = int(key[0])

        return b64_list, key

    except:
        msg = f"Could not extract payload and key from the encoded html.\n{payload_str}"
        raise EncodedParsingError(msg)


def decode_from_text(html_text: str, script_index: int | None = None):
    html = BeautifulSoup(html_text, "html.parser")

    scripts = html.find_all("script")
    if script_index is None:
        try:
            main_script = scripts[1]
        except IndexError:
            main_script = scripts[0]
    else:
        main_script = scripts[script_index]

    payload, key = parse_payload_str(main_script.text)
    return decode_redecanais(payload, key)


async def decode_from_response(response: aiohttp.ClientResponse, script_index: int | None = None):
    html_text = await response.text()

    return decode_from_text(html_text, script_index)


def decode_redecanais_simplified(payload_str: str):
    # remove everything outside the integer list
    payload_str = payload_str.split("[")[1]
    payload_str = payload_str.split("]")[0]

    # get list of integers
    int_list = re.findall(r"\b\d+\b", payload_str)

    # decode
    decoded_chars = [chr(int(i)) for i in int_list]
    decoded_str = "".join(decoded_chars)  # join chars
    decoded_str = decoded_str.replace("\\/", "/").encode().decode("unicode-escape")  # escape special chars

    return decoded_str


def decode_videojs(payload_str: str):
    payload_str = base64.b64decode(payload_str.encode()).decode()

    return decode_redecanais_simplified(payload_str)


def decode_xor_obfuscation(encoded_data: str, xor_key: int) -> str:
    """
    Replicates the JavaScript's decryption logic:
    1. Base64 Decodes the input string.
    2. Performs a byte-wise XOR operation using the given key.
    3. Reverses the order of the bytes during decryption.
    4. Decodes the resulting bytes into a UTF-8 string.

    Args:
        encoded_data: The Base64-encoded and XOR-encrypted string.
        xor_key: The integer key used for the XOR operation.

    Returns:
        The decrypted plaintext (assumed to be HTML).
    """
    # 1. Base64 Decode
    # JavaScript's atob() handles standard Base64, which corresponds to
    # base64.b64decode() in Python.
    decoded_bytes = base64.b64decode(encoded_data)
    L = len(decoded_bytes)

    # Array to hold the final, decrypted, and correctly ordered bytes
    decrypted_bytes = bytearray(L)

    # 2. XOR Decryption and 3. Reversal
    # The JavaScript logic was: a[L-1-i] = b.charCodeAt(i) ^ k
    # This means byte 'i' from the input goes to position 'L-1-i' in the output.
    for i in range(L):
        # decoded_bytes[i] is the equivalent of b.charCodeAt(i)
        # The XOR operation
        decrypted_byte = decoded_bytes[i] ^ xor_key

        # Write the decrypted byte to the reversed position
        decrypted_bytes[L - 1 - i] = decrypted_byte

    # 4. Decode to String
    return decrypted_bytes.decode("utf-8")


def decode_xor_from_text(text: str):
    matches = re.findall(r"function\( *\) *{var *k= *(\d+) *; *var *\w+ *= *\"(.+?)\"", text)
    key, payload = matches[0]
    key = int(key)

    return decode_xor_obfuscation(payload, key)
