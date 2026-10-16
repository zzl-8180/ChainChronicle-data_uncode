"""Preserve conflict records and test actual per-ID primary/fallback branching."""
import hashlib
import json
from pathlib import Path

from phase_d_chain_probe import Guest, fvalue, UC_ARM64_REG_S0
from sample_trace import locate_record


class PriorityGuest(Guest):
    def __init__(self,native,cache,base):
        self.base_rows = base
        self.labels = {}
        super().__init__(native,cache)

    def hook(self,cpu,address,size,unused):
        if address-0x50000000==0x1823a54:
            sid = self.reg(1)&0xffffffff
            result = 0
            if sid in self.base_rows:
                old = self.rows
                self.rows = self.base_rows
                result = self.skill(sid)
                self.rows = old
                self.labels[result] = 'APK'
            self.lookups.append({'id':sid,'layer':'APK','found':bool(result)})
            self.ret(result)
            return
        super().hook(cpu,address,size,unused)


def selected(path,array,key,value,original_json):
    raw = Path(path).read_bytes()
    rows = json.loads(raw)[array]
    matches = [i for i,r in enumerate(rows) if r[key]==value]
    if len(matches)!=1: raise ValueError('Conflict record not unique')
    record,location = locate_record(raw,array,matches[0])
    return {'file':path,'record':record,'location':location,
            'location_scope':'Original decompressed UTF8 JSON bytes' if original_json else 'Exported TypedTree JSON bytes, not original Unity binary record bytes',
            'file_sha256':hashlib.sha256(raw).hexdigest()}


def main():
    cache = selected('output/decoded/skilllist.data5.json.raw','skilllist','skillid',36000358,True)
    base = selected('output/base_master/_mdSkill.json','skilllist','skillid',36000358,False)
    assert cache['record']['param1']==400 and base['record']['param1']==300.0
    native = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
    cases = []
    missing_field = dict(cache['record'])
    del missing_field['param1']
    for name,primary,secondary,expected in (
        ('both_records_present',{36000358:cache['record']},{36000358:base['record']},400.0),
        ('JSON_id_absent',{}, {36000358:base['record']},300.0),
        ('both_ids_absent',{}, {},None),
        ('counterfactual_JSON_param1_missing',{36000358:missing_field},{36000358:base['record']},0.0)):
        g = PriorityGuest(native,primary,secondary)
        obj,_ = g.run(0x181be68,g.alloc(0x30),36000358,0)
        value = None
        if obj:
            g.run(0x1dbcf3c,obj,0)
            value = fvalue(g.uc.reg_read(UC_ARM64_REG_S0))
        assert value==expected,(name,value,expected)
        cases.append({'case':name,'lookup_sequence':g.lookups,'param1_after_native_getter':value,'status':'PASS',
                      'scope':'Existing source records except explicitly named counterfactual; per-layer lookup and engine scalar supplied, actual daSkill.get branch/get_param1 execute'})
    archive = json.loads(Path('output/base_master/report.json').read_text(encoding='utf-8'))
    result = {'status':'STATIC_RULE_AND_BOUNDED_BRANCH_PROVEN','skill_id':36000358,
              'source_records':{'APK':base,'phone_cache':cache},
              'APK_original_component':{'source_sha256':archive['source_sha256'],
                                        'serialized_file':archive['serialized_file'],
                                        'object_path_id':archive['object_path_id'],
                                        'object_sha256':archive['object_sha256'],
                                        'record_pointer_in_component':'/_mdSkill'+base['location']['json_pointer']},
              'native_rule':{'query':'daSkill.get@0x181be68 calls internal_get first; non-null returns immediately; null tails to internalAB_get',
                             'JSON_field':'daSkill.skilllist@+0x10, assigned/reset by FromJSONDictionary@0x1823c68',
                             'APK_field':'daSkill.ab_skilllist@+0x18, assigned by FromScriptableObject@0x1823e88 from ChronicleArchiveData._mdSkill',
                             'APK_load_callback':'DataAccessor.<getMasterData_sub>b__0@0x1c02540 calls FromScriptableObject at0x1c025d0 then SortListAB at0x1c025dc',
                             'JSON_load_callback':'DataAccessor.<getMasterSkillList>b__1@0x1c0357c calls FromJSONDictionary at0x1c035d8 then SortList at0x1c035ec',
                             'granularity':'Per-record ID fallback; no missing-field merge into APK record',
                             'conditional_value':'If this snapshot populates JSON skilllist successfully, lookup36000358 returns400; if ID absent there and APK base populated, returns300'},
              'actual_current_device_value':{'status':'UNKNOWN','value':None,
                                             'reason':'Current device loaded JSON table/accepted version not observed; no cache filename/time based choice'},
              'native_image_sha256':hashlib.sha256(native).hexdigest(),'cases':cases,
              'limits':['Layer lookup fixture returns matching source object; generic binary search itself not reimplemented as game runtime',
                        'Record0.0 in missing-field scenario is constructor behavior evidence, not a new source value',
                        'Original APK/cache records remain separate and unmodified']}
    out = Path('output/phase_d')
    out.mkdir(exist_ok=True)
    (out/'source_rule_36000358.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'cases':[(r['case'],r['param1_after_native_getter']) for r in cases],
                      'actual_device':result['actual_current_device_value']},ensure_ascii=False))


if __name__=='__main__':
    main()
