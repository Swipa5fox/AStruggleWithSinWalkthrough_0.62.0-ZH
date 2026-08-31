# -*- coding: utf-8 -*-

import html as html_mod
import os
import re
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
MD_DIR = os.path.join(BASE, "markdown")
IMG_SRC = os.path.join(MD_DIR, "images")
OUT = BASE  # 站点就是仓库根目录，GitHub Pages 直接发布 /(root)
IMG_OUT = os.path.join(BASE, "images")

# (slug, 菜单标题) - 顺序与 README 保持一致
SECTIONS = [
    ("wt-info", "基本信息"),
    ("wt-tips", "技巧与提示"),
    ("wt-house", "房屋翻新"),
    ("wt-intro", "序章"),
    ("wt-mc", "主角"),
    ("wt-church", "教堂"),
    ("wt-monastery", "修道院"),
    ("wt-mira", "Mira 米拉"),
    ("wt-tia", "Tia 缇娅"),
    ("wt-katherin", "Katherin 凯瑟琳"),
    ("wt-kate", "Kate 凯特"),
    ("wt-claire", "Claire 克莱尔"),
    ("wt-carmen", "Carmen 卡门"),
    ("wt-lucius", "Lucius 卢修斯"),
    ("wt-frisha", "Frisha 弗丽莎"),
    ("wt-arianna", "Arianna 阿里安娜"),
    ("wt-verena", "Verena 维蕾娜"),
    ("wt-rose", "Rose 萝丝"),
    ("wt-emily", "Emily 艾米丽"),
    ("wt-corven", "Corven 科尔文"),
    ("wt-john", "John 约翰"),
    ("wt-melissa", "Melissa 梅丽莎"),
    ("wt-imawyn", "Imawyn 伊玛温"),
    ("wt-lyvia", "Lyvia 莉薇亚"),
    ("wt-maui", "Maui 马乌伊"),
    ("wt-bianca", "Bianca 比安卡"),
    ("wt-gavina", "Gavina 加维娜"),
    ("wt-ugotha", "Ugotha 乌戈萨"),
    ("wt-snikka", "Snikka 斯妮卡"),
    ("wt-natasha", "Natasha 娜塔莎"),
    ("wt-ophilia", "Ophilia 奥菲莉亚"),
    ("wt-anya", "Anya 安雅"),
    ("wt-penny", "Penny 佩妮"),
    ("wt-lilly", "Lilly 莉莉"),
    ("wt-elisabeth", "Elisabeth 伊丽莎白"),
    ("wt-gwen", "Gwen 格温"),
    ("wt-sabrina", "Sabrina 萨布丽娜"),
    ("wt-athia", "Athia 阿西娅"),
    ("wt-bridget", "Bridget 布丽奇特"),
    ("wt-agatha", "Agatha 阿加莎"),
    ("wt-heather", "Heather 希瑟"),
    ("wt-rumah", "鲁玛村"),
    ("wt-raaisha", "Raaisha 拉伊莎"),
    ("wt-hiba", "Hiba 希芭"),
    ("wt-nyra", "Nyra 妮拉"),
    ("wt-ayita", "Ayita 阿伊塔"),
    ("wt-umah", "Umah 乌玛"),
    ("wt-darkholt", "重建达克霍特"),
    ("wt-mansion", "市长宅邸"),
    ("wt-julia", "Julia 茱莉亚"),
    ("wt-liandra", "Liandra 莉安德拉"),
    ("wt-helena", "Helena 海伦娜"),
    ("wt-yasmine", "Yasmine 雅斯敏"),
]


# ---------------------------------------------------------------------------
# 行内 Markdown
# ---------------------------------------------------------------------------

_CODE_RE = re.compile(r"`([^`]+)`")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _norm_image_src(src):
    """将图片路径规范化为相对于站点根目录 index.html 的形式。"""
    src = src.strip()
    src = re.sub(r"^\.?/", "", src)  # ./images -> images, /images -> images
    src = re.sub(r"^(?:markdown/)?images/", "images/", src)  # 统一前缀为 images/
    return src


def _link_repl(m):
    # 链接文本本身可能包含行内标记（例如 **加粗**）
    body = _BOLD_RE.sub(r"<strong>\1</strong>", m.group(1))
    return f'<a href="{m.group(2)}">{body}</a>'


def inline(text):
    """行内 Markdown：代码、图片、链接、加粗。先进行 HTML 转义。"""
    t = html_mod.escape(text, quote=False)
    # 先处理代码片段，使其内容不会被当作其他语法
    t = _CODE_RE.sub(r"<code>\1</code>", t)
    # 图片处理要在链接之前，以免 `![alt](src)` 被链接规则误匹配
    t = _IMG_RE.sub(lambda m: f'<img src="{_norm_image_src(m.group(2))}" 'f'alt="{m.group(1)}" loading="lazy">', t)
    t = _LINK_RE.sub(_link_repl, t)
    t = _BOLD_RE.sub(r"<strong>\1</strong>", t)
    # 清理来源粗糙的文本遗留的孤立标记（未闭合的 ** 等）
    return t.replace("**", "").replace("__", "")


# ---------------------------------------------------------------------------
# 块级 Markdown
# ---------------------------------------------------------------------------

def md_to_html(md_text):
    """将我们的 Markdown 子集转换为 HTML，并正确处理列表嵌套。"""
    lines = md_text.split("\n")
    out = []
    stack = []  # 列表栈：('ol'|'ul', 缩进, 计数器)
    para = []

    def flush_para():
        if para:
            txt = " ".join(x.strip() for x in para)
            if txt:
                out.append(f"<p>{inline(txt)}</p>")
            para.clear()

    def close_all():
        while stack:
            kind = stack.pop()[0]
            out.append(f"</{kind}>")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            close_all()
            level = min(len(m.group(1)) + 1, 4)  # # -> h2（h1 预留给页面标题）
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        # 引用块
        if stripped.startswith(">"):
            flush_para()
            close_all()
            out.append(f"<blockquote>{inline(stripped[1:].strip())}</blockquote>")
            i += 1
            continue
        # 有序列表项（带缩进）
        m = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if m:
            flush_para()
            indent = len(m.group(1))
            num = int(m.group(2))
            # 关闭更深层的列表
            while stack and stack[-1][1] > indent:
                kind = stack.pop()[0]
                out.append(f"</{kind}>")
            # 同缩进上方的非 ol 列表 -> 关闭它
            if stack and stack[-1][1] == indent and stack[-1][0] != "ol":
                kind = stack.pop()[0]
                out.append(f"</{kind}>")
            # 该缩进已有 ol 且编号重置为 1 -> 开启新列表
            if stack and stack[-1][1] == indent and stack[-1][0] == "ol" and num == 1:
                kind = stack.pop()[0]
                out.append(f"</{kind}>")
            if not stack or stack[-1][1] != indent or stack[-1][0] != "ol":
                out.append("<ol>")
                stack.append(("ol", indent, 0))
            out.append(f"<li>{inline(m.group(3))}</li>")
            i += 1
            continue
        # 无序列表项
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            flush_para()
            indent = len(m.group(1))
            while stack and stack[-1][1] > indent:
                kind = stack.pop()[0]
                out.append(f"</{kind}>")
            if stack and stack[-1][1] == indent and stack[-1][0] != "ul":
                kind = stack.pop()[0]
                out.append(f"</{kind}>")
            if not stack or stack[-1][1] != indent or stack[-1][0] != "ul":
                out.append("<ul>")
                stack.append(("ul", indent, 0))
            out.append(f"<li>{inline(m.group(2))}</li>")
            i += 1
            continue
        # 多行 li 续行（列表上下文中的缩进文本）
        if stack and line.startswith(" "):
            indent = len(line) - len(line.lstrip())
            if indent >= stack[-1][1]:
                if out and out[-1].startswith("<li>"):
                    out[-1] = out[-1][:-5] + " " + inline(stripped) + "</li>"
                else:
                    para.append(stripped)
                i += 1
                continue
        # 普通段落（关闭所有已开启的列表）
        close_all()
        para.append(stripped)
        i += 1

    flush_para()
    close_all()
    return "\n".join(out)


def strip_h1(md_text):
    """移除开头的 `# 标题` 行（标题由菜单提供）。"""
    md_text = md_text.lstrip("\ufeff")
    lines = md_text.splitlines()
    if lines and re.match(r"^#\s+", lines[0]):
        lines = lines[1:]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# 静态资源
# ---------------------------------------------------------------------------

def discover_md():
    """根据形如 `03-wt-house.md` 的文件名映射 slug -> 绝对 md 路径。"""
    found = {}
    for name in os.listdir(MD_DIR):
        m = re.fullmatch(r"\d+-([A-Za-z0-9-]+)\.md", name)
        if m:
            found[m.group(1)] = os.path.join(MD_DIR, name)
    return found


def copy_images():
    """将 markdown/images 同步到根目录 images/，返回同步后的文件名列表。

    先清空 images/ 再复制，保证与源目录严格一一对应，不留孤儿文件。
    """
    if not os.path.isdir(IMG_SRC):
        return []
    if os.path.abspath(IMG_SRC) == os.path.abspath(IMG_OUT):
        raise SystemExit("错误：图片源目录与输出目录相同，拒绝清空以免丢失源文件")
    os.makedirs(IMG_OUT, exist_ok=True)
    # 清空输出目录：源里已删除的图不应残留在发布目录
    for name in os.listdir(IMG_OUT):
        path = os.path.join(IMG_OUT, name)
        if os.path.isfile(path):
            os.remove(path)
    copied = []
    for name in os.listdir(IMG_SRC):
        shutil.copy2(os.path.join(IMG_SRC, name), os.path.join(IMG_OUT, name))
        copied.append(name)
    return copied


STYLES = """
:root {
  --bg: #222222; --panel: #1c1f24; --panel-2: #252a31;
  --line: rgba(100, 200, 255, .30); --line-strong: rgba(100, 200, 255, .72);
  --text: #f2f4f7; --dim: #a9b2be; --cyan: #64ffff; --blue: #64c8ff;
  --purple: #c792ea; --gold: #e8c26a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; min-height: 100%; }
body {
  font-family: "Hedvig Letters Sans", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.7;
}
#layout { display: grid; grid-template-columns: 220px minmax(0, 1fr); min-height: 100vh; }
#sidebar {
  height: 100vh; position: sticky; top: 0; overflow-y: auto;
  border-right: 1px solid var(--line); background: #202327; padding: 10px;
}
#sidebar h1 {
  color: var(--cyan); font-size: 15px; line-height: 1.35; font-weight: 700;
  padding: 7px 8px 12px; margin-bottom: 8px; border-bottom: 1px solid var(--line);
}
#sidebar ul { list-style: none; padding: 0; margin: 0; }
#sidebar li + li { margin-top: 2px; }
.section-link {
  width: 100%; border: 0; border-left: 4px solid var(--line); background: transparent;
  color: var(--dim); cursor: pointer; padding: 4px 7px; text-align: left;
  font: inherit; font-size: 14px; line-height: 1.35;
  transition: color .15s, background .15s, border-color .15s;
}
.section-link:hover { color: var(--blue); background: rgba(100, 200, 255, .08); border-left-color: var(--line-strong); }
.section-link.active { color: var(--cyan); background: rgba(100, 200, 255, .12); border-left-color: var(--cyan); }
#workspace { min-width: 0; display: grid; grid-template-rows: 58px minmax(0, 1fr); height: 100vh; }
#page-title {
  display: flex; align-items: center; padding: 5px 18px; border-bottom: 1px solid var(--line);
  background: #202327; color: var(--text); font-size: 28px; font-weight: 700;
}
#content { overflow-y: auto; padding: 20px; }
.walkthrough-card {
  display: none; width: min(1120px, 100%); margin: 0 auto;
  border: 1px solid var(--line); background: var(--panel); box-shadow: 0 16px 38px rgba(0, 0, 0, .28);
}
.walkthrough-card.active { display: block; }
.card-title {
  min-height: 52px; display: flex; align-items: center; padding: 8px 16px;
  border-bottom: 1px solid var(--line); background: var(--panel-2);
}
.card-title h2 { color: var(--cyan); font-size: 24px; line-height: 1.25; }
.card-body { padding: 18px 20px 28px; font-size: 16px; }
h3 { color: var(--purple); font-size: 20px; margin: 24px 0 9px; }
h4 { color: var(--gold); font-size: 17px; margin: 18px 0 8px; }
p { margin: 8px 0; }
ol, ul { margin: 7px 0 14px; padding-left: 27px; }
li { margin: 4px 0; }
ol ol, ul ul, ol ul, ul ol { margin: 4px 0; }
strong { color: #fff; }
a { color: var(--blue); text-decoration: none; }
a:hover { color: var(--cyan); text-decoration: underline; }
img { display: block; max-width: 100%; border: 1px solid var(--line); margin: 12px 0; }
blockquote {
  border-left: 4px solid var(--purple); background: #262b34; color: #c1c8d1;
  padding: 9px 14px; margin: 12px 0;
}
code { background: #303640; padding: 1px 6px; font-size: 13px; }
#footer {
  width: min(1120px, 100%); color: var(--dim); font-size: 13px;
  margin: 24px auto 0; padding: 14px 4px 24px; border-top: 1px solid var(--line);
  text-align: center;
}
@media (max-width: 760px) {
  #layout { display: block; }
  #sidebar { width: 100%; height: auto; max-height: 42vh; position: static; border-right: 0; border-bottom: 1px solid var(--line); }
  #workspace { height: auto; min-height: 58vh; display: block; }
  #page-title { position: sticky; top: 0; z-index: 5; min-height: 50px; font-size: 21px; }
  #content { overflow: visible; padding: 12px; }
  .card-body { padding: 14px; font-size: 15px; }
}
"""

SCRIPTS = """
(function() {
  var links = document.querySelectorAll('.section-link');
  var cards = document.querySelectorAll('.walkthrough-card');
  var title = document.getElementById('page-title');

  function show(id) {
    var target = null;
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].id === id) { target = cards[i]; }
    }
    if (!target) { return; }
    for (var i = 0; i < cards.length; i++) {
      cards[i].classList.toggle('active', cards[i] === target);
      cards[i].setAttribute('aria-hidden', cards[i] === target ? 'false' : 'true');
    }
    for (var i = 0; i < links.length; i++) {
      links[i].classList.toggle('active', links[i].getAttribute('data-target') === id);
      links[i].setAttribute('aria-current', links[i].getAttribute('data-target') === id ? 'page' : 'false');
    }
    title.textContent = target.getAttribute('data-title') || id;
  }

  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function() {
      show(this.getAttribute('data-target'));
      document.getElementById('content').scrollTop = 0;
      document.getElementById('workspace').scrollTop = 0;
    });
  }

  function fromHash() {
    var id = (location.hash || '').replace('#', '');
    if (id) { show(id); }
  }
  window.addEventListener('hashchange', fromHash);

  var first = document.querySelector('.walkthrough-card');
  if (first) {
    first.classList.add('active');
    first.setAttribute('aria-hidden', 'false');
    var firstLink = document.querySelector('.section-link');
    if (firstLink) { firstLink.classList.add('active'); firstLink.setAttribute('aria-current', 'page'); }
  }
  fromHash();
})();
"""


# ---------------------------------------------------------------------------
# 构建
# ---------------------------------------------------------------------------

def build():
    os.makedirs(OUT, exist_ok=True)
    existing_imgs = set(copy_images())

    by_slug = discover_md()
    known = {slug for slug, _ in SECTIONS}
    warnings = []
    for slug in sorted(set(by_slug) - known):
        warnings.append(f"md file not listed in SECTIONS (ignored): {slug}.md")
    for slug, _ in SECTIONS:
        if slug not in by_slug:
            warnings.append(f"SECTIONS entry not found on disk: {slug}")

    nav_items = []
    sections_html = []
    missing_images = []
    idx = 0  # 成功渲染的章节索引
    for slug, title in SECTIONS:
        fp = by_slug.get(slug)
        if not fp:
            continue
        with open(fp, "r", encoding="utf-8") as f:
            md_text = f.read()
        md_text = strip_h1(md_text)
        # 检查该文件引用的每张图片是否都已复制过去
        for _, src in _IMG_RE.findall(md_text):
            norm = _norm_image_src(src)
            if os.path.basename(norm) not in existing_imgs:
                missing_images.append(f"{slug}: {norm}")
        body = md_to_html(md_text)
        first = idx == 0
        nav_items.append(
            f'<li><button class="section-link" type="button" data-target="{slug}"'
            f'{" aria-current=\"page\"" if first else ""}>{html_mod.escape(title)}</button></li>'
        )
        sections_html.append(
            f'<section id="{slug}" class="walkthrough-card" '
            f'data-title="{html_mod.escape(title)}" aria-hidden="{"false" if first else "true"}">'
            f'\n<header class="card-title"><h2>{html_mod.escape(title)}</h2></header>'
            f'\n<div class="card-body">{body}</div>\n</section>'
        )
        idx += 1

    nav = "\n".join(nav_items)
    sections = "\n".join(sections_html)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A Struggle With Sin WalkThrough</title>
<style>
{STYLES}
</style>
</head>
<body>
<div id="layout">
  <nav id="sidebar" aria-label="章节导航">
    <h1>A Struggle With Sin<br>WalkThrough</h1>
    <ul>{nav}</ul>
  </nav>
  <div id="workspace">
    <div id="page-title" aria-live="polite">基本信息</div>
    <main id="content">
      {sections}
      <div id="footer">A Struggle With Sin 中文攻略</div>
    </main>
  </div>
</div>
<script>
{SCRIPTS}
</script>
</body>
</html>
"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Built {os.path.join(OUT, 'index.html')} ({len(page)} bytes)")
    print(f"Images: {len(existing_imgs)}")
    for w in warnings:
        print(f"WARN: {w}")
    for m in missing_images:
        print(f"MISSING IMG: {m}")


if __name__ == "__main__":
    build()
