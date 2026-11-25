import zipfile, re, json, collections
import xml.etree.ElementTree as ET
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
z = zipfile.ZipFile("/Users/lam/Downloads/Nhàn thoại.docx")
root = ET.fromstring(z.read("word/document.xml"))
body = root.find(W+"body")

# style names
st = ET.fromstring(z.read("word/styles.xml"))
names = {s.get(W+"styleId"): (s.find(W+"name").get(W+"val") if s.find(W+"name") is not None else "") for s in st.iter(W+"style")}

paras = []
for p in body.iter(W+"p"):
    ppr = p.find(W+"pPr")
    style = None; jc=None; outline=None
    if ppr is not None:
        s = ppr.find(W+"pStyle")
        if s is not None: style = names.get(s.get(W+"val"), s.get(W+"val"))
        j = ppr.find(W+"jc")
        if j is not None: jc = j.get(W+"val")
        o = ppr.find(W+"outlineLvl")
        if o is not None: outline = o.get(W+"val")
    text = ""; bold_all=True; any_run=False; sizes=collections.Counter(); img=0; pb=False
    for r in p.iter(W+"r"):
        t = "".join(x.text or "" for x in r.findall(W+"t"))
        if r.find(".//"+W+"drawing") is not None or r.find(".//{urn:schemas-microsoft-com:vml}imagedata") is not None: img+=1
        for br in r.findall(W+"br"):
            if br.get(W+"type")=="page": pb=True
        if t:
            any_run=True; text+=t
            rpr = r.find(W+"rPr")
            b = rpr is not None and rpr.find(W+"b") is not None
            bold_all = bold_all and b
            if rpr is not None and rpr.find(W+"sz") is not None: sizes[rpr.find(W+"sz").get(W+"val")]+=len(t)
    paras.append(dict(style=style, jc=jc, outline=outline, text=text, bold=bool(any_run and bold_all), size=(sizes.most_common(1)[0][0] if sizes else None), img=img, pb=pb))
json.dump(paras, open("paras.json","w"), ensure_ascii=False)
print("paragraphs", len(paras), "non-empty", sum(1 for p in paras if p["text"].strip()))
print("styles", collections.Counter(p["style"] for p in paras).most_common())
print("sizes", collections.Counter(p["size"] for p in paras if p["text"].strip()).most_common(8))
print("outline", collections.Counter(p["outline"] for p in paras))
print("images", sum(p["img"] for p in paras), "pagebreaks", sum(p["pb"] for p in paras))
print("chars", sum(len(p["text"]) for p in paras), "words", sum(len(p["text"].split()) for p in paras))
