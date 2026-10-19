"""Stable fragment spans in decoded JSON field strings, before literal-newline cleanup."""
import re


def fragment_positions(raw):
    raw=str(raw or '')
    chars=[];mapping=[];i=0
    while i<len(raw):
        if raw[i:i+2]=='\\n':chars.append('\n');mapping.append((i,i+2));i+=2
        else:chars.append(raw[i]);mapping.append((i,i+1));i+=1
    text=''.join(chars);cut=text.find('[i][c]');body=text[:cut] if cut>=0 else text
    out=[];start=0
    for match in list(re.finditer(r'。|\n|◆',body))+[None]:
        end=len(body) if match is None else match.end() if match.group()=='。' else match.start()
        a,b=start,end
        while a<b and body[a] in ' ◆\r\t\n':a+=1
        while b>a and body[b-1] in ' ◆\r\t\n':b-=1
        if a<b:out.append(dict(japanese=body[a:b],clean_span=[a,b],raw_span=[mapping[a][0],mapping[b-1][1]],
                              coordinate_system='decoded JSON field string Unicode code points; zero-based half-open; before literal \\n cleanup; not file bytes'))
        if match is not None:start=match.end()
    return out


def position_identity(cid,group,source,table,ident,level_state,level,span,original_group,execution_context=None):
    return [cid,group,original_group,source.get('source_key'),source.get('field_json_pointer',source.get('json_pointer')),
            table,ident,level_state,level,execution_context,span['raw_span'][0],span['raw_span'][1]]
