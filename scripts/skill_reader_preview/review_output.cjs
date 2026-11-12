'use strict';

const fs = require('node:fs');
const path = require('node:path');
const {writePath} = require('./project_layout_paths.cjs');

function freshReviewDirectory(label) {
    const parent = writePath(path.resolve(__dirname, '../../projects/reader/reports/review'));
    let existing = parent;
    while (!fs.existsSync(existing)) {
        existing = path.dirname(existing);
    }
    if (path.relative(existing, fs.realpathSync(existing)) !== '') {
        throw new Error('Review output must be a direct directory: ' + parent);
    }
    fs.mkdirSync(parent, {recursive: true});
    const stamp = new Date().toISOString().replace(/[-:.]/g, '');
    return fs.mkdtempSync(path.join(parent, label + '-' + stamp + '-'));
}

module.exports = {freshReviewDirectory};
