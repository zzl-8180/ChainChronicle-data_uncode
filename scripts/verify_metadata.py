"""Check native/model agreement and reject malformed metadata boundaries."""
import hashlib
import json
import struct
from pathlib import Path

from metadata_targets import Metadata


def main():
    raw = Path('work/protection/metadata_aei_decoded.bin').read_bytes()
    m = Metadata(raw)
    expected = hashlib.sha256(raw).hexdigest()
    native = json.loads(Path('output/il2cpp/metadata_aei_probe_native.json').read_text())
    model = json.loads(Path('output/il2cpp/metadata_aei_probe_lz4_model.json').read_text())
    assert native['decoded_sha256']==model['decoded_sha256']==expected
    assert native['optional_lz4_model'] is None
    assert model['optional_lz4_model']['guest_blocks'][0]['compressed_bytes']==3779379
    checks = ['Full native AEI conversion and bounded LZ4 substitute produce identical metadata',
              'All sections end exactly at decoded file boundary; core table strides/type ownership/UTF8 names pass']
    mutations = [('truncated_header',raw[:255]),('truncated_final_section',raw[:-1])]
    changed = bytearray(raw)
    struct.pack_into('<I',changed,24,len(raw))
    mutations.append(('string_section_outside_file',bytes(changed)))
    changed = bytearray(raw)
    struct.pack_into('<I',changed,m.sections['typeDefinitions']['offset'],0xffffffff)
    mutations.append(('type_name_outside_string_table',bytes(changed)))
    for name, blob in mutations:
        try:
            Metadata(blob)
        except ValueError:
            checks.append(name+': rejected')
        else:
            raise AssertionError('Malformed metadata accepted: '+name)
    source = Path(native['source']).read_bytes()
    assert hashlib.sha256(source).hexdigest()==native['source_sha256']==model['source_sha256']
    checks.append('Encrypted metadata input unchanged')
    result = {'status':'PASS','decoded_sha256':expected,'checks':checks,
              'limit':'Structural validity and selected native analysis; no normal Android runtime initialization claim'}
    Path('output/validation/metadata_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
