"""Observed full-cache envelope variants; reuse the pinned native decryptor."""
import gzip
import hashlib
import io
import struct
from unittest.mock import patch

from decode_data5 import NativeDecoder, unique_object
import json


def parse_variant(plaintext):
    if len(plaintext)<36:raise ValueError('Truncated native envelope')
    header=struct.unpack_from('<4I',plaintext);length=header[3]
    if header[1]!=20 or length>len(plaintext)-36:raise ValueError('Invalid envelope boundary')
    payload=plaintext[36:36+length]
    if hashlib.sha1(payload).digest()!=plaintext[16:36]:raise ValueError('Native payload SHA1 mismatch')
    if payload[:3]==b'\x1f\x8b\x08':offset=0
    elif payload[6:9]==b'\x1f\x8b\x08':offset=6
    else:raise ValueError('Neither observed gzip offset 0 nor 6')
    with gzip.GzipFile(fileobj=io.BytesIO(payload[offset:])) as stream:
        decoded=stream.read(64*1024*1024+1)
    if len(decoded)>64*1024*1024:raise ValueError('Decoded JSON exceeds64MiB')
    record=json.loads(decoded.decode('utf-8'),object_pairs_hook=unique_object)
    if not isinstance(record,dict):raise ValueError('Expected top-level object')
    meta={'header_u32':list(header),'payload_length':length,'gzip_offset':offset,
          'payload_prefix_hex':payload[:offset].hex(),'sha1_match':True,'gzip_crc_and_size':'PASS',
          'gzip_decoded_bytes':len(decoded),'plaintext_sha256':hashlib.sha256(plaintext).hexdigest(),
          'json_raw_sha256':hashlib.sha256(decoded).hexdigest()}
    return record,payload,decoded,meta


def decode_variant(raw,name):
    decoder=NativeDecoder()
    start=decoder.e.uc.emu_start
    # The largest acquired input (questdigest) exceeds the original experiment's
    # instruction/time budget. This remains bounded and changes no crypto rule.
    def bounded_start(begin,end,timeout=0,count=0):
        return start(begin,end,timeout=60000000,count=max(count,120000000))
    decoder.e.uc.emu_start=bounded_start
    # NativeDecoder has no parser injection API. Scoped replacement avoids
    # changing accepted E source or copying the recovered native decryptor.
    with patch('decode_data5.parse_plaintext',parse_variant):
        result=decoder.decode(raw,name)
    result['meta']['execution_bound']={'timeout_us':60000000,'instructions':120000000}
    return result
