# Stage 1 Template Card + Narrow Disambiguation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a decks-only template selection card to Confirm UI Stage 1 (with deferred Step 3 install on confirm) plus a narrow one-shot disambiguation question for pathless template intent, per `docs/superpowers/specs/2026-07-16-stage1-template-field-design.md`.

**Architecture:** The confirm server builds a `templates` catalog live from `decks_index.json` (mirroring the existing canvas↔`config.py` sync), serves token-substituted cover-shell SVG previews, and tells the front-end whether the card is an active selector or a locked info display. The front-end renders the card in Stage 1 and writes `template` into `result.json`; the AI then runs the normal Step 3 install *after* Stage 1 when a deck was picked. Four prompt docs (SKILL.md, strategist.md, confirm_ui.md, routing.md) encode the trigger-rule and orchestration changes.

**Tech Stack:** Python 3 + Flask (server), vanilla ES5 JS (front-end), Markdown prompt docs.

## Global Constraints

- **No automated tests** — no `tests/`, no `test_*.py`, no pytest (docs/rules/code-style.md §11). Verify with inline `python3 -c` smoke commands and a gitignored `projects/_smoke_stage1_template/` project.
- Python style: docs/rules/code-style.md (UTF-8, LF, 4-space indent, `_snake_case` private helpers, named exceptions only, no bare `except:`).
- Prompt docs under `.claude/skills/ppt-master/` are **English** scaffolding (CLAUDE.md language rule).
- catalogs.json / app.js user-facing labels need **all four languages** (zh / en / ja / ko).
- Confirm UI stays **px-only**; the **stage progression guard is unchanged**; **no new always-on blocking gate** (the disambiguation question fires only on the user's own ambiguous request).
- Commit directly to `main`, one commit per task, message ends with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. List changed files in the body (upstream-resync conflict aid).
- `python3` may need to be `python` on this Windows machine (SKILL.md Windows note).
- SKILL.md frontmatter must NOT change (no `.codex/skills/` stub resync needed).

---

### Task 1: Server — `templates` catalog key (live deck sync)

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/static/catalogs.json` (add static `templates` key with the `free` entry)
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/server.py` (module constants near line 84; `_build_catalogs()` near line 659)

**Interfaces:**
- Produces: `/api/catalogs` response gains `"templates": [{id:"free",label_*,desc_*}, {id:"<deck_id>", label, desc, canvas_format, page_count, primary_color}, ...]`. Task 4's front-end reads `CAT.templates`; Task 2 reuses `_read_decks_index()`.

- [ ] **Step 1: Add the static `free` entry to catalogs.json**

In `.claude/skills/ppt-master/scripts/confirm_ui/static/catalogs.json`, add a top-level `templates` key (after `"template_adherence"`, before `"delivery_purpose"`):

```json
  "templates": [
    {
      "id": "free",
      "label": "Free design",
      "label_zh": "自由设计",
      "label_en": "Free design",
      "label_ja": "自由デザイン",
      "label_ko": "자유 디자인",
      "desc_zh": "不使用预置模板，按确认的风格从零设计整套页面。",
      "desc_en": "No preset template — every page is designed fresh from the confirmed style.",
      "desc_ja": "プリセットテンプレートを使わず、確認済みスタイルで全ページを新規デザインします。",
      "desc_ko": "프리셋 템플릿 없이 확정된 스타일로 전 페이지를 새로 디자인합니다."
    }
  ],
```

- [ ] **Step 2: Add deck-index constants and reader to server.py**

Below `_CATALOGS_PATH` / `_ICON_LIBRARY_DIR` (near line 84):

```python
_DECKS_DIR = Path(__file__).resolve().parents[2] / 'templates' / 'decks'
_DECKS_INDEX_PATH = _DECKS_DIR / 'decks_index.json'
```

New module-level helper (place right above `_build_catalogs`):

```python
def _read_decks_index() -> dict:
    """Read the deck library index; {} when missing/invalid (catalog degrades)."""
    try:
        data = json.loads(_DECKS_INDEX_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _template_catalog_entries() -> list[dict]:
    """Deck entries for the Stage-1 template card, synced live from
    ``decks_index.json`` — the single source of truth for the deck library —
    so the card can never drift from the installed decks. The ``free`` entry
    and its four-language labels stay in catalogs.json."""
    entries = []
    index = _read_decks_index()
    for deck_id in sorted(index):
        info = index[deck_id] if isinstance(index[deck_id], dict) else {}
        entries.append({
            'id': deck_id,
            'label': deck_id,
            'desc': info.get('summary', ''),
            'canvas_format': info.get('canvas_format', ''),
            'page_count': info.get('page_count'),
            'primary_color': info.get('primary_color', ''),
        })
    return entries
```

- [ ] **Step 3: Merge deck entries in `_build_catalogs()`**

`_build_catalogs()` currently returns early when `import config` fails — the templates merge must happen on both paths. Change the top of the function:

```python
def _build_catalogs() -> dict:
    """Return the static catalog set with the canvas list synced live from
    ``config.CANVAS_FORMATS`` — the single source of truth for canvas formats —
    so the confirm page can never drift from the pipeline's real formats. The
    set of formats and their dimensions come from config; trilingual labels and
    use text are kept from catalogs.json (with a plain fallback for any new id).
    The ``templates`` list is likewise synced from ``decks_index.json``: the
    static ``free`` entry keeps its catalogs.json labels, deck entries are live.
    """
    data = json.loads(_CATALOGS_PATH.read_text(encoding='utf-8'))
    static_templates = [
        t for t in data.get('templates', [])
        if isinstance(t, dict) and t.get('id') == 'free'
    ]
    data['templates'] = static_templates + _template_catalog_entries()
    try:
        import config  # scripts/ is on sys.path (injected at import time)
        formats = config.CANVAS_FORMATS
    except (ImportError, AttributeError):  # missing module/attr → static canvas
        return data
```

(The rest of the canvas sync body is unchanged.)

- [ ] **Step 4: Smoke-verify the catalog**

```bash
python3 -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.claude/skills/ppt-master/scripts')
from confirm_ui.server import _build_catalogs
t = _build_catalogs()['templates']
print([e['id'] for e in t])
assert t[0]['id'] == 'free' and t[0]['label_ko'] == '자유 디자인'
assert {'apple', 'jangpm', 'mckinsey'} <= {e['id'] for e in t}
assert all(e.get('desc') for e in t if e['id'] != 'free')
print('OK')
"
```

Expected: `['free', 'apple', 'jangpm', 'mckinsey']` then `OK`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/scripts/confirm_ui/server.py .claude/skills/ppt-master/scripts/confirm_ui/static/catalogs.json
git commit -m "confirm-ui: sync templates catalog live from decks_index.json"
```

---

### Task 2: Server — `/api/template_preview/<deck_id>` endpoint

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/server.py` (module helpers + new route inside `create_app`, beside `/api/icon-previews` near line 856)

**Interfaces:**
- Consumes: `_read_decks_index()`, `_DECKS_DIR` from Task 1.
- Produces: `GET /api/template_preview/<deck_id>?lang=<zh|en|ja|ko>` → `image/svg+xml`, no-store; 404 on unknown deck / missing shells. Task 4 loads it via `<img src>`.

- [ ] **Step 1: Add token sample text + substitution helpers (module level, below `_template_catalog_entries`)**

```python
# Role sample text substituted into {{TOKEN}} slots when serving a deck cover
# shell as a card preview. Fixed role copy, not project content — the same
# principle as the visual_style previews (users compare visual treatment).
_TEMPLATE_PREVIEW_TEXT = {
    'zh': {'title': '演示文稿标题', 'subtitle': '副标题示例文字', 'date': '2026. 07', 'name': '演示者', 'generic': '示例文本'},
    'en': {'title': 'Presentation Title', 'subtitle': 'Sample subtitle line', 'date': '2026. 07', 'name': 'Presenter', 'generic': 'Sample text'},
    'ja': {'title': 'プレゼンテーションのタイトル', 'subtitle': 'サブタイトルの例', 'date': '2026. 07', 'name': '発表者', 'generic': 'サンプルテキスト'},
    'ko': {'title': '프레젠테이션 제목', 'subtitle': '부제 예시 한 줄', 'date': '2026. 07', 'name': '발표자', 'generic': '샘플 텍스트'},
}
_TEMPLATE_TOKEN_RE = re.compile(r'\{\{([A-Za-z0-9_]+)\}\}')


def _preview_token_text(token: str, texts: dict) -> str:
    """Map a shell {{TOKEN}} name to role sample copy by keyword."""
    name = token.upper()
    if 'SUBTITLE' in name:
        return texts['subtitle']
    if 'TITLE' in name:
        return texts['title']
    if 'DATE' in name:
        return texts['date']
    if 'PRESENTER' in name or 'AUTHOR' in name or 'ORGANIZATION' in name:
        return texts['name']
    return texts['generic']


def _render_template_preview(deck_id: str, lang: str) -> Optional[str]:
    """Serve a deck's first roster shell with tokens substituted, or None."""
    if deck_id not in _read_decks_index():
        return None
    shells = sorted((_DECKS_DIR / deck_id / 'templates').glob('*.svg'))
    if not shells:
        return None
    texts = _TEMPLATE_PREVIEW_TEXT.get(lang, _TEMPLATE_PREVIEW_TEXT['en'])
    raw = shells[0].read_text(encoding='utf-8')
    return _TEMPLATE_TOKEN_RE.sub(lambda m: _preview_token_text(m.group(1), texts), raw)
```

- [ ] **Step 2: Add the route inside `create_app` (after the `/api/icon-previews` route)**

```python
    @app.route('/api/template_preview/<deck_id>')
    def get_template_preview(deck_id: str):
        """Serve a token-substituted deck cover shell for the Stage-1 card.

        deck_id is validated against the decks index (the Flask converter
        already rejects path separators), so no path traversal is possible.
        """
        lang = request.args.get('lang') or 'en'
        svg = _render_template_preview(deck_id, lang)
        if svg is None:
            return jsonify({'error': 'unknown deck or empty roster'}), 404
        resp = app.response_class(svg, mimetype='image/svg+xml')
        resp.headers['Cache-Control'] = 'no-store'
        return resp
```

- [ ] **Step 3: Create the smoke project and verify the endpoint**

Create `projects/_smoke_stage1_template/confirm_ui/recommendations.json` (projects/ is git-ignored):

```json
{
  "stage": "stage1",
  "lang": "ko",
  "recommend": {
    "canvas": "ppt169",
    "mode": "briefing",
    "visual_style": "swiss-minimal",
    "delivery_purpose": "balanced",
    "template": "free"
  },
  "audience": { "value": "smoke check" },
  "content_divergence": { "value": "" },
  "visual_style_spectrum": [
    { "id": "swiss-minimal", "tag_ko": "안전", "note_ko": "표준 비즈니스", "tag_en": "Safe", "note_en": "standard business" },
    { "id": "editorial", "tag_ko": "변주", "note_ko": "편집 디자인풍", "tag_en": "Shifted", "note_en": "editorial feel" },
    { "id": "brutalist", "tag_ko": "대담", "note_ko": "선언문풍", "tag_en": "Bold", "note_en": "manifesto" }
  ]
}
```

Then:

```bash
python3 -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.claude/skills/ppt-master/scripts')
from confirm_ui.server import create_app
c = create_app('projects/_smoke_stage1_template').test_client()
r = c.get('/api/template_preview/apple?lang=ko')
body = r.get_data(as_text=True)
print(r.status_code, r.mimetype)
assert r.status_code == 200 and r.mimetype == 'image/svg+xml'
assert '{{' not in body and '프레젠테이션 제목' in body
assert c.get('/api/template_preview/nope').status_code == 404
print('OK')
"
```

Expected: `200 image/svg+xml` then `OK`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/scripts/confirm_ui/server.py
git commit -m "confirm-ui: add /api/template_preview deck cover shell endpoint"
```

---

### Task 3: Server — `_template_field` state + result fold-back

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/server.py` (`_ANCHOR_RECOMMEND_KEYS` near line 512; new helper beside `_template_adherence_enabled` near line 523; `/api/recommendations` route near line 900)

**Interfaces:**
- Produces: `/api/recommendations` response gains `_template_field`: `{"mode": "selector"}` when no template is installed, or `{"mode": "locked", "kind": "<brand|layout|deck>", "name": "<display>"}` when `<project>/templates/design_spec.md` exists. `result.json.template` folds back into `recommend.template` on later stages. Task 4 reads `REC._template_field`.

- [ ] **Step 1: Add `'template'` to the fold-back keys**

```python
_ANCHOR_RECOMMEND_KEYS = (
    'canvas',
    'mode',
    'visual_style',
    'delivery_purpose',
    'template',
    'template_adherence',
)
```

- [ ] **Step 2: Add the installed-template inspector (below `_template_adherence_enabled`)**

```python
def _installed_template_info(project_path: Path) -> Optional[dict]:
    """Describe the Step 3-installed template, or None when free design.

    Installed copies carry no library id, so the display name is the spec's
    first H1 (falling back to the kind). Drives the Stage-1 card's locked
    (informational) state — an installed template cannot be changed from the
    page.
    """
    spec_path = project_path / 'templates' / 'design_spec.md'
    try:
        lines = spec_path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != '---':
        return None
    kind = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == '---':
            break
        match = re.fullmatch(r'kind\s*:\s*["\']?(brand|layout|deck)["\']?', stripped)
        if match:
            kind = match.group(1)
            break
    if kind is None:
        return None
    name = kind
    for line in lines:
        if line.startswith('# '):
            name = line[2:].strip() or kind
            break
    return {'kind': kind, 'name': name}
```

- [ ] **Step 3: Inject `_template_field` in `/api/recommendations`**

Right after the existing `data['_template_adherence_enabled'] = template_adherence_enabled` block (keep that block unchanged), add:

```python
        installed = _installed_template_info(project_path)
        data['_template_field'] = (
            {'mode': 'locked', 'kind': installed['kind'], 'name': installed['name']}
            if installed else {'mode': 'selector'}
        )
```

- [ ] **Step 4: Smoke-verify both modes**

```bash
python3 -c "
import sys, pathlib; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.claude/skills/ppt-master/scripts')
from confirm_ui.server import create_app
proj = pathlib.Path('projects/_smoke_stage1_template')
c = create_app(str(proj)).test_client()
rec = c.get('/api/recommendations').get_json()
assert rec['_template_field'] == {'mode': 'selector'}, rec['_template_field']
spec = proj / 'templates' / 'design_spec.md'
spec.parent.mkdir(parents=True, exist_ok=True)
spec.write_text('---\nkind: deck\n---\n\n# Smoke Deck\n', encoding='utf-8')
rec = c.get('/api/recommendations').get_json()
assert rec['_template_field'] == {'mode': 'locked', 'kind': 'deck', 'name': 'Smoke Deck'}
assert rec['_template_adherence_enabled'] is True
spec.unlink(); spec.parent.rmdir()
print('OK')
"
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/scripts/confirm_ui/server.py
git commit -m "confirm-ui: expose stage1 template field state (selector/locked)"
```

---

### Task 4: Front-end — Stage 1 template card

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/static/app.js` (LABELS ×4 dicts near lines 29/141/253/365; new renderer near `renderStyle` line 1180; `renderForStage` line 2155; `initStage1State` line 2214; `stage1Payload` line 2292; `stage2Payload` line 2307)
- Modify: `.claude/skills/ppt-master/scripts/confirm_ui/static/style.css` (append card styles)

**Interfaces:**
- Consumes: `CAT.templates` (Task 1), `/api/template_preview` (Task 2), `REC._template_field` (Task 3), existing helpers `el` / `section` / `enumField` / `recOrFirst` / `optionLabel` / `optionDesc` / `hasTemplateAdherence` / `renderAll`.
- Produces: `result.json` stage1/stage2/final payloads carry `template: "<deck_id>"|"free"|"<installed name>"`; `template_adherence` present only when a deck is active.

- [ ] **Step 1: Add the four language labels**

In each of the four LABELS dicts (`en` ~line 29, `ja` ~line 141, `ko` ~line 253, `zh` ~line 365), next to the existing `sec_style` key, add two keys:

```javascript
            sec_template: "Template",
            template_locked_note: "Installed at Step 3 — shown for reference; not changeable here",
```
```javascript
            sec_template: "テンプレート",
            template_locked_note: "Step 3でインストール済み — 参考表示のためここでは変更できません",
```
```javascript
            sec_template: "템플릿",
            template_locked_note: "Step 3에서 설치됨 — 참고용 표시이며 여기서 변경할 수 없습니다",
```
```javascript
            sec_template: "模板",
            template_locked_note: "已在 Step 3 安装 — 仅供参考，此处不可更改",
```

- [ ] **Step 2: Add the template card renderer (insert directly above `renderStyle`, ~line 1180)**

```javascript
    // ---- Stage-1 template card (decks-only selector / locked info) --------
    function templateFieldState() {
        return (REC && REC._template_field) || { mode: "selector" };
    }

    function templateCatalog() {
        return (CAT && CAT.templates) || [];
    }

    function freeDesignPreview() {
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">' +
            '<rect width="1280" height="720" fill="#FFFFFF"/>' +
            '<rect x="96" y="96" width="1088" height="528" rx="24" fill="none" stroke="#CBD5E1" stroke-width="4" stroke-dasharray="18 14"/>' +
            '<rect x="180" y="200" width="420" height="40" rx="20" fill="#E2E8F0"/>' +
            '<rect x="180" y="290" width="620" height="22" rx="11" fill="#EEF2F7"/>' +
            '<rect x="180" y="336" width="540" height="22" rx="11" fill="#EEF2F7"/>' +
            '<circle cx="1000" cy="420" r="90" fill="#F1F5F9"/>' +
            '</svg>';
    }

    function templatePreviewNode(entry) {
        var node = el("div", "option-preview option-preview-template");
        node.setAttribute("aria-hidden", "true");
        if (!entry || entry.id === "free") {
            node.innerHTML = freeDesignPreview();
            return node;
        }
        var img = document.createElement("img");
        img.alt = "";
        img.loading = "lazy";
        img.src = "/api/template_preview/" + encodeURIComponent(entry.id) +
            "?lang=" + encodeURIComponent(LANG);
        img.onerror = function () { node.innerHTML = freeDesignPreview(); };
        node.appendChild(img);
        return node;
    }

    function adherenceVisible() {
        if (templateFieldState().mode === "locked") return hasTemplateAdherence();
        return !!(STATE.template && STATE.template !== "free");
    }

    function setTemplateSelection(id) {
        STATE.template = id;
        if (id && id !== "free") {
            if (!STATE.template_adherence) {
                STATE.template_adherence = recOrFirst("template_adherence", CAT.template_adherence);
            }
        } else {
            delete STATE.template_adherence;
        }
        renderAll();
    }

    function renderTemplate(host) {
        var field = templateFieldState();
        var sec = section(0, "sec_template");
        if (field.mode === "locked") {
            var lockedCard = el("div", "template-card template-card-locked selected");
            var lockedCopy = el("div", "template-card-copy");
            lockedCopy.appendChild(el("div", "template-card-name", field.name || field.kind || ""));
            lockedCopy.appendChild(el("div", "template-card-desc", t("template_locked_note")));
            lockedCard.appendChild(lockedCopy);
            sec.appendChild(lockedCard);
        } else {
            var row = el("div", "template-cards");
            var recommended = recOrFirst("template", templateCatalog());
            templateCatalog().forEach(function (entry) {
                var card = el("div", "template-card");
                card.appendChild(templatePreviewNode(entry));
                var copy = el("div", "template-card-copy");
                var nameRow = el("div", "template-card-name", optionLabel(entry));
                if (entry.primary_color) {
                    var dot = el("span", "template-color-dot");
                    dot.style.background = entry.primary_color;
                    nameRow.appendChild(dot);
                }
                copy.appendChild(nameRow);
                var meta = [];
                if (entry.canvas_format) meta.push(entry.canvas_format);
                if (entry.page_count) meta.push(entry.page_count + "p");
                if (meta.length) copy.appendChild(el("div", "template-card-meta", meta.join(" · ")));
                var desc = optionDesc(entry);
                if (desc) copy.appendChild(el("div", "template-card-desc", desc));
                if (entry.id === recommended) {
                    card.classList.add("recommended");
                    copy.appendChild(el("span", "rec-badge", "★ " + t("recommended")));
                }
                card.appendChild(copy);
                if ((STATE.template || "free") === entry.id) card.classList.add("selected");
                card.addEventListener("click", function () { setTemplateSelection(entry.id); });
                row.appendChild(card);
            });
            sec.appendChild(row);
        }
        if (adherenceVisible()) {
            var adherenceField = el("div", "subfield");
            adherenceField.appendChild(el("div", "subfield-label", t("sub_template_adherence")));
            enumField(adherenceField, CAT.template_adherence,
                recOrFirst("template_adherence", CAT.template_adherence),
                function () { return STATE.template_adherence; },
                function (v) { STATE.template_adherence = v; });
            sec.appendChild(adherenceField);
        }
        host.appendChild(sec);
    }
```

- [ ] **Step 3: Move the adherence subfield out of `renderStyle`**

In `renderStyle` (~line 1191), delete this block (it now lives in `renderTemplate`):

```javascript
        if (hasTemplateAdherence()) {
            var templateField = el("div", "subfield");
            templateField.appendChild(el("div", "subfield-label", t("sub_template_adherence")));
            enumField(templateField, CAT.template_adherence,
                recOrFirst("template_adherence", CAT.template_adherence),
                function () { return STATE.template_adherence; },
                function (v) { STATE.template_adherence = v; });
            sec.appendChild(templateField);
        }
```

- [ ] **Step 4: Wire the section into `renderForStage`**

In the `stage === 1` branch (~line 2159) append after `renderStyle(host);`:

```javascript
            renderTemplate(host);
```

In the legacy `else` (single-pass) branch (~line 2181), append the same line after its `renderStyle(host);`.

- [ ] **Step 5: Initialize state in `initStage1State` (~line 2220)**

Replace the existing adherence init block:

```javascript
        if (hasTemplateAdherence()) {
            STATE.template_adherence = pick("template_adherence", CAT.template_adherence);
        } else {
            delete STATE.template_adherence;
        }
```

with:

```javascript
        var templateField = templateFieldState();
        if (templateField.mode === "locked") {
            STATE.template = templateField.name || templateField.kind || "installed";
        } else {
            STATE.template = recOrFirst("template", templateCatalog()) || "free";
        }
        if (adherenceVisible()) {
            STATE.template_adherence = pick("template_adherence", CAT.template_adherence);
        } else {
            delete STATE.template_adherence;
        }
```

- [ ] **Step 6: Carry `template` in the staged payloads**

In `stage1Payload` (~line 2301) and `stage2Payload` (~line 2321), directly above the existing `if (STATE.template_adherence) ...` line, add:

```javascript
        if (STATE.template) payload.template = STATE.template;
```

(The final payload deep-copies `STATE`, so `template` rides along automatically.)

- [ ] **Step 7: Append card styles to style.css**

```css
/* ---- Stage-1 template card (decks-only selector) ---- */
.template-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 12px;
}
.template-card {
    border: 1.5px solid var(--border, #E2E8F0);
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    background: #fff;
}
.template-card.selected { border-color: var(--accent, #2563EB); box-shadow: 0 0 0 2px rgba(37, 99, 235, .18); }
.template-card.recommended .rec-badge { display: inline-block; margin-top: 4px; }
.template-card .option-preview-template { aspect-ratio: 16 / 9; background: #F8FAFC; }
.template-card .option-preview-template img,
.template-card .option-preview-template svg { width: 100%; height: 100%; display: block; object-fit: cover; }
.template-card-copy { padding: 10px 12px; }
.template-card-name { font-weight: 600; display: flex; align-items: center; gap: 8px; }
.template-color-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,.12); }
.template-card-meta { font-size: 12px; color: #64748B; margin-top: 2px; }
.template-card-desc { font-size: 12.5px; color: #475569; margin-top: 6px; line-height: 1.45; }
.template-card-locked { cursor: default; max-width: 460px; }
```

(If `style.css` does not define `--border` / `--accent` custom properties, the fallback values in `var()` apply — no further change needed.)

- [ ] **Step 8: Syntax-check and interactive smoke**

```bash
node --check .claude/skills/ppt-master/scripts/confirm_ui/static/app.js
```

Expected: no output (exit 0).

Launch on the smoke project (recommendations.json from Task 2 is already stage1):

```bash
python3 .claude/skills/ppt-master/scripts/confirm_ui/server.py projects/_smoke_stage1_template --daemon --no-browser
```

Drive the page with the available browser tooling (Playwright MCP / agent-browser) at the printed URL and verify: (1) a "템플릿" section shows 4 cards (자유 디자인 + apple/jangpm/mckinsey) with SVG previews, free selected+badged; (2) clicking a deck card reveals the adherence subfield (adaptive badged), clicking 자유 디자인 hides it; (3) click a deck, then Next → read `projects/_smoke_stage1_template/confirm_ui/result.json`:

```bash
python3 -c "
import json, sys; sys.stdout.reconfigure(encoding='utf-8')
r = json.load(open('projects/_smoke_stage1_template/confirm_ui/result.json', encoding='utf-8'))
print(r['status'], r['template'], r.get('template_adherence'))
assert r['status'] == 'stage1-confirmed' and r['template'] in {'apple','jangpm','mckinsey'}
assert r['template_adherence'] in {'adaptive','strict'}
print('OK')
"
```

Then shut down and reset the smoke result:

```bash
python3 .claude/skills/ppt-master/scripts/confirm_ui/server.py projects/_smoke_stage1_template --shutdown
rm projects/_smoke_stage1_template/confirm_ui/result.json
```

If no browser tooling is available, state that explicitly and ask the user to click through — do not skip the result.json assertion.

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/ppt-master/scripts/confirm_ui/static/app.js .claude/skills/ppt-master/scripts/confirm_ui/static/style.css
git commit -m "confirm-ui: render stage1 template card with shell previews"
```

---

### Task 5: Docs — SKILL.md Step 3 + Step 4

**Files:**
- Modify: `.claude/skills/ppt-master/SKILL.md` (trigger table ~line 254-268, checkpoint ~line 376, Step 4 stage table ~line 415, Step 4 steps 1/3 ~lines 425-435)

**Interfaces:**
- Produces: the pipeline contract Tasks 6-8 cross-reference ("deferred install", "narrow disambiguation").

- [ ] **Step 1: Extend the Step 3 trigger table**

Replace the third table row:

```markdown
| Anything else — bare template names ("用 academic_defense"), style descriptions ("麦肯锡风格"), brand mentions ("招商银行风格"), vague intent ("想用个模板"), or silence | Skip Step 3, free design |
```

with two rows:

```markdown
| Explicit template-seeking intent without a path ("use a template", "想用个模板", "템플릿 써줘"), or a bare name matching a **deck** id in `decks_index.json` ("apple 템플릿으로") | Ask the single narrow disambiguation question below, then either consume the confirmed deck path as a normal explicit-path trigger or take free design |
| Anything else — bare layout/brand names ("用 academic_defense", "anthropic"), style descriptions ("麦肯锡风格"), or silence | Skip Step 3, free design (the Step 4 Stage 1 template card still offers the deck library) |
```

- [ ] **Step 2: Rewrite the no-fuzzy sentence and the bare-names note**

Replace:

```markdown
There is no slug matching, no name lookup, no fuzzy resolution. A name without a path does not trigger — the user must give a path the AI can `cd` into.
```

with:

```markdown
There is no fuzzy resolution into an install. A deck-id mention or explicit template intent triggers only the single disambiguation question below — never a direct install; every other name flows to free design. The path that enters the install is always one the user confirmed.

**Narrow disambiguation (single question, only on the trigger above).** List the matched deck(s) — or, for pure intent with no name, up to 3 decks most relevant to the content — each with its workspace path (`templates/decks/<id>/`) and one-line summary from `decks_index.json`, plus a "free design" option. In Claude Code surface this with the AskUserQuestion tool; other hosts ask the same single question in chat. A deck answer confirms that explicit path (normal Step 3 install); free design skips Step 3 — the Stage 1 template card still allows re-picking. Ask at most once per run, and never when the trigger did not fire.
```

Replace the note:

```markdown
> Bare names ("academic_defense", "招商银行", "anthropic") do NOT trigger Step 3 even if a matching directory exists in the library. The user must give a path. AI must not "helpfully" resolve a name to a path.
```

with:

```markdown
> Bare names that match a **deck** id trigger only the disambiguation question above. Layout/brand bare names ("academic_defense", "anthropic") do NOT trigger Step 3 even if a matching directory exists — the user must give a path. AI must never silently resolve a name to a path and install it without the user's answer.
```

- [ ] **Step 3: Add the deferred-install subsection (immediately before the Step 3 checkpoint line ~376)**

```markdown
#### Deferred install — Stage 1 template card

When Step 3 took the free-design default, the Step 4 Confirm UI Stage 1 page still offers a decks-only template card (catalog synced live from `decks_index.json`; free design is the default). If the confirmed stage-1 `result.json` carries `template: "<deck_id>"`, run this Step's install for `templates/decks/<deck_id>/` at that point — same kind matrix, same structured-template preflight, no bypass — in the same turn, before re-deriving Stage 2. On preflight failure do NOT silently fall back to free design: report the error in chat and let the user re-pick (another deck or free design). `template: "free"` (or the field's absence) keeps the free-design path. When a template was already installed via an explicit path, the card renders locked (informational) and no deferred install happens.
```

And extend the checkpoint line:

```markdown
**✅ Checkpoint — Default path proceeds to Step 4 without user interaction. If the user supplied one or more explicit template paths, those have been copied, staged in place, or fused into `<project_path>/templates/` before advancing. A Stage-1 template-card selection installs later, at the Step 4 stage-1 handoff (see Deferred install above).**
```

- [ ] **Step 4: Update the Step 4 stage table and steps**

In the stage table (~line 415), extend the Stage 1 "Confirms" cell by appending before the final `|`:

```markdown
 · `template` *(decks-only card; free-design default — locked informational when Step 3 already installed a template)*
```

In step 1 (write Stage 1, ~line 425), after the sentence ending "omit the field entirely for free design and brand-only templates so the page does not display it.", insert:

```markdown
Always set `recommend.template` for the Stage-1 template card: a deck id from `decks_index.json` only when the content genuinely matches that deck's use cases, otherwise `"free"` (the honest default — see strategist.md §1). When a template is already installed via an explicit path the card renders locked and the key may be omitted.
```

In step 3 (re-derive Stage 2, ~line 431), after "Read the stage-1 `result.json` (`status: stage1-confirmed`).", insert:

```markdown
**Deferred template install**: if the result carries `template: "<deck_id>"` and no template is installed yet, first run the Step 3 deferred install for that deck (same kind matrix + structured preflight — no bypass) in this same turn; on preflight failure report in chat and let the user re-pick instead of silently downgrading. The installed template skin then becomes the recommended Stage-2 color / typography candidate per the existing rule.
```

- [ ] **Step 5: Verify and commit**

Re-read the edited Step 3/Step 4 sections end-to-end to confirm no contradiction remains (especially: the free-design default line at the top of Step 3 stays valid — the card lives in Step 4; the disambiguation question fires pre-pipeline only).

```bash
git add .claude/skills/ppt-master/SKILL.md
git commit -m "skill: stage1 template card orchestration + narrow disambiguation trigger"
```

---

### Task 6: Docs — strategist.md §1 recommendation rule

**Files:**
- Modify: `.claude/skills/ppt-master/references/strategist.md` (stage table ~line 31; new paragraph after the Confirm UI paragraph ~line 41; adherence default ~line 112)

- [ ] **Step 1: Extend the Stage 1 row of the three-stage table**

In the row `| **1 — direction anchors** | ... · template adherence *(only when Step 3 loaded a deck/layout template)* | confirmed first |`, append after the template-adherence item:

```markdown
 · template card *(decks-only; free-design default)*
```

- [ ] **Step 2: Add the recommendation-logic paragraph (new blockquote after the "Default presentation surface — Confirm UI." paragraph, ~line 41)**

```markdown
> **Template card recommendation (Stage 1).** The page lists the deck library (synced from `decks_index.json`) plus "free design". Set `recommend.template` to a deck id **only when the deck's summary / use cases genuinely fit the content, audience, and purpose**; otherwise recommend `free`. Free design is the honest default — never over-recommend a deck for merely style-adjacent content (a style wish maps to `visual_style`, not a template). A deck confirmed here is installed after Stage 1 (SKILL.md Step 3 "Deferred install"), and its skin becomes the recommended Stage-2 color / typography candidate; when a template is already installed via an explicit path the card is locked and needs no recommendation.
```

- [ ] **Step 3: Extend the adherence default paragraph (~line 112)**

After the sentence "Recommend `adaptive` when the user supplied only a template path with no stricter instruction.", insert:

```markdown
The same default applies when the deck was selected through the Stage-1 template card (deferred install): the card surfaces `template_adherence` beside the deck choice, preset to `adaptive`.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/references/strategist.md
git commit -m "strategist: stage1 template card membership + honest-default recommendation rule"
```

---

### Task 7: Docs — confirm_ui.md schema

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/docs/confirm_ui.md` (intro ~line 3; server bullets ~line 43; field-kinds ~lines 53-59; catalogs ~line 65; stage table ~line 77; recommendations schema + bullets ~lines 88-172; result schema + bullets ~lines 176-206)

- [ ] **Step 1: Intro + field kind**

In the intro paragraph (line 3), change "Fully closed fields (template adherence when a deck/layout template is active, AI source when applicable, formula policy, generation mode, refine spec) do not." to:

```markdown
Fully closed fields (the Stage-1 template card, template adherence when a deck/layout template is active or a deck card is selected, AI source when applicable, formula policy, generation mode, refine spec) do not.
```

In "Two kinds of field" → the **Closed enumerable** bullet, change "template adherence (conditional), formula policy / generation mode / refine spec" to:

```markdown
the Stage-1 template card (decks-only; free design default — rendered as preview cards, locked informational when Step 3 already installed a template), template adherence (conditional), formula policy / generation mode / refine spec
```

- [ ] **Step 2: Server behavior bullets (after the `_template_adherence_enabled` bullet, ~line 43)**

```markdown
- `/api/recommendations` also injects `_template_field`: `{"mode": "selector"}` when no template is installed (the Stage-1 card is an active decks-only selector; picking a deck reveals the `template_adherence` subfield client-side, default `adaptive`), or `{"mode": "locked", "kind", "name"}` when `<project>/templates/design_spec.md` exists (the card renders as a read-only badge of the installed template; `name` is the spec's first H1). `result.json.template` folds back into `recommend.template` on later stages like the other anchors.
- `/api/template_preview/<deck_id>?lang=<zh|en|ja|ko>` serves the deck's first roster shell SVG with `{{TOKEN}}` slots substituted by fixed role sample copy (same principle as the visual-style previews — users compare visual treatment, not project content). `deck_id` is validated against `decks_index.json`; unknown ids 404; the response is `no-store`. Unresolvable external references degrade gracefully (that element simply does not render).
```

- [ ] **Step 3: Catalogs section (~line 65)**

Add `templates` to the listed keys sentence ("Keys: `canvas`, `modes`, ...") and append to the section:

```markdown
`templates` is synced live from `templates/decks/decks_index.json` the same way `canvas` is synced from `config.py`: the static catalogs.json entry holds only the `free` option with its four-language labels; deck entries (`id`, `desc` from the index summary, `canvas_format`, `page_count`, `primary_color`) are appended at serve time, so the card can never drift from the installed deck library.
```

- [ ] **Step 4: Stage table + schemas**

Stage table `"stage1"` row (~line 77): change "plus `template_adherence` only when a deck/layout template is active" to:

```markdown
plus the `template` card (decks-only selector, or a locked badge when a template is already installed) and `template_adherence` when a deck/layout template is active or a deck card is selected
```

Recommendations example (~line 93): add to the `recommend` block after `"canvas": "ppt169",`:

```json
    "template": "free",
```

Add a bullet after the `recommend.template_adherence` bullet (~line 158):

```markdown
- `recommend.template` names the Stage-1 template card pick: a deck id from `decks_index.json` only when the content genuinely matches that deck, otherwise `"free"` (the honest default). Omit when a template is already installed (locked card). When the confirmed stage-1 `result.json` carries a deck id, the AI runs the SKILL.md Step 3 deferred install (same structured preflight) before re-deriving Stage 2 — the template skin then becomes the recommended color / typography candidate.
```

Result example (~line 184): add after `"visual_style": "swiss-minimal",`:

```json
  "template": "free",
```

Add a result bullet (after the custom-string bullet ~line 204):

```markdown
- `template` is the Stage-1 card value: a deck id, `"free"`, or — locked card — the installed template's display name (informational; never a re-install trigger). `template_adherence` accompanies it only when a deck is active.
```

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/scripts/docs/confirm_ui.md
git commit -m "confirm-ui docs: stage1 template card schema, preview endpoint, field state"
```

---

### Task 8: Docs — routing.md name-mention rows

**Files:**
- Modify: `.claude/skills/ppt-master/workflows/routing.md` (~lines 87, 91)

- [ ] **Step 1: Update the name-mention row**

Replace:

```markdown
| Bare template name, brand name, style label, or vague "use a template" | Do not trigger Step 3; treat as style input for Strategist confirmation stage |
```

with:

```markdown
| Explicit "use a template" intent, or a bare name matching a deck id in `decks_index.json` | Ask the single narrow disambiguation question (SKILL.md Step 3): matched deck path(s) + free design; a deck answer enters Step 3 as a confirmed explicit path |
| Bare layout/brand name or style label | Do not trigger Step 3; treat as style input for the Strategist confirmation stage (the Stage 1 template card still offers the deck library) |
```

- [ ] **Step 2: Update the fuzzy-resolution paragraph**

Replace:

```markdown
**Forbidden - fuzzy resolution**: Do not resolve bare names to local template directories on the user's behalf. The user must provide the path that enters Step 3. For every current template kind, that path is the workspace root.
```

with:

```markdown
**Forbidden - fuzzy resolution**: Do not resolve bare names to local template directories and install them on the user's behalf. A deck-id mention triggers only the single disambiguation question; the path that enters Step 3 is always one the user confirmed (their answer, an explicit path, or the Stage 1 template card). For every current template kind, that path is the workspace root.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ppt-master/workflows/routing.md
git commit -m "routing: deck-name mentions route to the narrow disambiguation question"
```

---

### Task 9: Regression pass + cleanup

**Files:**
- No new files; re-runs Task 1-4 verifications and checks cross-doc consistency.

- [ ] **Step 1: Re-run all server smoke checks** (Task 1 Step 4, Task 2 Step 3, Task 3 Step 4 command blocks — all must print `OK`).

- [ ] **Step 2: Locked-mode UI regression**

Recreate `projects/_smoke_stage1_template/templates/design_spec.md` with `---\nkind: deck\n---\n\n# Smoke Deck\n`, relaunch the confirm server, and verify in the browser that Stage 1 shows the locked badge card ("Smoke Deck" + locked note), no selectable deck cards, and the adherence field (existing behavior). Shut down, then delete `templates/design_spec.md` and any `result.json`.

- [ ] **Step 3: Free-path regression**

Relaunch, confirm Stage 1 with 자유 디자인 selected → `result.json` has `template: "free"` and **no** `template_adherence`. Shut down; delete the smoke project directory.

- [ ] **Step 4: Environment gate + doc coherence**

```bash
python3 .claude/skills/ppt-master/scripts/preflight.py
```

Expected: PASS (no stale-stub failure — frontmatter untouched). Then grep the four docs for consistency:

```bash
grep -rn "disambiguation\|Deferred install\|template_preview\|_template_field" .claude/skills/ppt-master/SKILL.md .claude/skills/ppt-master/references/strategist.md .claude/skills/ppt-master/scripts/docs/confirm_ui.md .claude/skills/ppt-master/workflows/routing.md | head -30
```

Confirm every cross-reference resolves (SKILL.md owns "Deferred install"; confirm_ui.md owns `_template_field` / `template_preview`; strategist/routing point at SKILL.md).

- [ ] **Step 5: Commit any fixups**

```bash
git status --short
```

If fixups were needed, commit them: `git commit -am "stage1 template card: regression fixups"`. Otherwise done — report the full commit list.

---

## Deferred (explicitly out of scope)

- layouts / brands entries on the card; card-driven fusion (path-based only).
- Live E2E deck generation through Steps 5-7 (the spec's E2E item runs as a separate user-driven session with a real topic, since SVG generation is main-agent work by Global Discipline rule 6).
