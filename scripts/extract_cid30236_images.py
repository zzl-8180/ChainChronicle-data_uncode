"""Export cid30236's icon and distinct image forms from acquired cache.

Run from the project root with the existing .venv. Original APK/cache are read
only; all derived files go to output/card_images/cid30236 (or --output).
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import UnityPy
from UnityPy.enums import TextureFormat
from PIL import Image
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from decode_data5 import NativeDecoder
from il2cpp_sample_code import Native
from metadata_targets import Metadata


CID = 30236
INVENTORY = Path('output/cache_refresh_20261015/composite_inventory.jsonl')
RECORDS = Path('output/cache_full_20261015_v3/records.jsonl')
TARGETS = {
    'portrait': ('Card_Icon', 'cha_2d_icon_30236', 'portrait.png', '头像；卡框与星级已烘焙在原始纹理中'),
    'standing_partial': ('Trimmed_Whole', 'cha_2d_whole_30236', 'standing_partial.png', '原始透明上半身图；画面边缘截断身体及装饰，不是完整全身立绘'),
    'bustup': ('Trimmed_BustUp', 'cha_2d_face_30236', 'bustup.png', '透明半身图变体'),
    'card': ('Card_OrgSize', 'cha_2d_card_30236', 'card.png', '卡面；原图含龙、背景、卡框、标题及星级，不是独立立绘'),
    'card_long': ('Card_LongVer3', 'cha_2d_tanz_30236', 'card_long.png', '长条卡面用纹理；保留存储尺寸，不按界面显示比例拉伸'),
}


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def binding_evidence(out):
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    methods = []
    for index in (6583, 6584, 6586, 34847, 34848, 24918):
        row = n.method(index)
        start = int(row['native_rva'], 16)
        end = min(p for p in n.pointers if p > start)
        code = n.raw[start:end]
        insns = list(md.disasm(code, start))
        assert sum(i.size for i in insns) == len(code)
        filename = f"method_{index}_{row['name']}.txt"
        (out / filename).write_text('\n'.join(
            f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in insns) + '\n', encoding='utf-8')
        row.update(code_sha256=sha(code), disassembly=filename,
                   boundary='Entry to next registered method; inspect RET for normal return')
        methods.append(row)
    literals = [n.literal(slot) for slot in (0x29b97a0, 0x29a0140, 0x29c1cf8, 0x29c4608,
                                            0x29c1580, 0x29d8a80, 0x29cd250, 0x29bf0f8, 0x29a2f80)]
    assert [r['text'] for r in literals] == ['D5', 'cha_2d_whole_', 'cha_2d_icon_', 'Trimmed_Whole',
                                            'Trimmed_WholeLong', 'cha_2d_wholeLong_{0:D5}',
                                            'cha_2d_card_{0:D5}.scr', 'Resource/Card', 'cha_2d_face_']
    core = Native(m, 'mscorlib.dll')
    helpers = [core.method(i) for address in (0x10ca040, 0x1218f70, 0x1217a74)
               for i in core.method_by_rva[address]]
    return {
        'metadata': 'work/protection/metadata_aei_decoded.bin',
        'native_image': 'work/protection/il2cpp_loader_seed1.bin',
        'methods': methods, 'literals': literals, 'resolved_string_helpers': helpers,
        'interpretation': {
            'whole': 'GetCharaTextureNameWhole(cid): Int32.ToString("D5") then String.Concat("cha_2d_whole_", formatted cid). daCharacter.GetCharaWholeBundleName(charaId,out path,out filename) assigns path="Trimmed_Whole" and the same generated name.',
            'portrait': 'GetCharaTextureNameIcon(cid): Int32.ToString("D5") then String.Concat("cha_2d_icon_", formatted cid). Bundle container independently identifies 2d/card_icon and the matching Texture2D.',
            'wholelong': 'daCharacter.GetCharaWholeLongBundleName assigns Trimmed_WholeLong and String.Format("cha_2d_wholeLong_{0:D5}", charaId). This proves a naming route, not that a particular cid has such a file.',
            'hires_card': 'CharaInfoCard coroutine MoveNext (24918) formats cha_2d_card_{0:D5}.scr with charaId, constructs DeliverFileInfo("Resource/Card", filename), downloads bytes, then calls ServerProvider.DecodeRotData. This is a card route; unframed full-body content is unproven.',
            'limits': 'Static client naming and bundle object references establish asset binding; no claim that a live player instance loaded this cache snapshot.',
        },
    }


def export_one(decoder, source, role, name, filename, description, expected_container, out):
    path = Path(source['work_file'])
    raw = path.read_bytes()
    assert len(raw) == source['bytes']
    pointer = decoder.e.allocate(len(raw), raw)
    accepted = decoder.call(0x2097c, pointer, len(raw))
    converted = bytes(decoder.e.uc.mem_read(pointer, len(raw)))
    assert accepted == 1 and converted.startswith(b'UnityFS\0')
    assert converted[256:] == raw[256:], 'Observed transform must affect first 256 bytes only'
    cursor = 12
    for _ in range(2):
        cursor = converted.index(b'\0', cursor) + 1
    assert struct.unpack_from('>Q', converted, cursor)[0] == len(converted)
    bundle_file = f'{name}.unityfs'
    (out / bundle_file).write_bytes(converted)
    env = UnityPy.load(converted)
    objects = list(env.objects)
    assert len(objects) == 2
    bundle_obj, = [o for o in objects if o.type.name == 'AssetBundle']
    texture_obj, = [o for o in objects if o.type.name == 'Texture2D']
    bundle = bundle_obj.read_typetree()
    assert bundle['m_Dependencies'] == []
    entry, = bundle['m_Container']
    assert entry[0] == expected_container
    assert entry[1]['asset'] == {'m_FileID': 0, 'm_PathID': texture_obj.path_id}
    texture = texture_obj.read()
    assert texture.m_Name == name
    picture = texture.image
    assert picture.size == (texture.m_Width, texture.m_Height)
    picture.save(out / filename)
    with Image.open(out / filename) as check:
        check.load()
        assert check.size == picture.size and check.mode == picture.mode
        assert check.tobytes() == picture.tobytes()
    alpha = picture.getchannel('A') if 'A' in picture.getbands() else None
    hist = alpha.histogram() if alpha else None
    return {
        'role': role, 'description': description,
        'status': 'CONFIRMED_CLIENT_ID_BINDING' if role in ('portrait', 'standing_partial', 'bustup') else 'CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH',
        'source': source, 'source_sha256': sha(raw), 'original_header64_hex': raw[:64].hex(),
        'conversion': {'function': 'DecodeXorData', 'native_rva': '0x2097c',
                       'returned': accepted, 'decoded_header': 'UnityFS',
                       'derived_bundle': bundle_file, 'decoded_sha256': sha(converted),
                       'method': 'Existing NativeDecoder initializes the recovered NUtils image using the local APK certificate; execute its original DecodeXorData on a guest copy. No data5 AES, rotation, or chronicle master conversion.'},
        'asset_bundle': bundle,
        'objects': [{'type': o.type.name, 'name': o.peek_name(), 'path_id': o.path_id,
                     'serialized_file': o.assets_file.name, 'byte_start': o.byte_start,
                     'byte_size': o.byte_size} for o in objects],
        'texture': {'name': texture.m_Name, 'path_id': texture_obj.path_id,
                    'width': texture.m_Width, 'height': texture.m_Height,
                    'unity_texture_format': int(texture.m_TextureFormat),
                    'unity_texture_format_name': TextureFormat(texture.m_TextureFormat).name,
                    'stream': {'path': texture.m_StreamData.path,
                               'offset': texture.m_StreamData.offset, 'size': texture.m_StreamData.size}},
        'png': {'file': filename, 'width': picture.width, 'height': picture.height,
                'mode': picture.mode, 'alpha_extrema': list(alpha.getextrema()) if alpha else None,
                'transparent_pixels': hist[0] if hist else 0,
                'partial_alpha_pixels': sum(hist[1:255]) if hist else 0,
                'opaque_pixels': hist[255] if hist else picture.width * picture.height,
                'alpha_nonzero_bbox': list(alpha.getbbox()) if alpha and alpha.getbbox() else None,
                'processing': 'UnityPy Texture2D.image decodes the native texture format and handles Unity vertical orientation. Export complete mip 0 at original dimensions. No manual crop, resize, rotation, alpha replacement, or compositing.',
                'verified_reopened_pixel_identical': True},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('output/card_images/cid30236'))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    records = [json.loads(line) for line in RECORDS.open(encoding='utf-8')]
    record, = [r for r in records if r['table'] == 'charainfo' and r['raw'].get('cid') == CID]
    assert record['raw']['name'] == 'チーカ' and record['raw']['title'] == '《Y.G.1009》竜の眷属'
    save_json(out / 'character_record.json', record)
    rows = [json.loads(line) for line in INVENTORY.open(encoding='utf-8')]
    image_candidates = [r for r in rows if f'30236.bdl' in r['path']
                        and '/Voice/' not in r['path'] and '/Character/' not in r['path']]
    save_json(out / 'image_candidates.json', image_candidates)
    evidence = binding_evidence(out)
    save_json(out / 'binding_evidence.json', evidence)
    decoder = NativeDecoder()
    results = []
    for role, (group, name, filename, description) in TARGETS.items():
        expected = f'files/Bundle/{group}/{name}.bdl'
        source, = [r for r in rows if r['path'] == expected]
        container = f'assets/resources/2d/{group.lower()}/{name}.tga'
        results.append(export_one(decoder, source, role, name, filename, description, container, out))
    missing_routes = ['files/Bundle/Trimmed_WholeLong/cha_2d_wholeLong_30236.bdl',
                      'Resource/Card/cha_2d_card_30236.scr']
    apk_matches = []
    apk_index = Path('output/unity/objects.jsonl')
    for line in apk_index.open(encoding='utf-8'):
        obj = json.loads(line)
        if '30236' in str(obj.get('name')) or 'chica' in str(obj.get('name')).lower():
            apk_matches.append(obj)
    resource_index = Path('output/unity/ResourceManager_13.json')
    containers = json.loads(resource_index.read_bytes())['m_Container']
    resource_matches = [r for r in containers if '30236' in r[0] or 'chica' in r[0].lower()]
    manifest = {
        'cid': CID, 'name': '《Y.G.1009》竜の眷属 チーカ',
        'status': 'PORTRAIT_CONFIRMED_FULL_BODY_NOT_LOCATED_PARTIAL_ART_EXPORTED',
        'inventory': str(INVENTORY), 'record': str(RECORDS),
        'record_pointer': record['location']['json_pointer'],
        'dependencies': {'UnityPy': UnityPy.__version__, 'Pillow': Image.__version__},
        'decoder_initialization': decoder.provenance, 'images': results,
        'scope': 'Only five explicitly selected cid30236 image bundles are transformed and parsed. The Sortie variant is listed but not decoded; no bulk game extraction.',
        'full_body_search': {
            'status': 'NOT_LOCATED_IN_SCOPED_INDEX_CHECKS',
            'cache_cid_filename_matches': [r['path'] for r in rows if '30236' in r['path']],
            'wholelong_route_inventory_hits': [r['path'] for r in rows if r['path'] == missing_routes[0]],
            'hires_scr_filename_inventory_hits': [r['path'] for r in rows if 'cha_2d_card_30236.scr' in r['path']],
            'apk_object_name_index': str(apk_index), 'apk_name_matches': apk_matches,
            'apk_resource_index': str(resource_index), 'apk_resource_key_matches': resource_matches,
            'limits': 'Index non-matches are not proof that the asset does not exist. Other bundles, private storage, and server content are outside this single-character check. No layout exists in the five self-contained bundles to recover truncated body parts or separate baked card layers.',
            'minimum_next_step': 'Obtain an authoritative cid30236 unframed full-body asset reference from the resource/download index. First check whether the confirmed WholeLong naming route is actually assigned to this cid. If a validated target is outside the acquired cache, collect only that target. The .scr route is an optional higher-resolution CARD lead, not proof of a complete standalone illustration.',
        },
        'reference': 'output/card_comparison_cid30236/reference.png is external visual reference only; never read by this extraction script.',
        'verification': 'PNG reload, original texture dimensions, alpha statistics, direct AssetBundle pointer and client cid-to-name linkage. No whole-game audit.',
    }
    save_json(out / 'manifest.json', manifest)
    lines = [
        'cid30236 / 《Y.G.1009》竜の眷属 チーカ — 单角色图片验证',
        '',
        '结果：头像已确认；完整无卡框全身立绘尚未定位。standing_partial.png 为源包内自带的上半身透明图，不能冒充完整立绘。',
        '原始纹理在卡面/长条卡面中可能以不同界面比例显示；本次严格保留存储分辨率。',
        '',
    ]
    for result in results:
        png = result['png']
        lines += [f"{png['file']}: {png['width']}×{png['height']} / {png['mode']} / Alpha {png['alpha_extrema']}",
                  result['description'], f"缓存：{result['source']['work_file']}",
                  f"原件：{result['source']['archive']} :: {result['source']['archive_member']}",
                  f"包内：{result['asset_bundle']['m_Container'][0][0]}",
                  f"Texture2D：{result['texture']['name']} / pathID={result['texture']['path_id']}", '']
    lines += [
        '关联依据：charainfo.data5 /charainfo/349 明确 cid=30236、标题和姓名；CharacterFactory 命名函数将传入 cid 以 D5 格式拼接到 icon/whole/face 前缀。',
        '头像与上半身图的包内 AssetBundle.m_Container 直接指向对应独立 Texture2D，且对象名称和角色外观均相符。卡面与长条变体另以包内引用和视觉核对区分。',
        '详细原值、原生函数地址、字符串槽位、对象指针和透明像素统计见 character_record.json、binding_evidence.json、manifest.json 及 method_*.txt。',
        '',
        '处理：复用 NativeDecoder 初始化和 NUtils 原生 DecodeXorData(0x2097c)；仅转换所选五包的内存副本，取得有效 UnityFS 后由 UnityPy 解压纹理并导出原尺寸 mip 0。',
        '无 Sprite、无图集、无多层布局或独立 Alpha 对象；每包仅一个 AssetBundle 和一个 Texture2D，依赖列表为空。没有手工裁切、缩放、旋转、合成或修图。',
        '“上半身”是原资源画面本身的截断；本脚本未从大图裁下该部分。头像卡框、卡面标题与背景均为原纹理自带。',
        'PNG 已重新打开验证尺寸、模式、像素一致；RGBA 不等于有透明像素：头像/卡面/长条图 Alpha 全255，两个透明图有0—255 Alpha。',
        '',
        '视觉核对：人工查看原始导出图与 output/card_comparison_cid30236/reference.png；发色、眨眼表情、角饰、黄蓝服装相符，卡面图构图也与截图一致。',
        '参考截图只用于核对；提取脚本不读取它，未从截图裁图。',
        '',
        '完整立绘阻塞：已导出的 whole 资源仅上半身，card 资源已烘焙卡框/背景。当前组合缓存索引未命中该 cid 的 WholeLong 包或高清 .scr 文件，APK 现有对象名/资源键索引也无目标命中。',
        '状态为“尚未定位”，不是“包无法解析”或“确认资源不存在”。已选五包均解析成功。',
        '最小下一步：先取得资源/下载索引中 cid30236 的无卡框全身图引用，确认该 cid 是否实际配置 WholeLong；若已确认的目标不在本地采集范围，再只补取该目标。高清卡面 .scr 仅是卡面线索，不保证含独立全身图。',
        '',
        '复现：在 E:\\代码项目\\锁链战记数据解包 根目录执行：',
        '.venv\\Scripts\\python.exe -B scripts/extract_cid30236_images.py',
        '可加 --output output/card_images/cid30236_rerun 写入另一个独立目录。',
        '依赖全部来自现有 .venv；还需要现有恢复镜像、APK证书、原缓存工作副本及上述索引。未安装新工具。',
    ]
    (out / 'SOURCES.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': manifest['status'], 'output': str(out),
                      'images': [{'role': r['role'], **r['png']} for r in results]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
