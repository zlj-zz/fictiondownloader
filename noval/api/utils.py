import base64


def encode64(s: str) -> str:
    misplaced_string = "".join(
        [chr(ord(code) + (idx % 5)) for idx, code in enumerate(s)]
    )
    encode64_str = base64.b64encode(misplaced_string.encode()).decode()
    return encode64_str


def decode64(s: str) -> str:
    decode64_str = base64.b64decode(s.encode()).decode()

    original_string = "".join(
        [chr(ord(code) - (idx % 5)) for idx, code in enumerate(decode64_str)]
    )
    return original_string


if __name__ == "__main__":
    c = encode64("https://www.baidu.com/1234")
    print(c)
    print(decode64(c))
