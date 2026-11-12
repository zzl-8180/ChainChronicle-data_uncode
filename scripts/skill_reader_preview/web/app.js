/* Offline reader. Data is emitted by the read-only adapter as local script files. */
(() => {
  'use strict';
  const catalog = window.CC_CATALOG;
  const details = window.CC_DETAILS = window.CC_DETAILS || {};
  const detailLoads = new Map();
  const pageVersion = Date.now();
  let routeVersion = 0;
  const main = document.getElementById('main');
  const state = { query: '', status: 'all', yg: false, job: '', home: '', page: 1, pageSize: 60, catalogMode: 'cards', scroll: 0, detailFilter: 'all' };
  let catalogView = null;
  let activeCid = null;
  const num = value => Number(value || 0).toLocaleString('zh-CN');
  const list = value => Array.isArray(value) ? value : [];
  const txt = value => value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const localDate = value => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? txt(value) : date.toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
  };
  const node = (tag, className, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text != null) el.textContent = txt(text);
    return el;
  };
  function button(label, action, className = '') {
    const el = node('button', className, label);
    el.type = 'button';
    el.addEventListener('click', action);
    return el;
  }
  function pressed(el, value) { el.setAttribute('aria-pressed', String(value)); return el; }
  function image(src, alt, className = 'portrait') {
    const fallback = node('span', `${className} portrait-fallback`, alt.slice(0, 1) || '✧');
    fallback.setAttribute('aria-hidden', 'true');
    if (!src || /^(?:javascript|data:text|https?):/i.test(txt(src).trim())) return fallback;
    const img = node('img', className);
    img.src = txt(src); img.alt = alt; img.loading = 'lazy';
    img.addEventListener('error', () => img.replaceWith(fallback), { once: true });
    return img;
  }
  function cardName(card) { return card.nameZh || card.name || `角色 ${card.cid}`; }
  function totals(card) {
    const wrap = node('div', 'card-totals');
    for (const [key, label, cls] of [['answer', '已解效果', ''], ['unresolved', '待解效果', 'pending']]) {
      const item = node('span', cls); item.append(node('strong', '', num(card.counts?.[key])), document.createTextNode(label)); wrap.append(item);
    }
    return wrap;
  }
  function metadata(card) {
    return [card.rarity ? `★ ${card.rarity}` : '', card.job, card.home, card.yg ? 'Y.G.' : '', `CID ${card.cid}`].filter(Boolean).join(' · ');
  }
  function openCard(card) {
    state.scroll = window.scrollY;
    location.hash = `card=${encodeURIComponent(card.cid)}`;
  }
  function cardTile(card) {
    const tile = button('', () => openCard(card), 'character');
    tile.setAttribute('aria-label', `${cardName(card)}，已解 ${card.counts?.answer || 0}，待解 ${card.counts?.unresolved || 0}，查看角色`);
    const top = node('div', 'character-top');
    top.append(image(card.icon, cardName(card)));
    const copy = node('div', 'character-copy');
    copy.append(node('div', 'card-title', card.titleZh || card.title || '角色资料'), node('div', 'card-name', cardName(card)));
    if (card.nameZh && card.name && card.nameZh !== card.name) copy.append(node('div', 'japanese', card.name));
    copy.append(node('div', 'card-meta', metadata(card)));
    top.append(copy); tile.append(top, totals(card));
    const bottom = node('div', 'card-bottom');
    const complete = card.status === 'complete' || (Number(card.counts?.descriptions) > 0 && Number(card.counts?.complete) === Number(card.counts?.descriptions));
    bottom.append(node('span', complete ? 'badge green' : 'badge', complete ? '全部描述完整' : Number(card.counts?.answer) ? '已有答案 · 仍有待核对' : '暂无效果答案'));
    bottom.append(node('span', 'badge gold', '阅读技能 →'));
    tile.append(bottom); return tile;
  }
  function indexEntry(card) {
    const item = node('li');
    const entry = button('', () => openCard(card), 'index-entry');
    entry.append(node('span', 'index-cid', card.cid));
    const name = node('span', 'index-name', cardName(card));
    if (card.titleZh || card.title) name.append(node('small', '', card.titleZh || card.title));
    entry.append(name, node('span', 'index-count confirmed', `已解 ${num(card.counts?.answer)}`), node('span', 'index-count unknown', `待解 ${num(card.counts?.unresolved)}`));
    item.append(entry); return item;
  }
  function renderCatalog() {
    activeCid = null;
    if (catalogView) { main.replaceChildren(catalogView); requestAnimationFrame(() => window.scrollTo(0, state.scroll)); return; }
    const wrap = node('div'); catalogView = wrap;
    const intro = node('section', 'intro');
    const introCopy = node('div'); introCopy.append(node('div', 'eyebrow', 'CHAIN CHRONICLE / CHARACTER LIBRARY'), node('h1', '', '角色技能数据库'), node('p', '', '中文描述与效果数值就近展示，支持按角色、已有答案与待解状态查找。'));
    const meta = catalog.meta || {};
    introCopy.append(node('div', 'metadata', meta.updated ? `${meta.acceptedCycle ? `主线 ${meta.acceptedCycle} · ` : ''}数据更新 ${localDate(meta.updated)}` : ''));
    const versionInfo = node('div');
    versionInfo.append(node('p', '', `已解、待解及完整度按主线已验收数据统计。补充核查会更新句内颜色与条件，不直接计入主线已解数。`));
    if (meta.snapshot) versionInfo.append(node('p', '', `主线版本：${meta.snapshot}`));
    const reviewStats = window.CC_BRANCH_ASSESSMENTS?.stats;
    if (reviewStats) versionInfo.append(node('p', '', `补充核查 ${num(reviewStats.reviewed)} 项：${num(reviewStats.inferred)} 项已有推断依据，${num(reviewStats.purple)} 项仍有待确认内容。`));
    introCopy.append(disclosure('数据版本与补充核查', versionInfo));
    if (meta.translations) introCopy.append(node('p', 'stat-note', Number(meta.translations.pending) === 0 ? `已逐句核对 ${num(meta.translations.readable)} 条中文描述。数值是否解出、对应条件是否确认，分别标示。` : `已提供中文 ${num(meta.translations.readable)} 句 · 中文待核对 ${num(meta.translations.pending)} 句。待核对处保留日文与数值。`));
    if (meta.translations && Number(meta.translations.pending) === 0) {
      const reviewLink = node('a', 'stat-note', '查看本轮核对结果与修改对照');
      reviewLink.href = 'audit/semantic_review.html'; introCopy.append(reviewLink);
    }
    const stats = node('div', 'stats');
    for (const [key, label] of [['cards', '全库角色'], ['withAnswer', '已有答案'], ['complete', '描述完整']]) {
      const stat = node('div', 'stat'); stat.append(node('strong', '', num(catalog.summary?.[key] ?? (key === 'cards' ? catalog.cards.length : 0))), node('span', '', label));
      if (key === 'withAnswer') stat.append(node('small', 'stat-note', '含推断；不代表整卡完成'));
      stats.append(stat);
    }
    intro.append(introCopy, stats); wrap.append(intro);
    const toolbar = node('section', 'toolbar'); toolbar.setAttribute('aria-label', '筛选角色');
    const searchRow = node('div', 'search-row');
    const searchBox = node('label', 'search-box');
    searchBox.append(node('span', '', '⌕'));
    const search = node('input'); search.type = 'search'; search.placeholder = '搜索中文名、日文名或 CID'; search.setAttribute('aria-label', '搜索中文名、日文名或 CID'); search.value = state.query;
    searchBox.append(search);
    const viewModes = node('div', 'catalog-modes'); viewModes.setAttribute('aria-label', '目录展示方式');
    const cardMode = button('角色卡片', () => { state.catalogMode = 'cards'; location.hash = ''; refresh(); });
    const indexMode = button('全部角色索引', () => { state.catalogMode = 'index'; location.hash = 'all'; refresh(); });
    viewModes.append(cardMode, indexMode);
    searchRow.append(searchBox, viewModes); toolbar.append(searchRow);
    const filterRow = node('div', 'filter-row'); const filters = [];
    for (const [key, label] of [['all', '全部'], ['answer', '已有答案'], ['none', '暂无答案'], ['complete', '全部描述完整']]) {
      const b = button(label, () => { state.status = key; state.page = 1; refresh(); }); filters.push([key, b]); filterRow.append(b);
    }
    const extras = node('div', 'filter-extra');
    function toggle(label, checked, update) {
      const el = node('label', 'toggle'); const input = node('input'); input.type = 'checkbox'; input.checked = checked;
      input.addEventListener('change', () => { update(input.checked); state.page = 1; refresh(); }); el.append(input, document.createTextNode(label)); extras.append(el); return input;
    }
    toggle('仅 Y.G.', state.yg, v => state.yg = v);
    filterRow.append(extras); toolbar.append(filterRow);
    const selects = node('div', 'filter-row');
    for (const [key, label] of [['job', '职业'], ['home', '所属']]) {
      const lab = node('label', 'select-label', label); const select = node('select'); select.setAttribute('aria-label', `按${label}筛选`);
      const all = node('option', '', `全部${label}`); all.value = ''; select.append(all);
      [...new Set(catalog.cards.map(c => txt(c[key])).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'zh-CN')).forEach(value => { const option = node('option', '', value); option.value = value; select.append(option); });
      select.value = state[key]; select.addEventListener('change', () => { state[key] = select.value; state.page = 1; refresh(); }); lab.append(select); selects.append(lab);
    }
    const reset = button('重置筛选', () => { Object.assign(state, { query: '', status: 'all', yg: false, job: '', home: '', page: 1 }); catalogView = null; renderCatalog(); }); selects.append(reset); toolbar.append(selects);
    wrap.append(toolbar);
    const result = node('div', 'result-line'); result.setAttribute('aria-live', 'polite'); result.id = 'catalog-results';
    const grid = node('div', 'card-grid');
    const indexList = node('ul', 'character-index'); indexList.setAttribute('aria-label', '全部角色索引');
    let pageCount = 1;
    let numberedButtons = [];
    function changePage(value, focusPage = false) {
      state.page = Math.max(1, Math.min(pageCount, value)); refresh();
      result.scrollIntoView({ block: 'start' });
      if (focusPage) numberedButtons.find(([page]) => page === state.page)?.[1].focus();
    }
    const pager = node('nav', 'pagination'); pager.setAttribute('aria-label', '角色目录分页');
    const previous = button('← 上一页', () => changePage(state.page - 1)); previous.setAttribute('aria-label', '上一页角色');
    const pageNumbers = node('div', 'page-numbers');
    const next = button('下一页 →', () => changePage(state.page + 1)); next.setAttribute('aria-label', '下一页角色');
    const pageSizeLabel = node('label', 'select-label', '每页');
    const pageSize = node('select'); pageSize.setAttribute('aria-label', '每页角色数量');
    for (const size of [30, 60, 120]) { const option = node('option', '', `${size}名`); option.value = String(size); pageSize.append(option); }
    pageSize.value = String(state.pageSize);
    pageSize.addEventListener('change', () => { state.pageSize = Number(pageSize.value); state.page = 1; refresh(); }); pageSizeLabel.append(pageSize);
    const jumpForm = node('form', 'page-jump'); jumpForm.setAttribute('aria-label', '跳转页码');
    const jumpLabel = node('label', '', '到第');
    const jump = node('input'); jump.type = 'number'; jump.min = '1'; jump.step = '1'; jump.inputMode = 'numeric'; jump.required = true; jump.setAttribute('aria-label', '目标页码');
    jumpLabel.append(jump, document.createTextNode('页'));
    const go = node('button', '', '跳转'); go.type = 'submit';
    jumpForm.append(jumpLabel, go);
    jump.addEventListener('input', () => jump.setCustomValidity(''));
    jumpForm.addEventListener('submit', event => {
      event.preventDefault();
      const value = Number(jump.value);
      if (!Number.isInteger(value) || value < 1 || value > pageCount) { jump.setCustomValidity(`请输入1到${pageCount}之间的页码`); jump.reportValidity(); return; }
      jump.setCustomValidity(''); changePage(value, true);
    });
    pager.append(previous, pageNumbers, next, pageSizeLabel, jumpForm);
    const bottomPager = node('nav', 'pagination-bottom'); bottomPager.setAttribute('aria-label', '页末翻页');
    const previousBottom = button('← 上一页', () => changePage(state.page - 1, true));
    const bottomPosition = node('span', 'muted');
    const nextBottom = button('下一页 →', () => changePage(state.page + 1, true));
    bottomPager.append(previousBottom, bottomPosition, nextBottom);
    wrap.append(result, pager, grid, indexList, bottomPager);
    search.addEventListener('input', () => { state.query = search.value; state.page = 1; refresh(); });
    function refresh() {
      const q = state.query.trim().normalize('NFKC').toLocaleLowerCase();
      const matched = catalog.cards.filter(card => {
        if (state.yg && !card.yg) return false;
        if (state.job && txt(card.job) !== state.job || state.home && txt(card.home) !== state.home) return false;
        const answer = Number(card.counts?.answer || 0);
        const complete = card.status === 'complete' || Number(card.counts?.descriptions) > 0 && Number(card.counts?.complete) === Number(card.counts?.descriptions);
        if (state.status === 'answer' && !answer || state.status === 'none' && answer || state.status === 'complete' && !complete) return false;
        return !q || [card.cid, card.name, card.nameZh, card.title, card.titleZh].some(value => txt(value).normalize('NFKC').toLocaleLowerCase().includes(q));
      });
      filters.forEach(([key, b]) => pressed(b, state.status === key));
      const index = state.catalogMode === 'index';
      pressed(cardMode, !index); pressed(indexMode, index);
      pageCount = Math.max(1, Math.ceil(matched.length / state.pageSize));
      state.page = Math.max(1, Math.min(pageCount, state.page));
      const start = (state.page - 1) * state.pageSize;
      result.replaceChildren(node('span', '', index ? `全部角色索引 · 共${num(matched.length)}名角色` : `第${matched.length ? state.page : 0}/${matched.length ? pageCount : 0}页 · 共${num(matched.length)}名角色`), node('span', '', index ? '点击姓名阅读技能 · 筛选条件继续生效' : matched.length ? `本页第${num(start + 1)}–${num(Math.min(start + state.pageSize, matched.length))}名` : '请调整筛选条件'));
      pager.hidden = index || !matched.length;
      bottomPager.hidden = index || !matched.length;
      grid.hidden = index; indexList.hidden = !index;
      grid.replaceChildren(); indexList.replaceChildren();
      if (index) indexList.append(...matched.map(indexEntry));
      else grid.append(...matched.slice(start, start + state.pageSize).map(cardTile));
      if (!matched.length) {
        const empty = node('div', 'empty'); empty.append(node('p', '', '没有找到符合条件的角色。'), button('清除搜索词', () => { state.query = ''; search.value = ''; refresh(); }));
        if (index) { const li = node('li', 'index-empty'); li.append(empty); indexList.append(li); } else grid.append(empty);
      }
      previous.disabled = previousBottom.disabled = state.page === 1;
      next.disabled = nextBottom.disabled = state.page === pageCount;
      bottomPosition.textContent = `第${state.page}/${pageCount}页`;
      jump.max = String(pageCount); jump.value = String(state.page); jump.setCustomValidity('');
      const pages = [...new Set([1, state.page - 1, state.page, state.page + 1, pageCount])].filter(page => page >= 1 && page <= pageCount).sort((a, b) => a - b);
      numberedButtons = []; pageNumbers.replaceChildren();
      pages.forEach((page, i) => {
        if (i && page - pages[i - 1] > 1) pageNumbers.append(node('span', 'page-gap', '…'));
        const b = button(String(page), () => changePage(page, true)); b.setAttribute('aria-label', `第${page}页`);
        if (page === state.page) b.setAttribute('aria-current', 'page');
        numberedButtons.push([page, b]); pageNumbers.append(b);
      });
    }
    refresh(); main.replaceChildren(wrap);
  }
  function disclosure(label, content) { const d = node('details', 'disclosure'); d.append(node('summary', '', label), content); return d; }
  function sourceBlock(answers, row) {
    const wrap = node('div');
    list(answers).forEach(answer => {
      const item = node('div', 'source-item');
      item.append(node('p', '', answer.text));
      if(answer.displayAssessment) {
        const review=answer.displayAssessment;
        item.append(node('p',review.status==='inferred'?'inferred':'branch-candidate',`本次复核：${review.branchInvariant?'全部实际分支的本项数值相同；分支触发条件仍未完全解释，按推断展示':review.status==='inferred'?'条件与效果已有依据，按推断展示':review.shortReason}${review.condition ? `；${review.condition}`:''}`));
        item.append(node('p','muted',review.evidence.join('；')));
      }
      if (answer.readerOrigin) item.append(node('small', 'source-origin', answer.readerOrigin));
      const dl = node('dl', 'source-grid');
      for (const [key, label] of [['branchLabel', '数值分支'], ['condition', '适用条件'], ['mappingNote', '对应说明']]) {
        if (answer[key]) dl.append(node('dt', '', answer.displayAssessment ? `原记录·${label}` : label), node('dd', '', answer[key]));
      }
      for (const [key, label] of [['file', '文件'], ['pointer', '位置'], ['field', '字段'], ['raw', '原值'], ['rule', '规则']]) {
        if (answer.source?.[key] != null) dl.append(node('dt', '', label), node('dd', '', txt(answer.source[key])));
      }
      if (answer.note) dl.append(node('dt', '', '说明'), node('dd', '', answer.note));
      if (answer.detailNote) dl.append(node('dt', '', '计算说明'), node('dd', '', answer.detailNote));
      for (const [key, label] of [['originalAnswer', '原答案'], ['originalConditions', '原条件'], ['originalConditionLabel', '条件标签'], ['limitations', '适用限制'], ['numericEvidence', '数值证据'], ['associationEvidence', '对应证据'], ['evidenceScope', '证据范围'], ['allSources', '全部来源'], ['rowId', '描述位置'], ['answerIndex', '答案序号']]) {
        if (answer.source?.[key] != null) dl.append(node('dt', '', label), node('dd', '', txt(answer.source[key])));
      }
      item.append(dl, disclosure('完整来源记录（JSON）', node('pre', 'source-json', JSON.stringify(answer, null, 2)))); wrap.append(item);
    });
    if (row.unmappedBranches?.length) wrap.append(disclosure('未对应分支参数（JSON）', node('pre', 'source-json', JSON.stringify(row.unmappedBranches,null,2))));
    if (row.candidateLinks?.length) wrap.append(disclosure('候选关联记录（JSON）', node('pre', 'source-json', JSON.stringify(row.candidateLinks,null,2))));
    if (row.id) wrap.append(node('p', '', `描述定位：${row.id}`));
    if (row.review) wrap.append(node('p', '', row.reviewMessage || '效果与数值的对应关系仍需核对。'));
    if (row.sourceRows) wrap.append(disclosure(row.levelRows ? '各等级原始记录（JSON）' : '合并前的两份记录（JSON）', node('pre', 'source-json', JSON.stringify(row.sourceRows,null,2))));
    return disclosure(row.levelRows ? '各等级说明与来源' : row.sourceRows ? '说明与来源（含角色资料）' : '说明与来源', wrap);
  }
  function answerView(answer, pendingAssociation = false) {
    const confidence = !pendingAssociation && ['confirmed', 'inferred', 'unknown'].includes(answer.confidence) ? answer.confidence : 'unknown';
    const wrap = node('div', 'answer-block');
    const line = node('span', `answer ${confidence}`, answer.text || '数值尚未解出');
    line.title = { confirmed: '已确认', inferred: '推断', unknown: '对应待核对' }[confidence];
    wrap.append(line);
    // Keep meaningful variants and conditions beside the value; repeated
    // evidence caveats are available once in the row's disclosure.
    const vagueBranch = /待核对|待确认|待核实|有独立原文/.test(txt(answer.branchLabel));
    if (answer.branchLabel && !vagueBranch) wrap.append(node('span', 'branch-label', answer.branchLabel));
    const vagueCondition = /^(?:触发条件待核实|触发条件待核对|实际触发条件仍需核对)$/.test(txt(answer.condition));
    if (answer.condition && !vagueCondition) wrap.append(node('span', 'condition', `条件：${txt(answer.condition)}`));
    else if (!pendingAssociation && (vagueBranch || vagueCondition)) wrap.append(node('span', 'condition condition-uncertain', '条件待确认'));
    if (answer.relatedDescription?.text) {
      const related = answer.relatedDescription;
      const label = `对应条件：${txt(related.text)}`;
      if (related.rowId) {
        const link = button('查看强化条件', event => {
        event.currentTarget.dispatchEvent(new CustomEvent('reveal-description', { bubbles: true, detail: { rowId: txt(related.rowId) } }));
        }, 'related-description');
        link.title = label; link.setAttribute('aria-label', label); wrap.append(link);
      }
      else wrap.append(node('p', 'condition', label));
    }
    if (pendingAssociation && answer.note) {
      const note = txt(answer.note).replace(/^这项数值已记录，与具体效果的对应仍需核对。/, '');
      if (note && note !== '原文明示；适用对象与条件见本句') wrap.append(node('span', 'answer-note', note));
    }
    return wrap;
  }
  function hasAnswer(effect) { return effect.status === 'has_answer'; }
  function isPending(effect) { return effect.status === 'unresolved' || effect.sourceStatus === 'unresolved' || list(effect.answers).some(a=>window.CC_INLINE.candidate(a)); }
  function rowMatches(row, filter) {
    if (row.levelRows) return row.levelRows.some(x=>rowMatches(x.row,filter));
    if (filter === 'all') return true;
    if (filter === 'answer') return list(row.effects).some(hasAnswer) || list(row.unboundAnswers).length > 0;
    return row.translationStatus === 'pending' || list(row.effects).some(isPending) || row.review || !list(row.effects).length;
  }
  function descriptionCopy(container, row, className) {
    if (row.translationStatus === 'pending') container.append(node('span', 'translation-pending', '中文待核对'));
    else if (row.translationStatus === 'template') {
      const label = node('span', 'translation-template', '中文整理稿');
      label.title = '已检查原文数字与关键术语；尚未逐句核对语义。';
      container.append(label);
    }
    if ((row.levelRows || row.extraLevelStage) && row.translationStatus !== 'pending') {
      const copy=node('p',className);
      const parts=window.CC_LEVELS.presentation(row,window.CC_INLINE).textParts;
      let consumedUnit = '';
      parts.forEach((part,partIndex)=>{
        if (part.text != null) {
          copy.append(document.createTextNode(part.text.slice(consumedUnit.length)));
          consumedUnit = '';
        }
        else {
          const span=node('span','level-values');
          const unit=(parts[partIndex+1]?.text || '').match(/^[%％]/)?.[0] || '';
          if(part.values.map(v=>v.value).join('/').length>26)span.classList.add('long-values');
          (part.constant ? part.values.slice(0,1) : part.values).forEach((value,index)=>{
            if(index)span.append(document.createTextNode('/'));
            span.append(node('span',value.color==='literal'?'':value.color,value.value));
          });
          if(unit)span.append(document.createTextNode(unit));
          consumedUnit = unit;
          span.title=part.values.map(v=>`${v.stage}：${v.value}${unit}`).join('；');
          span.setAttribute('aria-label',span.title);copy.append(span);
        }
      });
      container.append(copy);
    }
    else if (row.textZh && row.translationStatus !== 'pending') {
      const copy = node('p', className);
      let position = 0;
      const inlinePlan=window.CC_INLINE.plan(row);
      inlinePlan.inserts.forEach(entry => {
        copy.append(document.createTextNode(row.textZh.slice(position, entry.end)));
        const value = node('span', `inline-value ${entry.segments ? '' : entry.branchCandidate ? 'branch-candidate' : entry.answer.confidence}`);
        if (entry.segments) {
          value.append(document.createTextNode('（'));
          entry.segments.forEach((segment,index)=>{
            if (index) value.append(document.createTextNode(' / '));
            const part=node('span',`branch-number ${window.CC_INLINE.candidate(segment.answer) ? 'branch-candidate' : segment.answer.confidence}`);
            if((segment.conditionKnown || segment.conditionPartial) && segment.conditionLabel!=='本段技能' && !inlinePlan.valueOrder)part.append(node('small','branch-condition-label',`${segment.conditionLabel}：`));
            part.append(document.createTextNode(segment.text));
            if (!segment.conditionKnown && segment.branches?.length) {
              const marker=button(`[${segment.branches.map(b=>b.code).join('·')}]`,()=>{
                const target=document.getElementById(segment.branches[0].tableId);
                if (target) { target.open=true; target.scrollIntoView({block:'nearest'}); target.querySelector('summary')?.focus(); }
              },'branch-marker');
              marker.title=`${segment.conditionLabel || '条件待确认'}；查看这些数值对应的分支记录`;
              marker.setAttribute('aria-label',`查看分支 ${segment.branches.map(b=>b.code).join('、')} 的条件`);
              part.append(marker);
            }
            value.append(part);
          });
          value.append(document.createTextNode('）'));
        } else value.textContent = `（${entry.text}）`;
        const confidence = entry.branchCandidate ? '待确认' : entry.answer.confidence === 'confirmed' ? '已确认' : '推断';
        value.title = `${confidence}：${(entry.answers || [entry.answer]).map(a=>a.text).join(" / ")}。完整依据见本句“说明与来源”。`;
        value.setAttribute('aria-label', `${entry.text}，${confidence}`);
        value.dataset.effectId = entry.effect.id || '';

        copy.append(value); position = entry.end;
      });
      copy.append(document.createTextNode(row.textZh.slice(position))); container.append(copy);
    }
    else if (row.translationStatus !== 'pending') container.append(node('p', className, '中文待核对'));
    if (row.translationNote) container.append(node('p', 'translation-note', row.translationNote));
    if (row.translationStatus === 'pending' && row.original) container.append(node('p', 'original-visible', row.original));
  }
  function renderRow(row, filter, options = {}) {
    row = window.CC_LEVELS.displayRow(row,window.CC_INLINE.answerKey);
    const item = node('div', 'description');
    if (row.id && !options.omitId) item.id = txt(row.id);
    if (!options.omitId) list(row.aliasIds).forEach(id=>{ const alias=node('span','source-anchor');alias.id=id;alias.setAttribute('aria-hidden','true');item.append(alias); });
    if (!options.omitCopy) descriptionCopy(item, row, 'description-copy');
    const plan = row.levelRows || row.extraLevelStage ? window.CC_LEVELS.presentation(row,window.CC_INLINE) : window.CC_INLINE.plan(row);
    if(plan.valueOrder && !options.omitCopy) {
      const nested=plan.valueOrder.some(label=>label.includes(' / '));
      const conditions=plan.valueOrder.map((label,index)=>{
        const random='；每次预测按有效候选权重随机选档';
        const compact=label.includes(random)?label.split(random).join('')+random:label;
        return nested?`第${index+1}个数值〔${compact}〕`:compact;
      });
      item.append(node('p','value-order',`${nested?'数值对应':'数值顺序'}：${conditions.join(nested?'；':' / ')}`));
    }
    const sources = [...list(row.effects).flatMap(effect => list(effect.answers)), ...list(row.unboundAnswers)];
    if (row.sourceRows) row.sourceRows.forEach((r,i)=>{
      [...list(r.effects).flatMap(e=>list(e.answers)),...list(r.unboundAnswers)].forEach(a=>{
        if (!sources.some(existing=>window.CC_INLINE.answerKey(existing)===window.CC_INLINE.answerKey(a) && JSON.stringify(existing.source)===JSON.stringify(a.source))) sources.push({...a,readerOrigin:row.levelRows ? row.levelRows[i].stage : i ? '角色资料记录' : '技能分支记录'});
      });
    });
    const support = node('div', 'row-support');
    if (plan.strengthUnsolved && !options.omitCopy) item.append(node('p', 'strength-unsolved', '强化效果数值待解'));
    const branchEvidence = list(row.candidateLinks).length || list(row.unmappedBranches).length;
    const pending = list(row.effects).filter(effect => !list(effect.answers).length && effect.status !== 'justified_na' && !list(row.knownCandidateScopes).includes(effect.label));
    if (pending.length) item.append(node('p', row.levelTextParts?.some(p=>p.values) ? 'level-guide' : 'inline-missing', row.levelTextParts?.some(p=>p.values) ? '原文数值已列出；效果对应仍待核对。' : `${branchEvidence ? '效果对应待核对' : '尚未解出'}：${[...new Set(pending.map(e => e.label || '效果'))].join('、')}`));
    const scopeGaps=[...new Set(list(row.effects).flatMap(e=>list(e.answers)).map(a=>a.displayAssessment?.unresolvedScope).filter(Boolean))];
    if(scopeGaps.length)item.append(node('p','inline-missing',scopeGaps.join('；')));
    if (list(row.candidateLinks).length) {
      const links = node('div','candidate-links');
      const targets = new Map();
      list(row.candidateLinks).forEach(link=>targets.set(link.targetRowId,[...new Set([...(targets.get(link.targetRowId) || []),...list(link.labels)])]));
      targets.forEach((labels,targetRowId)=>links.append(button(`查看${labels.join('、') || '正文'}候选`, event=>{
        event.currentTarget.dispatchEvent(new CustomEvent('reveal-description',{bubbles:true,detail:{rowId:txt(targetRowId)}}));
      },'related-description')));
      support.append(disclosure('强化对应',links));
    }
    const held = plan.held;
    const unbound = list(row.unboundAnswers);
    const candidateAnswers=list(row.effects).flatMap(e=>list(e.answers)).filter(a=>window.CC_INLINE.candidate(a));
    const reviewReasons=[...new Set([...candidateAnswers.map(a=>a.displayAssessment?.shortReason || (a.displayBranch?.conditionKnown ? '效果对应依据待核对' : '条件待确认')),...list(row.linkedReviewReasons)])].filter((reason,index,reasons)=>reason!=='条件待确认' || !reasons.includes('分支选取待确认'));
    const hasCandidates=candidateAnswers.length || (row.linkedReviewReasons ? row.linkedReviewReasons.length : list(row.candidateLinks).length);
    const extraConditions=[...new Set(candidateAnswers.map(a=>a.condition).filter(c=>c && !/^(?:触发条件待核实|触发条件待核对|实际触发条件仍需核对|适用条件待确认|分支适用条件待确认|与本技能强化条件的对应待确认)$/.test(c)))];
    if (hasCandidates || list(row.unmappedBranches).length) {
      const note=hasCandidates ? reviewReasons.join('；') || '条件待确认' : '其他分支参数待对应';
      item.append(node('p',hasCandidates ? 'branch-pending' : 'branch-unmapped',note));
      if (extraConditions.length) support.append(disclosure('适用条件',node('p','',extraConditions.join('；'))));
    } else if (plan.branchLabel) item.append(node('p','branch-pending',plan.branchLabel));

    if (plan.visible.length) {
      const strip = node('div', 'visible-values');
      plan.visible.forEach(entry => {
        const line = node('div', 'value-comparison');
        line.append(node('span', 'comparison-label', entry.effect.label === '伤害' ? '伤害系数' : entry.effect.label));
        window.CC_INLINE.orderedAnswers(entry.effect.answers).forEach(answer => {
          const isCandidate = window.CC_INLINE.candidate(answer);
          const confidence = window.CC_INLINE.semanticUnclear(answer) ? 'unknown' : isCandidate ? 'branch-candidate' : answer.confidence;
          const value = node('span', `comparison-value ${confidence}`);
          const label = answer.levelLabel || (isCandidate ? '' : window.CC_INLINE.variantLabel(answer));
          if (label) value.append(node('small', 'variant-name', label));
          let text = window.CC_INLINE.compact(answer, entry.effect.label);
          if (entry.effect.label === '伤害') text = text.replace(/^系数\s*/, '');
          value.append(node('strong', '', text));
          value.title = `${answer.confidence === 'confirmed' ? '已确认' : answer.confidence === 'inferred' ? '推断' : '对应待核对'}：${answer.text}。${answer.mappingNote || ''}`;
          value.setAttribute('aria-label', `${label} ${text}，${isCandidate ? '分支待确认' : answer.confidence === 'confirmed' ? '已确认' : '推断'}`);
          const condition = answer.displayBranch?.conditionKnown ? answer.displayBranch.conditionLabel : answer.condition || '';
          if (condition && !/^(?:触发条件待核实|触发条件待核对|实际触发条件仍需核对)$/.test(condition)) value.append(node('small', 'value-condition', condition));
          line.append(value);
        });
        strip.append(line);
      });
      item.append(strip);
    }
    if (held.length || unbound.length) {
      const content = node('div', 'held-values');
      held.forEach(entry => {
        const section = node('div', 'held-effect');
        section.append(node('p', 'held-label', `${entry.effect.label} · ${entry.reason}`));
        list(entry.effect.answers).forEach(a => section.append(answerView(a, true)));
        content.append(section);
      });
      if (unbound.length) {
        const section = node('div', 'unbound');
        section.append(node('p', 'unbound-heading', '以下数值尚未确认对应哪项效果：'));
        unbound.forEach(a => section.append(answerView(a, true))); content.append(section);
      }
      const count = held.reduce((n, e) => n + list(e.effect.answers).length, 0) + unbound.length;
      const more = disclosure(`待对应数值 · ${count}`, content);
      more.classList.add('inline-more'); support.append(more);
    }
    if (row.original && row.translationStatus !== 'pending') support.append(disclosure('日文原文', node('p', '', row.levelRows ? row.levelRows.map(x=>`${x.stage}：${x.row.original}`).join('\n') : row.original)));
    if (sources.length || row.id) support.append(sourceBlock(sources, row));
    item.append(support);
    return item;
  }
  function conditionContext(skill, row) {
    const context = node('section', 'skill-condition');
    context.id = txt(row.id);
    list(row.aliasIds).forEach(id=>{ const alias=node('span','source-anchor');alias.id=id;alias.setAttribute('aria-hidden','true');context.append(alias); });
    context.setAttribute('aria-label', skill.conditionTitle || '强化条件');
    context.append(node('h4', 'condition-heading', skill.conditionTitle || '强化条件'));
    descriptionCopy(context, row, 'condition-original');
    if (window.CC_INLINE.plan(row).strengthUnsolved) context.append(node('p', 'strength-unsolved', '强化效果数值待解'));
    const more = node('div');
    if (skill.conditionScopeText) more.append(node('p', 'condition-scope', skill.conditionScopeText));
    context.append(renderRow(row, 'all', { omitId: true, omitCopy: true }));
    if (skill.conditionScopeText) context.append(disclosure('强化范围说明', more));
    return context;
  }
  function renderDetail(cid) {
    activeCid = cid; const card = catalog.cards.find(c => String(c.cid) === cid);
    const wrap = node('div');
    wrap.addEventListener('reveal-description', event => {
      const rowId = event.detail?.rowId;
      if (!rowId) return;
      let target = document.getElementById(rowId);
      if (!target && details[cid]) {
        state.detailFilter = 'all'; refresh();
        target = document.getElementById(rowId);
      }
      if (!target) return;
      target = target.closest('.description,.skill-condition') || target;
      target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
      target.tabIndex = -1; target.focus({ preventScroll: true });
      target.classList.add('description-highlight');
      window.setTimeout(() => target.classList.remove('description-highlight'), 2600);
    });
    const back = node('a', 'back', '← 返回角色目录'); back.href = state.catalogMode === 'index' ? '#all' : '#'; wrap.append(back);
    if (!card) { wrap.append(node('div', 'empty', '没有找到这张角色卡，请返回目录重新选择。')); main.replaceChildren(wrap); window.scrollTo(0, 0); return; }
    const rawData = window.CC_BRANCHES.apply(details[cid],window.CC_BRANCH_CANDIDATES?.cards?.[cid]);
    const data = rawData ? {...rawData,groups:window.CC_INLINE.orderGroups(window.CC_INLINE.mergeGroups(rawData.groups)).map(g=>({...g,skills:window.CC_LEVELS.groupSkills(g).map(skill=>window.CC_INLINE.prepareSkill(skill,window.CC_BRANCH_CONDITIONS?.records,window.CC_BRANCH_ASSESSMENTS?.records,window.CC_BRANCH_ASSESSMENTS?.resolvedParents))}))} : null;
    if(data) {
      const signature=skill=>JSON.stringify(list(skill.rows).map(row=>row.original));
      const special=list(data.groups).find(g=>g.id==='special_move'), denju=list(data.groups).find(g=>g.id==='denju');
      for(const skill of list(special?.skills).every(s=>s.sourceKind==='character_profile') ? list(special?.skills) : []) {
        const same=list(denju?.skills).filter(other=>signature(skill) && signature(skill)===signature(other));
        if(same.length) {
          skill.crossGroupNote='技能文字与传授相同；数值和条件按各自记录展示。';
          same.forEach(other=>other.crossGroupNote='技能文字与必杀技相同；数值和条件按各自记录展示。');
        }
      }
    }
    const hero = node('section', 'detail-hero');
    hero.append(data?.art ? image(data.art, `${cardName(card)}卡面`, 'full-card-art') : image(card.icon, cardName(card)));
    const copy = node('div', 'hero-copy'); copy.append(node('div', 'card-title', card.titleZh || card.title || ''), node('h1', '', cardName(card)));
    if (card.nameZh && card.name !== card.nameZh) copy.append(node('p', 'japanese', [card.title, card.name].filter(Boolean).join(' ')));
    copy.append(node('p', 'card-meta', metadata(card)), totals(card), node('small', 'stat-note', '含推断；已解数按主线统计，补充核查另行标色')); hero.append(copy); wrap.append(hero);
    if (!data) {
      const notice = node('section', 'not-ready'); notice.append(node('h2', '', '详情数据暂不可用'), node('p', '', `已解 ${num(card.counts?.answer)} 项，待解 ${num(card.counts?.unresolved)} 项。请检查本地数据文件后重新打开。`));
      const counts = card.counts || {}; notice.append(node('p', '', `描述状态：完整 ${num(counts.complete)} · 部分 ${num(counts.partial)} · 未解析 ${num(counts.unparsed)} · 待核对 ${num(counts.review)}`)); wrap.append(notice); main.replaceChildren(wrap); window.scrollTo(0, 0); return;
    }
    const layout = node('div', 'detail-layout'); const nav = node('nav', 'group-nav'); nav.setAttribute('aria-label', '技能分组'); nav.append(node('p', '', '技能目录'));
    list(data.groups).forEach((group, i) => { const link = node('a', '', group.label || '技能'); link.href = `#group-${i}`; link.addEventListener('click', event => { event.preventDefault(); document.getElementById(`group-${i}`)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); }); nav.append(link); });
    const reading = node('div'); const tools = node('div', 'reading-tools'); const body = node('div');
    const rows = list(data.groups).flatMap(g => list(g.skills).flatMap(s => list(s.rows)));
    const pendingChinese = rows.filter(r => r.translationStatus === 'pending').length;
    if (pendingChinese) tools.append(node('small', 'translation-pending', `${num(pendingChinese)} 句中文待核对 · 已保留日文与主线数值`));
    const filters = [];
    for (const [key, label] of [['all', '全部'], ['answer', '已有数值'], ['pending', '待解 / 待核对']]) {
      const count = rows.filter(r => rowMatches(r, key)).length;
      const b = button(`${label} ${num(count)}`, () => { state.detailFilter = key; refresh(); }); filters.push([key, b]); tools.append(b);
    }
    const shown = node('small'); shown.setAttribute('aria-live', 'polite'); tools.append(shown);
    const legend = node('div', 'legend'); legend.append(node('span', 'confirmed', '● 已确认'), node('span', 'inferred', '● 推断'), node('span', 'branch-candidate', '● 待确认'), node('span', 'unknown', '● 对应待核对'), node('span', 'not-decoded', '● 尚未解出'));
    const readingNotes = node('div');
    readingNotes.append(node('p', '', '“已有数值”包含待对应项；待对应项不计入已解效果。'));
    readingNotes.append(node('p', '', '已能核对的分支直接显示HP或Chain条件；仅条件不明确的保留字母。并列数值按本句标出的顺序阅读；同值同色合并，来源全部保留。HP按游戏整数百分比判断，0thChain表示未达到1stChain。条件有依据不代表紫色数值的效果对应已确认。'));
    readingNotes.append(node('p', '', '技能名旁的小圆点表示消耗法珠数，0珠单独注明；圆点不表示珠色。条件改变消耗时以技能正文为准。'));
    const hasDamageCoefficient = rows.some(row => [...list(row.effects).flatMap(effect => list(effect.answers)), ...list(row.unboundAnswers)].some(a => txt(a.text).includes('伤害系数')));
    if (hasDamageCoefficient) readingNotes.append(node('p', '', '伤害系数用于伤害计算，不等于面板攻击力的最终倍数；此处已含Chain修正。'));
    readingNotes.prepend(node('p', '', '括号数值对应前面的效果；金色为已有依据的推断，紫色的具体缺口见句下提示。条件与效果对应分开复核；仅缺条件证据且已补齐的改为金色，不升级为实机确认。原始记录与本次复核依据见每句的说明与来源。')); legend.append(disclosure('数值怎么看', readingNotes));
    reading.append(tools, legend, node('p', 'reading-explainer', '×C＝乘以Chain（连携）修正。完整计算见各句「说明与来源」。'));
    reading.append(body); layout.append(nav, reading); wrap.append(layout);
    function refresh() {
      const filter = state.detailFilter; filters.forEach(([key, b]) => pressed(b, key === filter)); body.replaceChildren();
      const matched = rows.filter(r => rowMatches(r, filter)).length;
      shown.textContent = `显示 ${num(matched)} / ${num(rows.length)} 条描述${data.groups.some(g=>g.skills.some(s=>s.mergedSourceCount)) ? ' · 同文已合并' : ''}`;
      list(data.groups).forEach((group, index) => {
        const section = node('section', 'skill-group'); section.id = `group-${index}`;
        const heading = node('div', 'group-heading'); heading.append(node('h2', '', group.label || '技能')); section.append(heading);
        let groupRows = 0;
        list(group.skills).forEach(skill => {
          const visible = list(skill.rows).filter(row => rowMatches(row, filter)); if (!visible.length) return;
          groupRows += visible.length;
          const skillEl = node('article', 'skill'); const skillHeading = node('div', 'skill-heading'); skillHeading.append(node('h3', '', skill.name || '技能'));
          const identity = window.CC_INLINE.skillIdentity(skill, list(group.skills));
          if (identity.stage) skillHeading.append(node('span', 'stage', skill.levelStages ? '各等级合并' : identity.stage));
          const mana=window.CC_MANA_COSTS?.records?.[skill.rows[0]?.id];
          if(mana && Number.isInteger(mana.cost) && mana.cost>=0) {
            const cost=node('span','mana-cost');
            cost.title=`消耗${mana.cost}颗法珠（${mana.basis==='explicit_zero_text' ? '原文明示' : '技能配置'}）；条件变化见正文`;
            cost.setAttribute('aria-label',`消耗${mana.cost}颗法珠`);
            if(mana.cost===0)cost.append(node('span','mana-zero','0珠'));
            else if(mana.cost<=5)for(let i=0;i<mana.cost;i++){const dot=node('i','mana-dot');dot.setAttribute('aria-hidden','true');cost.append(dot);}
            else cost.append(node('span','',`${mana.cost}珠`));
            skillHeading.append(cost);
          }
          skillEl.append(skillHeading);
          if (skill.levelStages) skillEl.append(node('p','level-guide',`数值顺序：${skill.levelStages.join(' / ')}（蓝色为原文明示数值）`));
          if (identity.note) skillEl.append(node('p', 'skill-origin-note', identity.note));
          if (skill.crossGroupNote) skillEl.append(node('p', 'skill-origin-note', skill.crossGroupNote));
          const conditions = list(skill.conditions).length ? skill.conditions : skill.conditionRowId ? [skill] : [];
          const conditionById = new Map(conditions.map(condition => [txt(condition.conditionRowId), condition]));
          // Preserve original sentence order, including trailing Chain clauses.
          visible.forEach(row => {
            const condition = conditionById.get(txt(row.id));
            skillEl.append(condition ? conditionContext(condition, row) : renderRow(row, filter));
          });
          if (skill.branchTable) {
            const guide=node('div','branch-guide');
            guide.append(node('p','muted','HP与Chain标签依据原始条件和原生选择逻辑；其余条件尚不能完整解释时保留字母。字母仅供本技能内对照，不代表强化顺序。紫色数值的具体缺口见正文提示。'));
            const conditionRows=list(skill.rows).filter(row=>/Chain|残りHP|ランダム|使用するたび|使用後|地形/.test(row.original || ''));
            if (conditionRows.length) guide.append(node('p','branch-context',conditionRows.map(row=>row.textZh || row.original).join(' ')));
            const rawKeys=[...new Set(skill.branchTable.flatMap(b=>Object.keys(b.raw || {})))].filter(key=>!/^skillid\d+$|^patternid$|^sname$|^stext$|^sinfo$|^voice$/.test(key));
            const varying=rawKeys.filter(key=>new Set(skill.branchTable.filter(b=>b.raw).map(b=>JSON.stringify(b.raw[key]) ?? 'missing')).size>1);
            skill.branchTable.forEach(branch=>{
              const entry=node('div','branch-guide-entry');
              entry.append(node('strong','',branch.conditionKnown ? branch.conditionLabel : branch.code),node('span','',branch.conditionKnown ? '' : `${branch.conditionLabel ? branch.conditionLabel+' · ' : ''}条件待确认`));
              const values=[...new Set(branch.values.map(v=>`${v.label}：${v.text}`))];
              entry.append(node('p','',values.join('；')));
              const evidence=node('div');
              evidence.append(node('p','muted',`来源：${branch.layer} / ${branch.id ?? '见逐句来源'}。以下为条件原始字段，不直接当作游戏中的档位或条件结论。`));
              if(branch.displayAliasOf)evidence.append(node('p','muted',`与 ${branch.displayAliasOf} 使用同一执行序列；按本父条件展示，不新增答案。执行槽：${JSON.stringify(branch.executionSlots)}`));
              if(branch.displayExclusionReason)evidence.append(node('p','muted',branch.displayExclusionReason));
              if (branch.raw) {
                evidence.append(node('p','',varying.length ? varying.map(key=>`${key}=${Object.hasOwn(branch.raw,key) ? JSON.stringify(branch.raw[key]) : '未记录'}`).join('；') : '已有条件字段没有差异；分支可能改变其他效果，不能据此判定是伤害强化。'));
                evidence.append(node('pre','source-json',JSON.stringify(branch.rawRecords.length>1 ? branch.rawRecords : branch.raw,null,2)));
              } else evidence.append(node('p','muted','此答案未附完整条件字段；沿用原句条件，不能补猜分支。'));
              entry.append(disclosure('条件记录',evidence));guide.append(entry);
            });
            const details=disclosure('分支对照',guide);details.id=skill.branchTable[0].tableId;skillEl.append(details);
          }
          section.append(skillEl);
        });
        heading.append(node('small', '', `${num(groupRows)} 条描述`));
        if (!groupRows) section.append(node('p', 'muted', '此分组没有符合筛选的描述。'));
        body.append(section);
      });
      if (!rows.length) body.append(node('div', 'empty', '这张卡尚无可展示的技能描述。'));
    }
    if (list(data.unmappedBranches).length) {
      const extra = node('div');
      list(data.unmappedBranches).forEach(branch=>{
        const entry = node('div','source-item');
        if (branch.reason) entry.append(node('p','branch-unmapped',branch.reason));
        entry.append(node('pre','source-json',JSON.stringify(branch,null,2))); extra.append(entry);
      });
      wrap.append(disclosure('其他分支参数 · 对应待核对',extra));
    }
    refresh(); main.replaceChildren(wrap); window.scrollTo(0, 0);
  }
  function loadDetail(cid) {
    if (details[cid]) return Promise.resolve();
    if (detailLoads.has(cid)) return detailLoads.get(cid);
    const promise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      let done = false;
      const finish = error => {
        if (done) return;
        done = true; window.clearTimeout(timeout); script.remove();
        if (window.CC_DETAILS !== details) Object.assign(details, window.CC_DETAILS || {});
        if (error || !details[cid]) reject(new Error('详情文件未能载入'));
        else resolve();
      };
      const timeout = window.setTimeout(() => finish(true), 20000);
      const file = catalog.meta?.detailMode === 'per-card' ? `data/cards/${encodeURIComponent(cid)}.js` : 'data/cards.js';
      script.src = `${file}?v=${encodeURIComponent(catalog.meta?.buildId || catalog.meta?.updated || '')}-${pageVersion}`;
      script.onload = () => finish(false); script.onerror = () => finish(true);
      document.head.append(script);
    });
    detailLoads.set(cid, promise);
    promise.catch(() => { if (detailLoads.get(cid) === promise) detailLoads.delete(cid); });
    return promise;
  }
  function detailStatus(cid, failed = false) {
    const wrap = node('section');
    const back = node('a', 'back', '← 返回角色目录'); back.href = state.catalogMode === 'index' ? '#all' : '#';
    const card = catalog.cards.find(c => String(c.cid) === cid);
    wrap.append(back, node('h1', '', cardName(card)));
    const status = node('div', 'empty'); status.setAttribute('role', 'status');
    status.append(node('p', '', failed ? '详情加载失败，请确认本地数据文件完整。' : '正在载入角色技能…'));
    if (failed) status.append(button('重新载入', route));
    wrap.append(status); main.replaceChildren(wrap); window.scrollTo(0, 0);
  }
  async function route() {
    const version = ++routeVersion;
    const params = new URLSearchParams(location.hash.slice(1)); const cid = params.get('card');
    if (params.has('all') && state.catalogMode !== 'index') { state.catalogMode = 'index'; catalogView = null; }
    if (!cid) { renderCatalog(); return; }
    if (!/^\d+$/.test(cid) || !catalog.cards.some(c => String(c.cid) === cid)) { renderDetail(cid); return; }
    if (activeCid !== cid) state.detailFilter = 'all';
    activeCid = cid;
    if (!details[cid]) {
      detailStatus(cid);
      try { await loadDetail(cid); }
      catch { if (version === routeVersion) detailStatus(cid, true); return; }
    }
    if (version === routeVersion) renderDetail(cid);
  }
  if (!catalog || !Array.isArray(catalog.cards)) { main.append(node('div', 'empty', '目录数据尚未生成。请检查本页 data 文件夹内的 catalog.js 和角色详情文件。')); return; }
  document.querySelector('footer').append(disclosure('数据来源与版本', node('pre', 'source-json', JSON.stringify(catalog.meta || {}, null, 2))));
  window.addEventListener('hashchange', route);
  route();
})();
