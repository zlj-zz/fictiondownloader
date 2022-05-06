import base64
import os


def encode64(s: str) -> str:
    # sourcery skip: inline-immediately-returned-variable
    misplaced_string = "".join(
        [chr(ord(code) + (idx % 5)) for idx, code in enumerate(s)]
    )
    encode64_str = base64.b64encode(misplaced_string.encode()).decode()
    return encode64_str


def decode64(s: str) -> str:
    # sourcery skip: inline-immediately-returned-variable
    # base64 decode should meet the padding rules
    remainder = len(s) % 3
    if remainder == 1:
        s += "=="
    elif remainder == 2:
        s += "="

    decode64_str = base64.b64decode(s.encode()).decode()

    original_string = "".join(
        [chr(ord(code) - (idx % 5)) for idx, code in enumerate(decode64_str)]
    )
    return original_string


def local_exist(path: str, only_file: bool = True) -> bool:
    """Check whether exist local file."""
    return os.path.isfile(path) if only_file else os.path.exists(path)


def key2file(key: str, path: str = "") -> str:
    """Trans the key to local file path."""
    return os.path.join(path, f"{key}.txt")
