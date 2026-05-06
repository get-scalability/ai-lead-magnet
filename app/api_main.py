from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import structlog

from app.agents.company_list.route import router as company_list_router
from app.core.logging import setup_logging


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger.info("api_startup")
    yield
    logger.info("api_shutdown")


app = FastAPI(
    title="AI Lead Magnet",
    description="Public-facing AI tools for getscalability.io",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to getscalability.io before production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app.include_router(company_list_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


_TEST_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Company List — Local Test</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0f0f0f;color:#e8e8e8;padding:40px 20px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:22px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{font-size:13px;color:#555;margin-bottom:32px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
label{display:block;font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px}
input,textarea{width:100%;background:#1a1a1a;border:1px solid #2e2e2e;border-radius:8px;color:#e8e8e8;font-size:14px;padding:10px 12px;outline:none}
input:focus,textarea:focus{border-color:#555}
.full{grid-column:1/-1}
textarea{resize:vertical;min-height:80px}
button{background:#fff;color:#000;border:none;border-radius:8px;font-size:14px;font-weight:600;padding:11px 28px;cursor:pointer;margin-top:4px}
button:disabled{background:#2a2a2a;color:#555;cursor:not-allowed}
#log{margin-top:28px;background:#141414;border:1px solid #1e1e1e;border-radius:10px;padding:18px 20px;min-height:80px;font-size:13px;line-height:1.8;font-family:monospace}
.s-msg{color:#aaa}
.s-det{color:#444;margin-left:18px;font-size:12px}
.s-err{color:#f87171}
.s-ok{color:#4ade80}
#results{display:none;margin-top:28px}
#results h2{font-size:15px;font-weight:600;color:#ccc;margin-bottom:14px}
.badge{font-size:11px;background:#1e1e1e;border:1px solid #333;border-radius:20px;padding:2px 10px;color:#666;margin-left:8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-size:11px;color:#444;text-transform:uppercase;letter-spacing:.05em;padding:8px 12px;border-bottom:1px solid #1e1e1e}
td{padding:10px 12px;border-bottom:1px solid #1a1a1a;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#161616}
.sc{display:inline-block;min-width:34px;text-align:center;border-radius:5px;font-size:12px;font-weight:700;padding:2px 6px}
.hi{background:#14532d;color:#4ade80}
.mid{background:#713f12;color:#fbbf24}
.lo{background:#1f2937;color:#9ca3af}
a{color:#60a5fa;text-decoration:none}
a:hover{text-decoration:underline}
.plink{margin-top:14px;font-size:12px;color:#444}
.plink a{color:#555}
</style>
</head>
<body>
<div class="wrap">
  <h1>Company List Agent</h1>
  <p class="sub">Local test — raw output, no UX polish</p>

  <div class="row">
    <div>
      <label>Your email</label>
      <input id="inp-email" type="email" value="yazid@getscalability.io">
    </div>
    <div>
      <label>Your company domain</label>
      <input id="inp-domain" type="text" value="getscalability.io">
    </div>
    <div class="full">
      <label>Target ICP description</label>
      <textarea id="inp-prompt">B2B SaaS companies in France, 50-500 employees, using outbound sales</textarea>
    </div>
  </div>

  <button id="btn" onclick="runAgent()">Run agent</button>

  <div id="log"><span style="color:#333">Output will appear here…</span></div>

  <div id="results">
    <h2>Results <span class="badge" id="cnt"></span></h2>
    <table>
      <thead><tr><th>ICP</th><th>Company</th><th>Domain</th><th>Industry</th><th>Size</th><th>Country</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="plink" id="plink"></div>
  </div>
</div>

<script>
function runAgent() {
  var email  = document.getElementById('inp-email').value.trim();
  var domain = document.getElementById('inp-domain').value.trim();
  var prompt = document.getElementById('inp-prompt').value.trim();
  if (!email || !domain || !prompt) { alert('Fill in all fields.'); return; }

  var btn = document.getElementById('btn');
  btn.disabled = true;
  btn.textContent = 'Running…';

  document.getElementById('log').innerHTML = '';
  document.getElementById('results').style.display = 'none';
  document.getElementById('tbody').innerHTML = '';
  document.getElementById('plink').innerHTML = '';

  fetch('/agents/company-list/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: email, domain: domain, icp_prompt: prompt})
  })
  .then(function(resp) {
    if (resp.status === 429) {
      addLog('Monthly limit reached. Try again next month.', '', true);
      btn.disabled = false; btn.textContent = 'Run agent'; return;
    }
    if (!resp.ok) {
      resp.text().then(function(t){ addLog('Server error ' + resp.status + ': ' + t, '', true); });
      btn.disabled = false; btn.textContent = 'Run agent'; return;
    }
    var reader = resp.body.getReader();
    var dec = new TextDecoder();
    var buf = '';
    var evType = '';

    function read() {
      reader.read().then(function(chunk) {
        if (chunk.done) { btn.disabled = false; btn.textContent = 'Run agent'; return; }
        buf += dec.decode(chunk.value, {stream: true});
        var lines = buf.split('\\n');
        buf = lines.pop();
        for (var i = 0; i < lines.length; i++) {
          var line = lines[i];
          if (line.indexOf('event: ') === 0) {
            evType = line.slice(7).trim();
          } else if (line.indexOf('data: ') === 0) {
            handleEvent(evType, line.slice(6).trim(), btn);
            evType = '';
          }
        }
        read();
      }).catch(function(e){ addLog('Stream error: ' + e.message, '', true); btn.disabled = false; btn.textContent = 'Run agent'; });
    }
    read();
  })
  .catch(function(e) {
    addLog('Request failed: ' + e.message, '', true);
    btn.disabled = false; btn.textContent = 'Run agent';
  });
}

function handleEvent(type, raw, btn) {
  var d;
  try { d = JSON.parse(raw); } catch(e) { return; }
  if (type === 'status') {
    addLog(d.message || '', d.detail || '', false);
  } else if (type === 'error') {
    addLog(d.message || 'Error', d.hint || '', true);
    btn.disabled = false; btn.textContent = 'Run agent';
  } else if (type === 'result') {
    renderTable(d.companies, d.total_found);
  } else if (type === 'done') {
    addLog('Done!', '', false, true);
    if (d.public_id) {
      var url = '/agents/company-list/result/' + d.public_id;
      document.getElementById('plink').innerHTML = 'Permalink: <a href="' + url + '" target="_blank">' + url + '</a>';
    }
    btn.disabled = false; btn.textContent = 'Run agent';
  }
}

function addLog(msg, detail, isErr, isOk) {
  var log = document.getElementById('log');
  var first = log.querySelector('span[style]');
  if (first) first.remove();
  var d = document.createElement('div');
  d.className = isErr ? 's-err' : (isOk ? 's-ok' : 's-msg');
  d.textContent = msg;
  log.appendChild(d);
  if (detail) {
    var dd = document.createElement('div');
    dd.className = 's-det';
    dd.textContent = detail;
    log.appendChild(dd);
  }
}

function renderTable(companies, total) {
  document.getElementById('cnt').textContent = total + ' companies';
  var tb = document.getElementById('tbody');
  for (var i = 0; i < companies.length; i++) {
    var c = companies[i];
    var cls = c.icp_score >= 70 ? 'hi' : (c.icp_score >= 40 ? 'mid' : 'lo');
    var name = c.linkedin_url
      ? '<a href="' + c.linkedin_url + '" target="_blank">' + esc(c.name) + '</a>'
      : esc(c.name);
    var dom = c.domain
      ? '<a href="https://' + esc(c.domain) + '" target="_blank">' + esc(c.domain) + '</a>'
      : '';
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td><span class="sc ' + cls + '">' + c.icp_score + '</span></td>' +
      '<td>' + name + '</td>' +
      '<td>' + dom + '</td>' +
      '<td>' + esc(c.industry) + '</td>' +
      '<td>' + esc(c.size) + '</td>' +
      '<td>' + esc(c.country) + '</td>';
    tb.appendChild(tr);
  }
  document.getElementById('results').style.display = 'block';
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
</body>
</html>
"""


@app.get("/test", response_class=HTMLResponse)
async def test_ui() -> str:
    return _TEST_HTML
