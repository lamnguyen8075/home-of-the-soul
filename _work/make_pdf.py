#!/usr/bin/env python3
"""
Build the downloadable PDF of the whole book  ->  assets/Nhan-Thoai-Nguyen-Hong-Phuc.pdf

  * reads exactly the same data/*.json the website reads (so the words are Tin's, untouched)
  * lays it out as an A5 book (title page, contents with page numbers, parts, running heads, page numbers)
  * renders with headless Google Chrome, then renders a 2nd time so the contents page shows real page numbers
  * PDF bookmarks (outline) are generated: parts + all 200 entries

Run:   python3 _work/make_pdf.py          (needs Google Chrome and `pip install --user pymupdf`)
"""
import html, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "Nhan-Thoai-Nguyen-Hong-Phuc.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

book = json.load(open(f"{ROOT}/data/book.json"))
cover = book["cover"]
T = book["totals"]
esc = lambda s: html.escape(s, quote=True)
fonts_css = open(f"{HERE}/fonts/fonts.css").read()   # @font-face rules, paths relative to _work/print.html

CSS = r"""
@page { size: A5; margin: 17mm 15mm 19mm 15mm;
  @top-left   { content: "Nhàn Thoại"; font: 500 7pt 'Lexend', sans-serif; letter-spacing: .14em; text-transform: uppercase; color: #b08a92; }
  @top-right  { content: string(sec); font: 500 7pt 'Lexend', sans-serif; letter-spacing: .14em; text-transform: uppercase; color: #b08a92; }
  @bottom-center { content: counter(page); font: 400 8.5pt 'Lexend', sans-serif; color: #7a5f6e; } }
@page :first { @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; } }
@page opener { @top-left { content: none; } @top-right { content: none; } }

:root { --ink: #33202e; --soft: #7a5f6e; --blue: #d9482f; --violet: #c2437c; --line: #efd5cc; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 400 10.4pt/1.62 'Lora', Georgia, serif; color: var(--ink); orphans: 3; widows: 3; }
a { color: inherit; text-decoration: none; }
h1, h2 { margin: 0; font-family: 'Fraunces', 'Lexend', serif; font-weight: 600; }

/* ---- title page ---- */
.title { page-break-after: always; text-align: center; padding-top: 0; height: 172mm; overflow: hidden; }
.title .photo { width: 42mm; height: 52mm; margin: 0 auto 6mm; padding: 1.4mm; border-radius: 6mm; background: linear-gradient(135deg, #ff8a5c, #ff6f91 60%, #b78cff); }
.title .photo img { width: 100%; height: 100%; object-fit: cover; object-position: 50% 28%; border-radius: 4.8mm; display: block; }
.title .eyebrow { font: 500 7.5pt 'Lexend', sans-serif; letter-spacing: .2em; text-transform: uppercase; color: var(--blue); margin: 0 0 3mm; }
.title h1 { font-family: 'Fraunces', serif; font-size: 38pt; line-height: 1.05; letter-spacing: -.01em; margin-bottom: 3mm; }
.title .sub { font: italic 500 13pt 'Fraunces', 'Lora', serif; color: var(--violet); margin: 0 0 2mm; }
.title .tag { font: italic 10pt 'Lora', serif; color: var(--soft); margin: 0 0 5mm; }
.title .by { font: 600 12pt 'Lexend', sans-serif; margin: 0; }
.title .by em { font-weight: 400; color: var(--soft); font-style: normal; }
.title .dates { font: 400 8.5pt 'Lexend', sans-serif; color: var(--soft); margin: 1.5mm 0 0; letter-spacing: .04em; }
.orn { width: 34mm; height: .5mm; margin: 6mm auto; background: linear-gradient(90deg, transparent, #ff7a59, #ff6f91, transparent); position: relative; }
.orn::after { content: ""; position: absolute; left: 50%; top: 50%; width: 2.2mm; height: 2.2mm; transform: translate(-50%, -50%) rotate(45deg); background: linear-gradient(135deg, #ff8a5c, #ff6f91); }
.title .credits { font: italic 9pt 'Lora', serif; color: var(--soft); margin: 0 0 4mm; }
.epi { white-space: pre-line; margin: 0 6mm; padding: 3mm 5mm; border-radius: 3mm; background: #fff0ea; font: italic 9.6pt/1.55 'Lora', serif; }
.epi cite { display: block; font: 500 7pt 'Lexend', sans-serif; font-style: normal; color: var(--soft); margin-top: 2mm; }
.colophon { page-break-after: always; display: flex; flex-direction: column; justify-content: flex-end; min-height: 165mm; font: 400 8.5pt/1.6 'Lora', serif; color: var(--soft); text-align: center; }
.colophon p { margin: 0 0 2mm; }

/* ---- contents ---- */
.toc-title { break-before: page; string-set: sec "Mục lục"; font-size: 20pt; text-align: center; margin-bottom: 7mm; }
.toc { font-size: 8.7pt; line-height: 1.35; }
.toc .row { display: flex; align-items: baseline; gap: 1.6mm; padding: .5mm 0; break-inside: avoid; }
.toc .sec { margin-top: 4mm; font: 600 9.6pt 'Lexend', sans-serif; color: var(--blue); }
.toc .sec:first-child { margin-top: 0; }
.toc .no { flex: none; width: 8mm; text-align: right; font: 500 7.6pt 'Lexend', sans-serif; color: var(--blue); }
.toc .tt { flex: 0 1 auto; min-width: 0; }
.toc .dots { flex: 1 1 4mm; min-width: 4mm; border-bottom: .25mm dotted #d3a9a0; transform: translateY(-.9mm); }
.toc .pg { flex: none; width: 9mm; text-align: right; font: 400 8pt 'Lexend', sans-serif; color: var(--soft); }
.toc .sec .tt { flex: 0 1 auto; }

/* ---- part openers ---- */
.opener { page: opener; break-before: page; string-set: sec attr(data-name); text-align: center; padding-top: 10mm; }
.opener h1 { font-size: 15pt; letter-spacing: .24em; text-transform: uppercase; color: var(--soft); font-weight: 500; }
.opener h1 .big { display: inline-block; width: 100%; margin-top: 2mm; font-size: 52pt; letter-spacing: 0; text-transform: none; font-weight: 600; line-height: 1.1; color: var(--blue); }
.opener h1.word { font-size: 34pt; letter-spacing: 0; text-transform: none; font-weight: 600; color: var(--ink); margin-top: 22mm; }
.interlude { margin: 6mm auto 0; break-inside: avoid; text-align: center; }
.interlude img { display: block; margin: 0 auto; max-width: 100%; max-height: 100mm; width: auto; border-radius: 2mm; box-shadow: 0 .6mm 2.4mm rgba(26, 33, 56, .25); }
.interlude figcaption { font: italic 8.5pt 'Lora', serif; color: var(--soft); margin-top: 2.4mm; }
.after-opener { break-before: page; }

/* ---- the text ---- */
.prose p { margin: 0 0 3.1mm; text-align: justify; text-justify: inter-character; hyphens: none; overflow-wrap: break-word; }
.eno { break-after: avoid; text-align: center; margin: 9mm 0 5mm; font-size: 20pt; line-height: 1; color: var(--blue); position: relative; }
.eno .n { display: inline-block; position: relative; padding: 0 5mm; }
.eno .n::before, .eno .n::after { content: ""; position: absolute; top: 52%; width: 11mm; height: .4mm; background: linear-gradient(90deg, transparent, var(--blue)); }
.eno .n::before { right: 100%; } .eno .n::after { left: 100%; transform: scaleX(-1); }
.eno .ot { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.prose > .eno:first-child { margin-top: 0; }
.bq { margin: 4.4mm 0 4.6mm; padding: .6mm 0 .6mm 4mm; border-left: .9mm solid var(--blue); font-style: italic; break-inside: avoid; }
.bq p { margin: 0; text-align: left; white-space: pre-line; }
.bq cite { display: block; font: 500 7.6pt 'Lexend', sans-serif; font-style: normal; color: var(--soft); margin-top: 1.4mm; }
.prose .ln { font: 600 10.4pt/1.45 'Fraunces', 'Lexend', serif; color: var(--blue); margin: 0 0 1.6mm; text-align: left; break-after: avoid; }
.closing { margin-top: 14mm; text-align: center; font: 400 8pt/1.6 'Lexend', sans-serif; color: var(--soft); break-inside: avoid; }
"""


def block(b):
    t, x = b["t"], esc(b["x"])
    if t == "n":
        return None
    if t == "q":
        s = f"<cite>{esc(b['s'])}</cite>" if b.get("s") else ""
        return f'<blockquote class="bq"><p>{x}</p>{s}</blockquote>'
    if t == "l":
        return f'<p class="ln">{x}</p>'
    return f"<p>{x}</p>"


def build_html(pages):
    """pages: {'sec-s1': 12, 'e5': 20 ...} -> printed page numbers (placeholders on the 1st pass)"""
    pg = lambda k: str(pages.get(k, "000"))
    out = ['<!doctype html><html lang="vi"><head><meta charset="utf-8">',
           f'<title>{esc(cover["title"])} — {esc(cover["author"])} ({esc(cover["nick"])})</title>',
           f'<meta name="author" content="{esc(cover["author"])}">',
           f"<style>{fonts_css}\n{CSS}</style></head><body>"]

    # title page
    out.append(f"""<section class="title">
      <div class="photo"><img src="../{cover['photo']}" alt=""></div>
      <p class="eyebrow">{esc(cover['credits'][0])}</p>
      <h1>{esc(cover['title'])}</h1>
      <p class="sub">{esc(cover['subtitle'])}</p>
      <p class="tag">{esc(cover['tagline'])}</p>
      <p class="by">{esc(cover['author'])} <em>({esc(cover['nick'])})</em></p>
      <p class="dates">{esc(cover['dates'])}</p>
      <div class="orn"></div>
      <p class="credits">{esc(cover['credits'][1])} · {esc(cover['credits'][2])}</p>
      <blockquote class="epi">{esc(cover['epigraph'])}<cite>{esc(cover['epigraphSrc'])}</cite></blockquote>
    </section>""")
    out.append(f"""<section class="colophon">
      <p><b>{esc(cover['title'])}</b> — {esc(cover['author'])} ({esc(cover['nick'])}), {esc(cover['dates'])}</p>
      <p>Bản PDF này do gia đình thực hiện để gìn giữ và chia sẻ quyển sách.<br>Toàn bộ chữ nghĩa được giữ nguyên như bản thảo của Tin.</p>
      <p>{T['entries']} mục · khoảng {round(T['words'] / 1000)}.000 từ</p>
    </section>""")

    # contents
    out.append('<h1 class="toc-title" id="toc">Mục lục</h1><div class="toc">')
    for s in book["sections"]:
        name = "Mở đầu" if s["id"] == "open" else "Cuối sách" if s["id"] == "end" else f"Phần {s['label']}"
        rng = f' <span style="font-weight:400;color:#b08a92;font-size:7.6pt">· mục {s["entries"][0]}–{s["entries"][1]}</span>' if s["entries"] else ""
        out.append(f'<a class="row sec" href="#sec-{s["id"]}"><span class="tt">{name}{rng}</span><span class="dots"></span><span class="pg">{pg("sec-" + s["id"])}</span></a>')
        for p in s["pages"]:
            for n, title in p.get("heads", []):
                out.append(f'<a class="row" href="#e{n}"><span class="no">{n}</span><span class="tt">{esc(title)}</span><span class="dots"></span><span class="pg">{pg("e" + str(n))}</span></a>')
    out.append("</div>")

    # parts
    for s in book["sections"]:
        blocks = json.load(open(f"{ROOT}/data/{s['id']}.json"))["pages"]
        name = "Mở đầu" if s["id"] == "open" else "Cuối sách" if s["id"] == "end" else f"Phần {s['label']}"
        if s["id"] in ("open", "end"):
            h = f'<h1 class="word" id="sec-{s["id"]}">{name}</h1>'
        else:
            h = f'<h1 id="sec-{s["id"]}">Phần <span class="big">{s["label"]}</span></h1>'
        imgs = "".join(f'<figure class="interlude"><img src="../{im["src"]}" alt="">'
                       + (f'<figcaption>{esc(im["cap"])}</figcaption>' if im["cap"] else "") + "</figure>" for im in s["images"])
        out.append(f'<section class="opener" data-name="{name}">{h}<div class="orn"></div>{imgs}</section>')
        heads = {n: t for p in s["pages"] for n, t in p.get("heads", [])}
        out.append(f'<div class="prose{" after-opener" if imgs else ""}" style="string-set: sec \'{name}\'">')
        for page in blocks:
            for i, b in enumerate(page):
                if b["t"] == "n":
                    n = int(b["x"])
                    out.append(f'<h2 class="eno" id="e{n}"><span class="n">{n}</span><span class="ot"> · {esc(heads.get(n, ""))}</span></h2>')
                else:
                    out.append(block(b))
        if s["id"] == "end":
            out.append('<div class="closing">Sự yêu thương của gia đình<br>Nguyễn Hồng Phúc (Tin) · 1991 – 2025</div>')
        out.append("</div>")
    out.append("</body></html>")
    return "\n".join(out)


def render(html_path, pdf_path):
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--generate-pdf-document-outline",
           "--allow-file-access-from-files", f"--print-to-pdf={pdf_path}", "file://" + html_path]
    t = time.time()
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
    print(f"  rendered in {time.time() - t:.0f}s")


def outline_pages(pdf_path):
    """printed page number of every part and every entry, read back from the rendered PDF"""
    import fitz
    doc = fitz.open(pdf_path)
    lvl1 = [(t, p) for l, t, p in doc.get_toc() if l == 1]      # title, contents, then the parts in order
    pages = {"toc": lvl1[1][1]}
    for s_, (t, p) in zip(book["sections"], lvl1[2:]):
        pages["sec-" + s_["id"]] = p
    for l, t, p in doc.get_toc():
        mm = re.match(r"(\d+)$", t)
        if l == 2 and mm: pages["e" + mm.group(1)] = p
    return pages, len(doc)


def finish(pdf_in, pdf_out, pages):
    """friendly bookmarks + metadata + compression"""
    import fitz
    doc = fitz.open(pdf_in)
    toc = [[1, "Trang bìa", 1], [1, "Mục lục", pages["toc"]]]
    for s_ in book["sections"]:
        name = "Mở đầu" if s_["id"] == "open" else "Cuối sách" if s_["id"] == "end" else f"Phần {s_['label']}"
        toc.append([1, name, pages["sec-" + s_["id"]]])
        for p_ in s_["pages"]:
            for n, title in p_.get("heads", []):
                toc.append([2, f"{n} · {title}", pages["e" + str(n)]])
    doc.set_toc(toc)
    doc.set_metadata({"title": f"{cover['title']} — {cover['author']} ({cover['nick']})", "author": cover["author"],
                      "subject": cover["subtitle"], "keywords": "Nhàn Thoại, Nguyễn Hồng Phúc, Tin", "creator": "Gia đình — the-memory"})
    doc.save(pdf_out, garbage=4, deflate=True, deflate_fonts=True)


if __name__ == "__main__":
    html_path = os.path.join(HERE, "print.html")
    tmp_pdf = os.path.join(HERE, "print.pdf")
    pages = {}
    for attempt in range(1, 4):
        print(f"pass {attempt}")
        open(html_path, "w", encoding="utf8").write(build_html(pages))
        render(html_path, tmp_pdf)
        new, n = outline_pages(tmp_pdf)
        print(f"  {n} pages, {len(new)} bookmarks found")
        if new == pages:
            break
        pages = new
    finish(tmp_pdf, OUT, pages)
    os.remove(tmp_pdf)
    print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")
