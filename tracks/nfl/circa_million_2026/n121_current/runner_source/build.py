"""Rebuild the published recovery zipapp byte for byte from its two Python modules."""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from struct import Struct
from zipfile import ZipFile
from zlib import crc32

# The original stored entries have UTF-8 filenames, a fixed date, and no
# platform-specific attributes. These headers preserve its exact release bytes.
LOCAL = Struct("<I5H3I2H")
CENTRAL = Struct("<I6H3I5H2I")
END = Struct("<I4H2IH")
DATA_DATE = ((2026 - 1980) << 9) | (11 << 5) | 15
UTF8_FLAG = 0x800
VERSION = 20
FILES = ("__main__.py", "evidence.py")
EXPECTED = "72d84f2a5c8579f402417c5f6bc9f6791719f72eade0c20b8db7a5f63923cf5f"


def build(source_directory):
    body = BytesIO()
    index = BytesIO()
    for name in FILES:
        label = name.encode("utf-8")
        content = (source_directory / name).read_bytes()
        size = len(content)
        checksum = crc32(content)
        offset = body.tell()
        common = (UTF8_FLAG, 0, 0, DATA_DATE, checksum, size, size, len(label), 0)
        body.write(LOCAL.pack(0x04034B50, VERSION, *common))
        body.write(label)
        body.write(content)
        index.write(CENTRAL.pack(0x02014B50, VERSION, VERSION, *common, 0, 0, 0, 0, offset))
        index.write(label)
    index_start = body.tell()
    directory = index.getvalue()
    body.write(directory)
    body.write(END.pack(0x06054B50, 0, 0, len(FILES), len(FILES), len(directory), index_start, 0))
    result = body.getvalue()
    if hashlib.sha256(result).hexdigest() != EXPECTED:
        raise ValueError("archive fingerprint differs from the published release")
    with ZipFile(BytesIO(result)) as archive:
        if tuple(archive.namelist()) != FILES or archive.testzip() is not None:
            raise ValueError("rebuilt archive verification failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    destination = parser.parse_args().output
    release = build(Path(__file__).resolve().parent)
    try:
        with destination.open("xb") as file:
            file.write(release)
    except FileExistsError:
        if destination.read_bytes() != release:
            raise SystemExit("output already exists with different bytes")
    print(f"{EXPECTED}  {destination}")


if __name__ == "__main__":
    main()
