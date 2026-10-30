#!/usr/bin/env python3
"""HWPX(한글) 파일 도우미 — 양식 구조는 그대로 두고 글자만 읽고/채운다.

사용법
  python hwpx_tool.py text  문서.hwpx              # 본문 글자 추출(표는 | 로 구분)
  python hwpx_tool.py fields 양식.hwpx             # 양식 안의 {{빈칸}} 목록
  python hwpx_tool.py fill  양식.hwpx 값.json 결과.hwpx
        값.json 예: {"행사명": "진로체험의 날", "일시": "2026. 11. 20.(목)"}
        - 값이 없는 {{빈칸}}은 "[확인 필요]"로 채운다(지어내지 않기 위해).
        - 값을 ""로 주면 그 칸은 빈칸으로 남는다.
        - 표의 행 수, 칸 합치기, 글꼴, 정렬은 바꾸지 않는다.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape

NS = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
FIELD = re.compile(r"\{\{([^{}]+)\}\}")


def _sections(z):
    return sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))


def _para_text(p):
    return "".join(t.text or "" for t in p.iter(NS + "t"))


def _walk(elem, out, depth=0):
    for child in elem:
        if child.tag == NS + "p":
            tables = [t for t in child.iter(NS + "tbl")]
            if tables:
                for tbl in child.findall(f".//{NS}run/{NS}tbl"):
                    out.append("[표]")
                    for tr in tbl.findall(NS + "tr"):
                        cells = []
                        for tc in tr.findall(NS + "tc"):
                            sub = tc.find(NS + "subList")
                            cells.append(" / ".join(_para_text(pp) for pp in sub.findall(NS + "p")
                                                    if _para_text(pp).strip()))
                        out.append("| " + " | ".join(cells) + " |")
                    out.append("[표 끝]")
                own = "".join((t.text or "") for r in child.findall(NS + "run") for t in r.findall(NS + "t"))
                if own.strip():
                    out.append(own)
            else:
                txt = _para_text(child)
                if txt.strip():
                    out.append(txt)


def cmd_text(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in _sections(z):
        _walk(ET.fromstring(z.read(n)), out)
    print("\n".join(out))


def cmd_fields(path):
    z = zipfile.ZipFile(path)
    seen = []
    for n in _sections(z):
        for f in FIELD.findall(unescape(z.read(n).decode("utf-8"))):
            if f not in seen:
                seen.append(f)
    print("\n".join(seen))


def cmd_fill(src, values_json, dst):
    values = json.load(open(values_json, encoding="utf-8"))
    zin = zipfile.ZipFile(src)
    missing = []

    def fill_t(m):
        inner = unescape(m.group(2))

        def rep(f):
            key = f.group(1)
            if key in values:
                return str(values[key])
            missing.append(key)
            return "[확인 필요]"
        return m.group(1) + escape(FIELD.sub(rep, inner)) + m.group(3)

    with zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if re.match(r"Contents/section\d+\.xml$", info.filename):
                xml = data.decode("utf-8")
                xml = re.sub(r"(<hp:t>)(.*?)(</hp:t>)", fill_t, xml, flags=re.S)
                xml = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", xml, flags=re.S)
                data = xml.encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.create_system = info.create_system
            zout.writestr(zi, data)
    used = [k for k in values if k not in missing]
    print(f"저장: {dst}")
    if missing:
        print("[확인 필요]로 채운 빈칸:", ", ".join(dict.fromkeys(missing)))
    unknown = [k for k in values if not k.startswith("_") and f"{{{{{k}}}}}" not in
               unescape("".join(zin.read(n).decode("utf-8") for n in _sections(zin)))]
    if unknown:
        print("양식에 없는 키(무시됨):", ", ".join(unknown))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("text", "fields", "fill"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "text":
        cmd_text(sys.argv[2])
    elif sys.argv[1] == "fields":
        cmd_fields(sys.argv[2])
    else:
        cmd_fill(sys.argv[2], sys.argv[3], sys.argv[4])
