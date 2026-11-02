// Runs site_tab/js/elnino-model.js on the published bundle for each case tests/test_site_model.py
// writes, and prints how far each case's statistics land from the run's own (JSON on stdout).
const fs = require('fs');
const path = require('path');
const M = require('../site_tab/js/elnino-model.js');

const base = path.join(__dirname, '..', 'site_tab', 'data', 'elnino');
const io = {
  json: f => Promise.resolve(JSON.parse(fs.readFileSync(f, 'utf8'))),
  bin: f => { const b = fs.readFileSync(f); return Promise.resolve(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); },
};
const refDir = process.argv[2];
const readF64 = f => { const b = fs.readFileSync(path.join(refDir, f)); return new Float64Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); };

(async () => {
  const model = await M.load(base, io);
  const cases = JSON.parse(fs.readFileSync(path.join(refDir, 'cases.json'), 'utf8'));
  const out = {};
  for (const c of cases) {
    const S = Object.assign({}, model.meta.defaults, c.settings);
    await model.ensure(S);
    const t = Date.now();
    const r = model.run(S);
    const ms = Date.now() - t;
    const diff = (a, b) => { let m = 0; for (let i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i] - b[i])); return m; };
    const y = r.youden(c.E);
    out[c.name] = {
      maxdiff0: diff(r.m(0, c.E), readF64(c.name + '_m0.bin')),
      maxdiff1: diff(r.m(1, c.E), readF64(c.name + '_m1.bin')),
      youden: { threshold: y.threshold, sensitivity: y.sensitivity, falsePositive: y.falsePositive, growth: y.growth },
      pYes0: r.pYes(0, c.E, model.meta.defaults.strike), pYes1: r.pYes(1, c.E, model.meta.defaults.strike),
      ms,
    };
  }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
