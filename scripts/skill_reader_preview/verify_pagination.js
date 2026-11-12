/* Run real reader handlers against a small DOM harness; no browser or build.
 * node scripts/skill_reader_preview/verify_pagination.js [path/to/app.js]
 * The 2,236 records below are test fixtures, not player data.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let focused = null;
const scripts = [];
class Element {
  constructor(tag) {
    this.tag = tag; this.children = []; this.listeners = {}; this.attrs = {};
    this.textContent = ''; this.disabled = false; this.hidden = false; this.value = '';
    this.classList = { add() {}, remove() {} };
  }
  append(...items) {
    this.children.push(...items);
    if (this.tag === 'head') items.filter(el => el.tag === 'script').forEach(el => scripts.push(el));
  }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.textContent = ''; this.children = items; }
  addEventListener(type, action) { (this.listeners[type] ||= []).push(action); }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  focus() { focused = this; }
  scrollIntoView() {}
  remove() {}
  setCustomValidity(message) { this.validityMessage = message; }
  reportValidity() { this.validityReported = true; }
}
const main = new Element('main'), footer = new Element('footer'), head = new Element('head');
const text = el => el.textContent + el.children.map(child => typeof child === 'object' ? text(child) : child).join('');
const all = (predicate, root = main) => [root, ...root.children.flatMap(child => typeof child === 'object' ? all(() => true, child) : [])].filter(predicate);
const one = (predicate, root = main) => {
  const result = all(predicate, root)[0]; assert(result, 'Expected a matching UI element'); return result;
};
const byClass = (name, root = main) => all(el => (el.className || '').split(' ').includes(name), root);
const byAria = name => one(el => el.attrs?.['aria-label'] === name);
const byButton = label => one(el => el.tag === 'button' && text(el) === label);
function fire(el, type, extra = {}) {
  if (type === 'click' && el.disabled) return;
  const event = { currentTarget: el, target: el, preventDefault() {}, ...extra };
  (el.listeners[type] || []).forEach(action => action(event));
}
const events = {};
const cards = Array.from({ length: 2236 }, (_, index) => ({
  cid: index + 1, name: `角色${index + 1}`, title: '测试称号', hasDetail: true,
  job: index % 2 ? '战士' : '法师', home: '测试所属', yg: index % 3 === 0,
  counts: { answer: index % 2, unresolved: 1, complete: 0, descriptions: 1 },
}));
const window = {
  CC_INLINE: require('./web/inline.js'), CC_LEVELS: require('./web/levels.js'), CC_BRANCHES: require('./web/branches.js'),
  CC_CATALOG: { meta: { detailMode: 'per-card' }, summary: { cards: 2236 }, cards },
  setTimeout, clearTimeout, scrollY: 0,
  scrollTo(x, y) { this.scrollY = y; },
  matchMedia: () => ({ matches: true }),
  addEventListener(type, action) { events[type] = action; },
};
const document = {
  head, createElement: tag => new Element(tag),
  createTextNode: content => ({ textContent: content, children: [] }),
  getElementById: id => id === 'main' ? main : all(el => el.id === id)[0],
  querySelector: () => footer,
};
let hashValue = '';
const location = { get hash() { return hashValue; }, set hash(value) { hashValue = value ? '#' + String(value).replace(/^#/, '') : ''; } };
const source = process.argv[2] || path.join(__dirname, 'web/app.js');
vm.runInNewContext(fs.readFileSync(source, 'utf8'), {
  window, document, location, URLSearchParams, Date, Promise, Map, Set, Number, String, Array, JSON,
  requestAnimationFrame: action => action(), CustomEvent: class {},
});
const summary = () => text(byClass('result-line')[0]);
const tiles = () => byClass('character');
const tileIds = () => tiles().map(tile => Number(text(byClass('card-name', tile)[0]).replace('角色', '')));
function jumpTo(page) {
  const input = byAria('目标页码'); input.value = String(page);
  fire(byAria('跳转页码'), 'submit');
}
function searchFor(value) {
  const input = byAria('搜索中文名、日文名或 CID'); input.value = value; fire(input, 'input');
}
function size(value) {
  const select = byAria('每页角色数量'); select.value = String(value); fire(select, 'change');
}

(async () => {
  assert.match(summary(), /第1\/38页 · 共2,236名角色/);
  assert.equal(tiles().length, 60);
  assert.equal(scripts.length, 0, 'Catalog must not load any detail scripts');
  assert.equal(byAria('上一页角色').disabled, true);
  fire(byAria('下一页角色'), 'click');
  assert.match(summary(), /第2\/38页/); assert.equal(tileIds()[0], 61);
  fire(byAria('第3页'), 'click');
  assert.match(summary(), /第3\/38页/); assert.equal(focused.attrs['aria-current'], 'page');
  jumpTo(9999);
  assert.match(summary(), /第3\/38页/); assert.equal(byAria('目标页码').validityReported, true);

  const reached = new Set();
  for (let page = 1; page <= 38; page++) { jumpTo(page); tileIds().forEach(cid => reached.add(cid)); }
  assert.equal(reached.size, 2236, 'Every catalog record must be reachable by explicit pagination');
  assert.equal(tiles().length, 16); assert.equal(byAria('下一页角色').disabled, true);
  fire(byAria('上一页角色'), 'click'); assert.match(summary(), /第37\/38页/);
  size(120); assert.match(summary(), /第1\/19页/); assert.equal(tiles().length, 120);
  size(30); assert.match(summary(), /第1\/75页/); assert.equal(tiles().length, 30);
  jumpTo(75); assert.equal(tiles().length, 16);
  searchFor('2236'); assert.match(summary(), /第1\/1页 · 共1名角色/); assert.deepEqual(tileIds(), [2236]);
  searchFor('不存在的角色'); assert.match(summary(), /第0\/0页 · 共0名角色/);
  assert.equal(byAria('角色目录分页').hidden, true);
  fire(byButton('清除搜索词'), 'click'); assert.match(summary(), /第1\/75页/);

  fire(byButton('全部角色索引'), 'click');
  assert.equal(byClass('index-entry').length, 2236);
  assert.match(summary(), /全部角色索引 · 共2,236名角色/);
  assert.equal(byAria('角色目录分页').hidden, true);
  assert.equal(scripts.length, 0, 'Full index must not load all details');
  fire(byButton('暂无答案'), 'click'); assert.equal(byClass('index-entry').length, 1118);
  searchFor('2236'); assert.equal(byClass('index-entry').length, 0, 'Index must honor combined filters');
  fire(byButton('全部'), 'click'); assert.equal(byClass('index-entry').length, 1);
  searchFor('角色'); fire(byButton('角色卡片'), 'click'); size(60); jumpTo(3);

  window.scrollY = 393;
  fire(tiles()[0], 'click'); assert.equal(location.hash, '#card=121');
  const opening = events.hashchange(); assert.equal(scripts.length, 1);
  assert.match(scripts[0].src, /^data\/cards\/121\.js\?/);
  window.CC_DETAILS['121'] = { cid: 121, groups: [] }; scripts[0].onload(); await opening;
  location.hash = ''; await events.hashchange();
  assert.match(summary(), /第3\/38页/); assert.equal(tileIds()[0], 121);
  assert.equal(byAria('搜索中文名、日文名或 CID').value, '角色');
  assert.equal(window.scrollY, 393, 'Returning from detail must restore directory position');

  fire(byButton('全部角色索引'), 'click');
  const entry = one(el => el.tag === 'button' && text(el).startsWith('121角色121'), byAria('全部角色索引'));
  fire(entry, 'click'); await events.hashchange();
  location.hash = ''; await events.hashchange();
  assert.match(summary(), /全部角色索引/); assert.equal(byClass('index-entry').length, 2236);
  fire(byButton('角色卡片'), 'click'); assert.match(summary(), /第3\/38页/);
  assert.equal(scripts.length, 1, 'Cached detail and index browsing must not load more cards');
  assert.equal(byAria('目标页码').type, 'number');
  assert.equal(byButton('跳转').type, 'submit');
  console.log('PASS: all 2236 cards reachable; page sizes/bounds/jump/empty filters; full filtered index; lazy details; page/query/mode/scroll restoration; native keyboard form controls.');
})().catch(error => { console.error(error); process.exitCode = 1; });
