"""Trace cid30236 WholeLong selection and verify native image/display ratios.

Read existing recovered code, one APK container and the five already-decoded
target bundles. Do not decode any additional cache bundle or contact a server.
"""
import argparse
import json
import struct
from pathlib import Path

import UnityPy
from PIL import Image
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from il2cpp_sample_code import Native
from metadata_targets import Metadata


ROOT = Path('output/card_images/cid30236')
METHODS = (7789, 10729, 10732, 24567, 24593, 24910, 24918, 29204, 32896, 33237,
           34848, 35662, 35666, 38777, 38778, 39015)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def dump_method(n, mi, out):
    row = n.method(mi)
    start = int(row['native_rva'], 16)
    end = min(a for a in n.pointers if a > start)
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    insns = list(md.disasm(n.raw[start:end], start))
    assert sum(i.size for i in insns) == end - start
    pages, literals, calls, lines = {}, [], [], []
    for ins in insns:
        word = struct.unpack_from('<I', n.raw, ins.address)[0]
        note = []
        if word & 0xffc00000 == 0xf9400000 and (word >> 5 & 31) in pages:
            slot = pages[word >> 5 & 31] + (word >> 10 & 4095) * 8
            try:
                lit = n.literal(slot)
            except (ValueError, struct.error):
                pass
            else:
                literals.append({'instruction_rva': hex(ins.address), **lit})
                note.append(repr(lit['text']))
        if ins.mnemonic in ('bl', 'b') and ins.op_str.startswith('#0x'):
            for ci in n.method_by_rva.get(int(ins.op_str[1:], 16), []):
                callee = n.method(ci)
                calls.append({'instruction_rva': hex(ins.address), 'callee': callee})
                note.append(callee['declaring_type'] + '.' + callee['name'])
        for reg in ins.regs_access()[1]:
            reg_name = md.reg_name(reg)
            if reg_name.startswith(('x', 'w')) and reg_name[1:].isdigit():
                pages.pop(int(reg_name[1:]), None)
        if ins.mnemonic == 'adrp':
            pages[word & 31] = ins.operands[1].imm
        lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str} ' + '; '.join(note))
        if ins.mnemonic in ('bl', 'blr'):
            pages = {r: p for r, p in pages.items() if r >= 19}
        elif ins.mnemonic in ('br', 'b', 'ret') or ins.mnemonic.startswith('b.'):
            pages.clear()
    filename = f'method_{mi}.txt'
    (out / filename).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {**row, 'disassembly': filename, 'literals': literals, 'direct_calls': calls,
            'boundary_limit': 'Next registered method entry; exceptional tails can follow RET. Literal scan is a bounded straight-line aid, not a full CFG.'}


def widget_from_owner(assets, component_id, field_index, field_name, out, pointer_offset=None):
    owner = assets.objects[component_id]
    raw = owner.get_raw_data()
    assert struct.unpack_from('<I', raw, 28)[0] == 0, 'Expected empty MonoBehaviour name'
    if pointer_offset is None:
        pointer_offset = 32 + 12 * field_index
    file_id, path_id = struct.unpack_from('<iq', raw, pointer_offset)
    assert file_id == 0
    widget = assets.objects[path_id]
    head = widget.parse_monobehaviour_head()
    assert head.m_Script.deref().read_typetree()['m_ClassName'] == 'UITexture'
    b = widget.get_raw_data()
    assert len(b) == 312 and struct.unpack_from('<I', b, 28)[0] == 0
    # Minimal serialized prefix, NOT native in-memory field offsets:
    # MonoBehaviour head 32; 4 x AnchorPoint(target PPtr 12, relative 4,
    # absolute 4); updateAnchors 4; mColor 16; mPivot 4; width/height.
    anchors = [dict(zip(('file_id', 'path_id', 'relative', 'absolute'),
                       struct.unpack_from('<iqfi', b, 32 + 20 * i))) for i in range(4)]
    width, height = struct.unpack_from('<ii', b, 0x88)
    aspect, = struct.unpack_from('<f', b, 0xac)
    assert abs(aspect - width / height) < 1e-6
    # This build's serialized UITexture tail: Rect 16, texture PPtr 12,
    # shader PPtr 12, border Vector4 16, fixedAspect bool + alignment 4.
    uv = struct.unpack_from('<4f', b, len(b) - 60)
    assert uv == (0, 0, 1, 1)
    fixed_aspect, = struct.unpack_from('<I', b, len(b) - 4)
    assert fixed_aspect == 0
    go = head.m_GameObject.deref().read()
    trans = next(p.component.deref().read_typetree() for p in go.m_Component
                 if p.component.deref().type.name == 'Transform')
    chain = []
    current = trans
    while True:
        scale = current['m_LocalScale']
        assert scale['x'] == scale['y'] and scale['x'] != 0, 'Nonuniform UI scale needs explicit aspect calculation'
        chain.append({'game_object': assets.objects[current['m_GameObject']['m_PathID']].read().m_Name,
                      'scale': scale})
        parent = current['m_Father']
        if not parent['m_PathID']:
            break
        assert parent['m_FileID'] == 0
        current = assets.objects[parent['m_PathID']].read_typetree()
    (out / f'owner_{component_id}.bin').write_bytes(raw)
    (out / f'UITexture_{path_id}.bin').write_bytes(b)
    texture_file, texture_id = struct.unpack_from('<iq', b, len(b) - 44)
    assert texture_file == 0
    default_name = assets.objects[texture_id].peek_name() if texture_id else None
    return {'owner_component': component_id, 'serialized_field': field_name,
            'owner_field_pointer_byte_offset': pointer_offset,
            'widget_component': path_id, 'game_object': go.m_Name,
            'width': width, 'height': height, 'aspectRatio': aspect,
            'serialized_width_offset': '0x88', 'serialized_height_offset': '0x8c',
            'serialized_aspect_ratio_offset': '0xac', 'full_texture_uv': list(uv),
            'fixedAspect': bool(fixed_aspect), 'anchors': anchors,
            'placeholder_texture_path_id': texture_id, 'placeholder_texture_name': default_name,
            'local_transform': trans, 'ancestor_uniform_scales': chain,
            'layout_basis': 'Minimal prefix derived from this build UIRect.AnchorPoint/UIRect/UIWidget field order and nonserialized cache flags; 2 separate prefabs agree with their stored aspectRatio. Full MonoBehaviour type tree is unavailable. These are prefab dimensions, not a claim to run every UI animation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'followup')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    methods = [dump_method(n, mi, out) for mi in METHODS]
    fields = {}
    for ti in (180, 182, 189, 295, 792, 2896, 2903, 2930, 3391, 4469, 5072):
        fields[m.string(m.types[ti][0])] = [
            {**f, 'native_type': n.type_info(f['type_index'])} for f in n.fields(ti)]
    assert [f['name'] for f in fields['AnchorPoint'][:3]] == ['target', 'relative', 'absolute']
    assert all(not int(f['native_type']['bits'], 16) & 0x80 for f in fields['AnchorPoint'][:3])
    assert all(int(f['native_type']['bits'], 16) & 0x80 for f in fields['AnchorPoint'][3:])
    assert [f['name'] for f in fields['UIWidget'][:5]] == ['mColor', 'mPivot', 'mWidth', 'mHeight', 'mDepth']
    enum = {f['name']: n.default(f['index'])['value'] for f in n.fields(791) if f['name'] != 'value__'}
    jump = list(n.raw[0x206fb38:0x206fb3d])
    branches = {name: hex(0x1399378 + 4 * jump[value]) for name, value in enum.items()}
    assert branches['WholeLong'] == '0x1399440' and branches['Body'] == '0x139967c'
    inventory_path = Path('output/cache_refresh_20261015/composite_inventory.jsonl')
    rows = [json.loads(line) for line in inventory_path.open(encoding='utf-8')]
    index_names = {'files2.json', 'files.json', 'filelist.json'}
    full_body = {
        'status': 'CID30236_WHOLELONG_ASSIGNMENT_UNDETERMINED',
        'reason': 'A generic name factory is not per-character assignment. CommonMenuBalloon.RequestAssetBundle checks daFile.isServerFileExists before requesting WholeLong. The decisive server delivery index is not in the acquired external-cache inventory.',
        'gate': {'method_index': 10729, 'format_at': '0x1736164',
                 'server_index_check_at': '0x17361bc', 'false_branch_at': '0x17361c0',
                 'load_only_after_true_at': '0x17362a4'},
        'server_index_chain': ['DataAccessor.getMasterFileList (32896)',
                               'ServerProvider.getDeliverList / MoveNext (39015)',
                               'Bdl21_And/files2.json via WebClient.Get',
                               'CalcSHA1.CheckData then callback (33237)',
                               'daFile.processServerBundleFileList (35662)',
                               'daFile._serverHashArray; isServerFileExists (35666)'],
        'target': 'Trimmed_WholeLong/cha_2d_wholeLong_30236.bdl',
        'local_inventory': str(inventory_path),
        'target_inventory_matches': [r for r in rows if 'wholelong' in r['path'].lower() and '30236' in r['path']],
        'delivery_index_named_matches': [r for r in rows if Path(r['path']).name.lower() in index_names],
        'texture_type_enum': enum, 'load_request_case_addresses': branches,
        'limits': 'Client supports WholeLong but does not impose it for every cid. The charainfo record has no direct WholeLong flag. Cache absence cannot distinguish no server assignment from not downloaded. Other private/server data are outside this local probe.',
        'minimum_next_step': 'Capture the same client/build delivery-index response (files2.json, with server/build/time). Query only the target WholeLong path after CheckData parsing. A matching entry confirms this delivery version publishes it; then collect only that bundle. If absent, conclude only that this index version does not publish the target name. A newer live index must not be described as the 2026-10-15 acquired snapshot.',
    }
    env = UnityPy.load('work/apk/assets/bin/Data/data.unity3d')
    assets = next(a for a in env.assets if a.name == 'resources.assets')
    card_widget = widget_from_owner(assets, 138463, 4, 'CharaInfoCard._cardTexture', out)
    long_widget = widget_from_owner(assets, 108301, 2, 'CardListItem._spriteCard', out)
    icon_widget = widget_from_owner(assets, 128285, 1, 'CardKizunaButton._charaIcon', out)
    # Six PPtrs, _bonusIconAtlas array (length + PPtrs), then _texRewardChara
    # and _texChara. Do not mistake the variable array for a single PPtr.
    sortie_bytes = assets.objects[122719].get_raw_data()
    atlas_count, = struct.unpack_from('<I', sortie_bytes, 32 + 6 * 12)
    whole_pointer_offset = 32 + 6 * 12 + 4 + atlas_count * 12 + 12
    whole_widget = widget_from_owner(assets, 122719, 8, 'PanelSortieLoginNext._texChara', out,
                                     pointer_offset=whole_pointer_offset)
    whole_widget['owner_array_prefix'] = {'field': '_bonusIconAtlas', 'count': atlas_count,
                                          'array_count_byte_offset': 32 + 6 * 12}
    assert (card_widget['width'], card_widget['height']) == (640, 960)
    assert (long_widget['width'], long_widget['height']) == (150, 450)
    assert (icon_widget['width'], icon_widget['height']) == (42, 42)
    assert (whole_widget['width'], whole_widget['height']) == (512, 512)
    manifest = json.loads((ROOT / 'manifest.json').read_bytes())
    quality = []
    for image in manifest['images']:
        bundle = UnityPy.load((ROOT / image['conversion']['derived_bundle']).read_bytes())
        obj = next(o for o in bundle.objects if o.type.name == 'Texture2D')
        t, tree = obj.read(), obj.read_typetree()
        expected_bytes = ((t.m_Width + 3) // 4) * ((t.m_Height + 3) // 4) * (8 if t.m_TextureFormat == 34 else 16)
        assert len(t.get_image_data()) == expected_bytes == tree['m_CompleteImageSize']
        assert tree['m_MipCount'] == 1 and tree['m_MipsStripped'] == 0
        with Image.open(ROOT / image['png']['file']) as png:
            png.load()
            assert png.mode == t.image.mode and png.size == t.image.size
            assert png.tobytes() == t.image.tobytes()
        quality.append({'file': image['png']['file'], 'native_size': [t.m_Width, t.m_Height],
                        'format': image['texture']['unity_texture_format_name'],
                        'mip_count': tree['m_MipCount'], 'mips_stripped': tree['m_MipsStripped'],
                        'block_payload_expected_and_actual_bytes': expected_bytes,
                        'filter_mode': tree['m_TextureSettings']['m_FilterMode'],
                        'png_pixels_equal_native_decoder': True,
                        'quality_limit': 'Source ETC GPU compression is lossy. PNG adds no further pixel changes relative to the decoder. No higher mip or resolution is present inside this selected bundle; possible separate HD assets are not ruled out.'})
    previews = []
    for source, size, filename in [('card.png', (512, 768), 'card_display_512x768.png'),
                                   ('card_long.png', (256, 768), 'card_long_display_256x768.png')]:
        with Image.open(ROOT / source) as picture:
            preview = picture.resize(size, Image.Resampling.BILINEAR)
            preview.save(out / filename)
        with Image.open(out / filename) as check:
            check.load()
            assert check.size == size
        previews.append({'source': source, 'output': filename, 'size': list(size),
                         'processing': 'Separate display-aspect preview using measured prefab ratio and bilinear resampling (source filter mode=1). No AI, sharpening, crop, or new source detail. Original square PNG stays unchanged.',
                         'kind': 'CARD_DISPLAY_PREVIEW_NOT_STANDALONE_ART'})
    report = {'cid': 30236, 'wholelong': full_body, 'methods': methods,
              'field_layout_evidence': fields,
              'display_widgets': {'card': card_widget, 'card_long': long_widget,
                                  'portrait': icon_widget, 'standing_partial': whole_widget},
              'quality': quality, 'display_previews': previews,
              'transparent_art_ratio': 'Portrait widget is 42x42 and ordinary whole widget is 512x512, with uniform ancestor scales and full UVs: 1:1 is supported for those contexts. No alternate ratio established for face/bustup; preserve native square canvas. Do not apply card ratios to these textures.',
              'scope': 'No additional target bundles, other characters, remote requests, phone operations or skill research.'}
    write_json(out / 'trace_and_quality.json', report)
    text = '\n'.join([
        'cid30236：WholeLong 追踪与图片画质/比例复核', '',
        'WholeLong 配置结论：仍无法判定该 cid 是否实际配置，不能标成“未配置”。',
        '新证据：CommonMenuBalloon.RequestAssetBundle 将 cid 格式化为 cha_2d_wholeLong_30236，先调用 daFile.isServerFileExists；返回真后才请求加载。',
        'CharaTexManager.TextureType.WholeLong=4，对应 LoadRequest 分支0x1399440；Body=1对应普通 whole 的分支0x139967c，两种资源独立。',
        '实际资源目录由 ServerProvider 从 Bdl21_And/files2.json 获取，经过 CalcSHA1.CheckData 和 processServerBundleFileList，进入 _serverHashArray。',
        '当前外部缓存组合清单中，未找到该 cid 的 WholeLong 文件，也未找到 files2.json 索引原件。APK基础主表只含角色/技能/Boss/羁绊，不含此下载目录。',
        '最小下一步：只补取本构建对应的 files2.json 响应（保留服务器/构建/时间），查询 Trimmed_WholeLong/cha_2d_wholeLong_30236.bdl；命中后再定向补取该单包。',
        '索引新旧版本须区分；未命中只能说明该索引版本未发布该名字，不能宣称游戏从未有该图。', '',
        '画质：五个已有PNG的像素与UnityPy原生格式解码结果一致。ETC1/ETC2的压缩块字节数完整；m_MipCount均为1，m_MipsStripped均为0，没有漏导包内更高清的mip。',
        '这些是游戏缓存本身的有损GPU压缩纹理，PNG没有额外降低解码像素质量。尚不能据此排除另有独立高清资产。',
        '本机可选etcpak第二解码器在调用时异常退出，未用于改图或声称双实现一致；本次依据是源格式/块长度、既有UnityPy解码、像素与尺寸检查及视觉核对。', '',
        '比例：card.png原始存储512×512；CharaInfoCard._cardTexture指向UITexture 109376 / CardOrg，控件640×960，aspectRatio约0.6666667，UV覆盖整张纹理。显示比例应为2:3。',
        '比例：card_long.png原始存储256×256；CardListItem._spriteCard指向UITexture 106708 / SpriteCard，控件150×450，aspectRatio约0.3333333，UV覆盖整张纹理。显示比例应为1:3。',
        '以上UI尺寸来自APK prefab的最小序列化前缀解析，并以元数据字段顺序、NonSerialized缓存标志、独立存储的aspectRatio及局部Transform校验；不是完整UI类型树恢复或实机测量。',
        '先前直接按方形查看这两张卡面用纹理，确实会变形。原始方形导出是正确的存储像素；另存显示比例预览，不替代源PNG。',
        '头像：CardKizunaButton._charaIcon指向UITexture 108878，控件42×42。透明上半身：PanelSortieLoginNext._texChara指向UITexture 123768，控件512×512。两者UV完整、父节点等比缩放，1:1比例在这些使用场景有依据。',
        '半身face变体未建立其他界面比例依据，保留原始1:1画布，不套卡面比例。', '',
        '显示预览：card_display_512x768.png（卡面2:3）；card_long_display_256x768.png（长条卡面1:3）。',
        '预览仅按已核控件比例做双线性重采样，不是更高清源图，也不是无框立绘。无AI、锐化、裁切、合成。',
        '原始五张PNG保持不变。完整证据和指令地址见trace_and_quality.json与method_*.txt；UI前缀原字节保留为.bin。', '',
        '复现（项目根目录，现有.venv）：',
        '.venv\\Scripts\\python.exe -B scripts/trace_cid30236_art.py',
    ])
    (out / 'REPORT.txt').write_text(text + '\n', encoding='utf-8')
    print(json.dumps({'wholelong_status': full_body['status'],
                      'card_ratio': [card_widget['width'], card_widget['height']],
                      'long_ratio': [long_widget['width'], long_widget['height']],
                      'native_images_verified': len(quality), 'previews': previews,
                      'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
