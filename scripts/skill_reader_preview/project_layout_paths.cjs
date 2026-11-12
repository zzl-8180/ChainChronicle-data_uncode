'use strict';
/* Explicit SHA-pinned data paths for candidate Node audits. No I/O on import without activation. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const SOURCE_ROOT = path.resolve(__dirname, '../..');
const CONFIG_ENV = 'CC_PROJECT_LAYOUT_CONFIG';
const SHA_ENV = 'CC_PROJECT_LAYOUT_SHA256';
const SELECTOR = path.join(SOURCE_ROOT, 'scripts/project_layout_active.json');
const initialName = process.env[CONFIG_ENV];
const initialSha = process.env[SHA_ENV];
if ((initialName === undefined) !== (initialSha === undefined) ||
    (initialName !== undefined && (!initialName || !initialSha)))
  throw new Error('Layout configuration and SHA must both be explicit');
if (initialName && !path.isAbsolute(initialName)) throw new Error('Layout config must be absolute');
const expectedSha = initialSha && initialSha.toLowerCase();
if (expectedSha && !/^[0-9a-f]{64}$/.test(expectedSha)) throw new Error('Invalid layout SHA-256');

function sameEnv() {
  if (process.env[CONFIG_ENV] !== initialName || process.env[SHA_ENV] !== initialSha)
    throw new Error('Layout activation cannot change within a Node process');
}
function inside(target, parent) {
  const rel = path.relative(parent, target);
  return rel === '' || (rel !== '..' && !rel.startsWith('..' + path.sep) && !path.isAbsolute(rel));
}
function ordinaryAncestors(target) {
  let current = path.resolve(target);
  for (;;) {
    try {
      if (fs.lstatSync(current).isSymbolicLink()) throw new Error('Reparse in strict path: ' + current);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
}
function physical(value, repo) {
  if (typeof value !== 'string' || !value || value.includes('\0')) throw new Error('Invalid physical path');
  if (value.split(/[\\/]/).includes('..')) throw new Error('Parent traversal in configured path');
  if (/^[A-Za-z]:(?:$|[^\\/])/.test(value)) throw new Error('Drive-relative physical path');
  return path.resolve(path.isAbsolute(value) ? value : path.join(repo, value));
}
function table(value, repo) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Root table must be an object');
  const rows = [], seen = new Set();
  for (const [name, destination] of Object.entries(value)) {
    const parts = name.replace(/\\/g, '/').replace(/\/$/, '').split('/');
    if (!parts.length || parts.some(p => !p || p === '.' || p === '..') || name.startsWith('/') || name.includes(':'))
      throw new Error('Unsafe logical root');
    const key = parts.map(p => p.toLowerCase()).join('/');
    if (seen.has(key)) throw new Error('Duplicate logical root');
    seen.add(key);
    rows.push({ parts, folded: parts.map(p => p.toLowerCase()), destination: physical(destination, repo) });
  }
  return rows.sort((a, b) => b.parts.length - a.parts.length);
}
function parseConfig(raw) {
  let cfg;
  try { cfg = JSON.parse(raw.toString('utf8')); } catch (error) { throw new Error('Invalid layout JSON: ' + error.message); }
  if (!cfg || Array.isArray(cfg) || cfg.schema_version !== 1) throw new Error('Unsupported layout schema');
  const allowed = new Set(['schema_version','repository_root','read_roots','write_roots','strict_write_roots',
    'legacy_repository_roots','deny_unmapped_output_writes','description','mode']);
  if (Object.keys(cfg).some(k => !allowed.has(k))) throw new Error('Unknown layout config field');
  if (typeof cfg.repository_root !== 'string' || !cfg.repository_root || cfg.repository_root.split(/[\\/]/).includes('..') ||
      cfg.read_roots === undefined || cfg.write_roots === undefined) throw new Error('Missing layout fields');
  if (/^[A-Za-z]:(?:$|[^\\/])/.test(cfg.repository_root)) throw new Error('Drive-relative repository root');
  const repo = path.resolve(path.isAbsolute(cfg.repository_root) ? cfg.repository_root : path.join(SOURCE_ROOT,cfg.repository_root));
  const strict = (cfg.strict_write_roots || []).map(p => physical(p, repo));
  const legacy = (cfg.legacy_repository_roots || []).map(p => physical(p, repo));
  if (!Array.isArray(cfg.strict_write_roots || []) || !Array.isArray(cfg.legacy_repository_roots || []))
    throw new Error('Root allowlists must be arrays');
  if (cfg.deny_unmapped_output_writes !== undefined && typeof cfg.deny_unmapped_output_writes !== 'boolean')
    throw new Error('deny_unmapped_output_writes must be boolean');
  for (const root of strict) ordinaryAncestors(root);
  return { repo, reads: table(cfg.read_roots, repo), writes: table(cfg.write_roots, repo), strict, legacy,
    deny: cfg.deny_unmapped_output_writes || false };
}
let pinnedConfig = null;
let pinnedRaw = null;
let activationKey = null;
function active() {
  sameEnv();
  let configName = initialName, configSha = expectedSha;
  if (!configName) {
    ordinaryAncestors(path.dirname(SELECTOR));
    let selector;
    try { selector = fs.lstatSync(SELECTOR); }
    catch (error) {
      if (error.code !== 'ENOENT') throw error;
      if (activationKey && activationKey !== 'legacy') throw new Error('Layout activation removed within a Node process');
      activationKey = 'legacy';
      return null;
    }
    if (!selector.isFile() || selector.isSymbolicLink()) throw new Error('Active layout locator must be ordinary');
    const selected = JSON.parse(fs.readFileSync(SELECTOR, 'utf8'));
    if (!selected || Array.isArray(selected) || Object.keys(selected).sort().join(',') !==
        'configuration,schema_version,sha256' || selected.schema_version !== 1 ||
        typeof selected.configuration !== 'string' || typeof selected.sha256 !== 'string')
      throw new Error('Invalid active layout locator');
    configName = physical(selected.configuration, SOURCE_ROOT);
    configSha = selected.sha256.toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(configSha)) throw new Error('Invalid active layout SHA');
  }
  const key = configName + '|' + configSha;
  if (activationKey && activationKey !== key) throw new Error('Layout activation changed within a Node process');
  activationKey = key;
  const raw = fs.readFileSync(configName);
  if (crypto.createHash('sha256').update(raw).digest('hex') !== configSha) throw new Error('Layout SHA mismatch');
  if (!pinnedRaw || !raw.equals(pinnedRaw)) {
    pinnedConfig = parseConfig(raw);
    pinnedRaw = raw;
  }
  return pinnedConfig;
}
function relative(value, namespaces) {
  if (typeof value !== 'string' || value.includes('\0')) throw new Error('Invalid data path');
  const parts = value.replace(/\\/g, '/').split('/');
  if (parts.includes('..')) throw new Error('Parent traversal in logical path');
  if (!path.isAbsolute(value)) {
    if (/^[A-Za-z]:/.test(value)) throw new Error('Drive-relative data path');
    return { logical: value };
  }
  const absolute = path.resolve(value);
  for (const root of namespaces.sort((a, b) => b.length - a.length))
    if (inside(absolute, root)) return { logical: path.relative(root, absolute) };
  return { external: absolute };
}
function strictWrite(target, roots) {
  if (!roots.length) return;
  for (const root of roots) ordinaryAncestors(root);
  ordinaryAncestors(target);
  const canonical = value => {
    let existing = value;
    while (!fs.existsSync(existing)) {
      const parent = path.dirname(existing);
      if (parent === existing) break;
      existing = parent;
    }
    return path.join(fs.realpathSync.native(existing), path.relative(existing, value));
  };
  const effective = canonical(target);
  if (!roots.some(root => inside(effective, canonical(root))))
    throw new Error('Write outside declared roots: ' + target);
}
function resolveData(value, access, root) {
  const cfg = active();
  if (!cfg) return value;
  const namespace = root ? path.resolve(root) : SOURCE_ROOT;
  const extracted = relative(value, [namespace, SOURCE_ROOT, cfg.repo, ...cfg.legacy]);
  let result, mapped = false;
  if (extracted.external) result = extracted.external;
  else {
    const parts = extracted.logical.split(/[\\/]/).filter(Boolean);
    if (parts[0]?.toLowerCase() === 'scripts') throw new Error('Source code is not a data path');
    const folded = parts.map(p => p.toLowerCase());
    const roots = access === 'read' ? cfg.reads : cfg.writes;
    const match = roots.find(row => row.folded.every((part, index) => folded[index] === part));
    result = match ? path.join(match.destination, ...parts.slice(match.parts.length)) : path.join(cfg.repo, ...parts);
    mapped = !!match;
    if (access === 'write' && cfg.deny && !mapped && folded[0] === 'output')
      throw new Error('Unmapped output write denied');
  }
  if (access === 'write') strictWrite(result, cfg.strict);
  return result;
}
module.exports = { readPath: (value, root) => resolveData(value, 'read', root),
  writePath: (value, root) => resolveData(value, 'write', root), SOURCE_ROOT };
