"""
Convert the extracted docx paragraphs (paras.json) into site data:
  data/book.json     -> metadata + table of contents (sections -> pages)
  data/s<N>.json     -> the actual reading pages for each section
  assets/img/*.jpg   -> web-sized copies of the photos in the docx

Structure found in the source document:
  * title page + epigraph        paras 19-50
  * unnumbered opening essays    paras 51-290
  * 200 numbered entries         "Heading 2" paragraphs containing just a number
  * 6 photos / 2 notebook pages  placed on their own page, used as dividers
"""
import json, re, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = json.load(open(os.path.join(HERE, "paras.json")))
os.makedirs(f"{ROOT}/data", exist_ok=True)
os.makedirs(f"{ROOT}/assets/img", exist_ok=True)

# ---- images (resize to web size) -----------------------------------------
for i in range(1, 9):
    src = f"{HERE}/image{i}.jpeg"
    dst = f"{ROOT}/assets/img/p{i}.jpg"
    subprocess.run(["sips", "-Z", "1400", "-s", "format", "jpeg", "-s", "formatOptions", "72", src, "--out", dst],
                   check=True, stdout=subprocess.DEVNULL)

# ---- block classification -------------------------------------------------
ATTR = re.compile(r"^(.*?)\s*(\([^()]{3,120}\)\.?)\s*$", re.S)   # group 2 keeps his brackets and full stop exactly

def classify(text):
    t = text.strip()
    words = len(t.split())
    m = ATTR.match(t)
    if m and (t.startswith(("“", '"')) or re.search(r"[–—\-,]|\d{4}", m.group(2))) and len(m.group(1).split()) >= 3:
        return {"t": "q", "x": m.group(1).strip(), "s": m.group(2).strip()}   # source kept verbatim, with ( ) and full stop
    if t.startswith(("“", '"')):
        return {"t": "q", "x": t}
    if words <= 8:
        return {"t": "l", "x": t}
    return {"t": "p", "x": t}

def wc(b):
    return len(b.get("x", "").split())

SRC_ONLY = re.compile(r"^(\([^()]{3,140}\)\.?)$")

def to_blocks(raws):
    """Raw paragraph strings -> blocks. Keeps multi-line quotes together and
    attaches a stand-alone "(Source)" line to the quote above it."""
    blocks, i = [], 0
    while i < len(raws):
        t = raws[i]; i += 1
        m = SRC_ONLY.match(t)
        if m and blocks:
            last = blocks[-1]
            src = m.group(1).strip()
            if last["t"] != "q":
                last["t"] = "q"
            last["s"] = (last["s"] + " " + src) if last.get("s") else src
            continue
        if t.count("“") > t.count("”"):          # quote that continues over several paragraphs
            parts, j = [t], i
            while j < len(raws) and j - i < 8 and sum(x.count("“") for x in parts) > sum(x.count("”") for x in parts):
                parts.append(raws[j]); j += 1
            if sum(x.count("“") for x in parts) <= sum(x.count("”") for x in parts):
                i = j
                blocks.append({"t": "q", "x": "\n".join(parts)})
                continue
        blocks.append(classify(t))
    return blocks

def units(a, b):
    """Split paragraphs [a,b) into entry-units: (entry_number|None, [blocks])."""
    out, cur_n, cur = [], None, []
    for p in P[a:b]:
        t = p["text"].strip()
        if p["style"] == "heading 2":
            if re.fullmatch(r"\d+", t):
                if cur: out.append((cur_n, to_blocks(cur)))
                cur_n, cur = int(t), []
            continue  # blank headings only carry images
        if t:
            cur.append(t)
    if cur: out.append((cur_n, to_blocks(cur)))
    return out

TARGET, MAXU = 2300, 3000

def paginate(us):
    """Group entry-units into reading pages of roughly TARGET words."""
    pages, cur, curw = [], [], 0
    def flush():
        nonlocal cur, curw
        if cur: pages.append(cur)
        cur, curw = [], 0
    for n, blocks in us:
        w = sum(wc(b) for b in blocks)
        head = [{"t": "n", "x": str(n)}] if n is not None else []
        if w > MAXU:  # long entry (or unnumbered essay run): split on paragraph boundaries
            flush()
            chunk, cw, first = list(head), 0, True
            for b in blocks:
                if cw >= TARGET and b["t"] != "l":
                    pages.append(chunk); chunk, cw, first = [], 0, False
                chunk.append(b); cw += wc(b)
            if chunk: pages.append(chunk)
            continue
        if curw + w > TARGET + 400: flush()
        cur += head + blocks; curw += w
    flush()
    return pages

def head_title(x):
    """Navigation label for an entry = its own opening words (verbatim; '…' when cut)."""
    x = re.sub(r"\s+", " ", x).strip().lstrip("“").strip()
    m = re.match(r"^(.{12,64}?[.!?:;,])(\s|$)", x)          # a short opening sentence/clause reads best
    if m and len(m.group(1)) <= 64:
        t = m.group(1).rstrip(",;:")
    elif len(x) <= 64:
        t = x
    else:
        t = x[:62].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    if "”" in t and "“" not in t:          # closing mark of the quote we just opened with
        t = t.replace("”", "")
    return t

def page_meta(blocks, idx):
    nums = [int(b["x"]) for b in blocks if b["t"] == "n"]
    words = sum(wc(b) for b in blocks)
    prev = next((b["x"] for b in blocks if b["t"] in ("q", "l", "p")), "")
    prev = re.sub(r"\s+", " ", prev)
    prev = (prev[:78].rsplit(" ", 1)[0] + "…") if len(prev) > 80 else prev
    heads = []
    for k, bl in enumerate(blocks):
        if bl["t"] == "n" and k + 1 < len(blocks):
            heads.append([int(bl["x"]), head_title(blocks[k + 1]["x"])])
    return {"entries": [nums[0], nums[-1]] if nums else None, "words": words, "preview": prev, "heads": heads}

# ---- sections -------------------------------------------------------------
SECTIONS = [
    # id, roman, [start, end) paragraphs, images
    ("open", "Mở đầu", 51, 291, []),
    ("s1", "I",   291, 355, []),
    ("s2", "II",  355, 431, [2]),
    ("s3", "III", 431, 623, [3]),
    ("s4", "IV",  623, 1087, [4]),
    ("s5", "V",   1087, 1722, [5]),
    ("s6", "VI",  1722, 3669, [6]),
    ("s7", "VII", 3669, 3941, [7, 8]),
    ("end", "Cuối sách", 3941, len(P), []),
]

captions = {2: "", 3: "", 4: "Trang vở học bài của Tin", 5: "", 6: "", 7: "Trang vở học tiếng Anh của Tin", 8: "Trang vở học tiếng Anh của Tin"}

book = {
    "cover": {
        "title": "Nhàn Thoại",
        "subtitle": "Tuyên ngôn của một kẻ tầm thường",
        "tagline": "Di sản của vô minh",
        "author": "Nguyễn Hồng Phúc",
        "nick": "Tin",
        "dates": "04/02/1991 – 18/12/2025",
        "credits": [P[22]["text"].strip(), P[23]["text"].strip(), P[24]["text"].strip()],
        # the couplet he chose to close the book with (paras 3904-3906) - cheerful & humble, in his own words
        "epigraph": P[3904]["text"].strip() + "\n" + P[3905]["text"].strip(),
        "epigraphSrc": P[3906]["text"].strip(),
        "photo": "assets/img/portrait-happy.jpg",
    },
    "sections": [],
}

total_pages = 0
running = None  # entry number currently in progress (for pages that continue a long entry)
for sid, roman, a, b, imgs in SECTIONS:
    us = units(a, b)
    pages = paginate(us)
    running = None  # don't guess continuity across the author's photo dividers
    metas = []
    for i, pg in enumerate(pages):
        m = page_meta(pg, i)
        if pg and pg[0]["t"] != "n" and running is not None:
            m["cont"] = running
        nn = [int(x["x"]) for x in pg if x["t"] == "n"]
        if nn: running = nn[-1]
        metas.append(m)
    nums = [m["entries"] for m in metas if m["entries"]]
    sec = {
        "id": sid,
        "label": roman,
        "images": [{"src": f"assets/img/p{i}.jpg", "cap": captions[i]} for i in imgs],
        "entries": [min(n[0] for n in nums), max(n[1] for n in nums)] if nums else None,
        "words": sum(m["words"] for m in metas),
        "pages": metas,
    }
    book["sections"].append(sec)
    json.dump({"id": sid, "pages": pages}, open(f"{ROOT}/data/{sid}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    total_pages += len(pages)
    print(f"{sid:5s} {roman:8s} pages={len(pages):3d} words={sec['words']:7d} entries={sec['entries']}")

book["totals"] = {"pages": total_pages, "words": sum(s["words"] for s in book["sections"]), "entries": 200}
json.dump(book, open(f"{ROOT}/data/book.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("total pages", total_pages, "words", book["totals"]["words"])

# ---- recurring themes (counted from his own text) -> data/topics.json -----
TOPICS = ["tương lai", "nhận thức", "tư duy", "thế giới", "hiện thực", "con người", "thông tin", "tự do",
          "khoa học", "hy vọng", "khám phá", "ước mơ", "sáng tạo", "học hỏi", "dữ liệu", "vũ trụ", "công nghệ"]
alltext = []
for sec in book["sections"]:
    for pg in json.load(open(f"{ROOT}/data/{sec['id']}.json"))["pages"]:
        alltext += [b["x"].lower() for b in pg if b["t"] != "n"]
alltext = "\n".join(alltext)
topics = sorted(({"t": t, "n": alltext.count(t)} for t in TOPICS), key=lambda x: -x["n"])
json.dump(topics, open(f"{ROOT}/data/topics.json", "w"), ensure_ascii=False)
print("topics:", [(x["t"], x["n"]) for x in topics])
