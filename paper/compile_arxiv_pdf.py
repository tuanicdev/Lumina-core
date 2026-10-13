#!/usr/bin/env python3
"""
Lumina Sovereign Academic PDF Compiler - ArXiv / APA 7th Edition
Compiles LUMINA_PAPER_ARXIV.md into LUMINA_PAPER_ARXIV_APA7.pdf
with full GFM table support, typographic polish, clean math rendering, and running headers.
"""

import os
import re
import fitz
from markdown_it import MarkdownIt

def build_pdf(md_path="LUMINA_PAPER_ARXIV.md", out_pdf="LUMINA_PAPER_ARXIV_APA7.pdf"):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file '{md_path}' not found.")

    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Escape literal backslash-dollar e.g. \$4 -> &dollar;4
    text = text.replace(r'\$', '&dollar;')

    # 2. Protect code blocks so math parsing doesn't touch code
    code_blocks = []
    def save_fenced(m):
        idx = len(code_blocks)
        code_blocks.append(m.group(0))
        return f'\n\n@@FENCED_CODE_{idx}@@\n\n'
    text = re.sub(r'```.*?```', save_fenced, text, flags=re.DOTALL)

    inline_codes = []
    def save_inline_code(m):
        idx = len(inline_codes)
        inline_codes.append(m.group(0))
        return f'@@INLINE_CODE_{idx}@@'
    text = re.sub(r'`[^`\n]+`', save_inline_code, text)

    # 3. Extract block equations: $$ ... $$ -> @@BLOCK_EQ_{idx}@@
    block_eqs = []
    def save_block_eq(m):
        idx = len(block_eqs)
        eq_clean = clean_latex(m.group(1).strip())
        block_eqs.append(f'<div class="equation"><i>{eq_clean}</i></div>')
        return f'\n\n@@BLOCK_EQ_{idx}@@\n\n'
    text = re.sub(r'\$\$(.*?)\$\$', save_block_eq, text, flags=re.DOTALL)

    # 4. Extract inline math: $...$ -> @@INLINE_EQ_{idx}@@
    inline_eqs = []
    def save_inline_eq(m):
        idx = len(inline_eqs)
        eq_clean = clean_latex(m.group(1).strip())
        inline_eqs.append(f'<span class="math"><i>{eq_clean}</i></span>')
        return f'@@INLINE_EQ_{idx}@@'
    text = re.sub(r'(?<![\$\w])\$([^\$\n\r]{1,160}?)\$(?![\$\w])', save_inline_eq, text)

    # 5. Restore code blocks and inline code
    for idx, cb in enumerate(code_blocks):
        text = text.replace(f'@@FENCED_CODE_{idx}@@', cb)
    for idx, ic in enumerate(inline_codes):
        text = text.replace(f'@@INLINE_CODE_{idx}@@', ic)

    # 6. Page breaks on standalone '---'
    text = re.sub(r'(?m)^---\s*$', '\n\n<div class="page-break"></div>\n\n', text)

    # 7. Ensure blank lines before and after tables
    text = re.sub(r'([^\n])\n(\|[^\n]+\|)\n(\|[\s:\-\|]+\|)', r'\1\n\n\2\n\3', text)

    # 8. Render markdown
    md = MarkdownIt("gfm-like").disable("linkify")
    html = md.render(text)

    # 9. Re-inject block and inline equations
    for idx, eq_html in enumerate(block_eqs):
        html = html.replace(f'<p>@@BLOCK_EQ_{idx}@@</p>', eq_html)
        html = html.replace(f'@@BLOCK_EQ_{idx}@@', eq_html)
    for idx, eq_html in enumerate(inline_eqs):
        html = html.replace(f'@@INLINE_EQ_{idx}@@', eq_html)

    # 10. Restore &dollar; as $
    html = html.replace('&dollar;', '$')

    # Wrap in complete HTML
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body>
{html}
</body>
</html>"""

    css = """
    body {
        font-family: "Times-Roman", serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #111111;
        text-align: justify;
    }
    h1 {
        font-family: "Times-Bold", serif;
        font-size: 16pt;
        line-height: 1.25;
        text-align: center;
        margin-top: 14pt;
        margin-bottom: 12pt;
    }
    h2 {
        font-family: "Times-Bold", serif;
        font-size: 13pt;
        line-height: 1.2;
        margin-top: 16pt;
        margin-bottom: 6pt;
        border-bottom: 1px solid #222;
        padding-bottom: 2pt;
    }
    h3 {
        font-family: "Times-Bold", serif;
        font-size: 11pt;
        line-height: 1.2;
        margin-top: 12pt;
        margin-bottom: 4pt;
    }
    h4 {
        font-family: "Times-Italic", serif;
        font-size: 10pt;
        line-height: 1.2;
        margin-top: 10pt;
        margin-bottom: 3pt;
    }
    p {
        margin-top: 3pt;
        margin-bottom: 6pt;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10pt;
        margin-bottom: 10pt;
        font-size: 8.5pt;
        line-height: 1.2;
    }
    th {
        border-top: 1.5px solid #111;
        border-bottom: 1.5px solid #111;
        font-family: "Times-Bold", serif;
        padding: 4pt 3pt;
        background-color: #f8f8f8;
        text-align: left;
    }
    td {
        border-bottom: 0.5px solid #ddd;
        padding: 3.5pt 3pt;
        vertical-align: top;
    }
    tr:last-child td {
        border-bottom: 1.5px solid #111;
    }
    pre {
        background-color: #f7f7f8;
        border: 0.5px solid #ccc;
        border-radius: 2px;
        padding: 6pt;
        font-family: "Courier", monospace;
        font-size: 8pt;
        line-height: 1.2;
        margin-top: 6pt;
        margin-bottom: 8pt;
    }
    code {
        font-family: "Courier", monospace;
        font-size: 8pt;
        background-color: #eee;
        padding: 1px 2px;
    }
    .equation {
        text-align: center;
        font-size: 10pt;
        margin-top: 8pt;
        margin-bottom: 8pt;
    }
    div.page-break {
        break-after: page;
        height: 0;
        margin: 0;
        padding: 0;
    }
    """

    paper_rect = fitz.paper_rect("letter")
    margins = (60, 50, -60, -50)
    where = paper_rect + margins

    temp_pdf = "temp_clean_draft.pdf"
    writer = fitz.DocumentWriter(temp_pdf)
    story = fitz.Story(html=full_html, user_css=css)

    page_count = 0
    more = 1
    while more:
        page_count += 1
        device = writer.begin_page(paper_rect)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()

    print(f"[*] Initial layout created {page_count} pages. Applying headers...")
    doc = fitz.open(temp_pdf)
    header_text = "LUMINA: NEURO-SYMBOLIC TRANSDUCTION & DETERMINISTIC VERIFICATION"
    for i in range(len(doc)):
        p = doc[i]
        w = p.rect.width
        num_str = str(i + 1)
        if i > 0:
            p.insert_textbox(
                fitz.Rect(60, 24, w - 100, 40),
                header_text,
                fontsize=8,
                fontname="Times-Roman",
                align=fitz.TEXT_ALIGN_LEFT
            )
        p.insert_textbox(
            fitz.Rect(w - 100, 24, w - 60, 40),
            num_str,
            fontsize=8.5,
            fontname="Times-Roman",
            align=fitz.TEXT_ALIGN_RIGHT
        )
        del p

    doc.save(out_pdf, incremental=False, encryption=0)
    doc.close()
    del doc
    if os.path.exists(temp_pdf):
        try:
            os.remove(temp_pdf)
        except Exception:
            pass
    print(f"[+] Output written to {out_pdf} with {page_count} pages.")

def clean_latex(text):
    text = text.strip()
    
    # 1. Specific LaTeX symbol macros (longest/most specific first)
    text = re.sub(r'\\pmod\{([^{}]+)\}', r' (mod \1)', text)
    text = text.replace(r"\infty", "&infin;")
    text = text.replace(r"\notin", "&notin;")
    text = text.replace(r"\in", "&isin;")
    text = text.replace(r"\approx", "&asymp;")
    text = text.replace(r"\equiv", "&equiv;")
    text = text.replace(r"\implies", "&rArr;")
    text = text.replace(r"\rightarrow", "&rarr;")
    text = text.replace(r"\to", "&rarr;")
    text = text.replace(r"\ll", "&Lt;")
    text = text.replace(r"\gg", "&Gt;")
    text = text.replace(r"\le", "&le;")
    text = text.replace(r"\ge", "&ge;")
    text = text.replace(r"\ne", "&ne;")
    text = text.replace(r"\pm", "&plusmn;")
    text = text.replace(r"\times", "&times;")
    text = text.replace(r"\cdot", "&middot;")
    text = text.replace(r"\prod", "&prod;")
    text = text.replace(r"\sum", "&sum;")
    text = text.replace(r"\int", "&int;")
    text = text.replace(r"\forall", "&forall;")
    text = text.replace(r"\exists", "&exist;")
    text = text.replace(r"\sim", "~")
    text = text.replace(r"\mid", "|")
    text = text.replace(r"\|", "|")
    
    # Greek letters
    text = text.replace(r"\alpha", "&alpha;")
    text = text.replace(r"\beta", "&beta;")
    text = text.replace(r"\gamma", "&gamma;")
    text = text.replace(r"\delta", "&delta;")
    text = text.replace(r"\epsilon", "&epsilon;")
    text = text.replace(r"\theta", "&theta;")
    text = text.replace(r"\Theta", "&Theta;")
    text = text.replace(r"\lambda", "&lambda;")
    text = text.replace(r"\mu", "&mu;")
    text = text.replace(r"\pi", "&pi;")
    text = text.replace(r"\sigma", "&sigma;")
    text = text.replace(r"\tau", "&tau;")
    text = text.replace(r"\chi", "&chi;")
    text = text.replace(r"\Psi", "&Psi;")
    
    # Special constructs
    text = text.replace(r"\lfloor", "&lfloor;")
    text = text.replace(r"\rfloor", "&rfloor;")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\quad", "&nbsp;&nbsp;")
    text = text.replace(r"\\", "<br/>")

    # Fractions and square roots
    while re.search(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', text):
        text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1 / \2)', text)
    while re.search(r'\\sqrt\{([^{}]+)\}', text):
        text = re.sub(r'\\sqrt\{([^{}]+)\}', r'&radic;(\1)', text)

    # Escape literal < and > BEFORE introducing HTML tags!
    text = text.replace('<', '&lt;').replace('>', '&gt;')

    # Blackboard / Mathcal
    text = text.replace(r"\mathbb{Q}", "<b>Q</b>")
    text = text.replace(r"\mathbb{R}", "<b>R</b>")
    text = text.replace(r"\mathbb{N}", "<b>N</b>")
    text = text.replace(r"\mathbb{Z}", "<b>Z</b>")
    text = text.replace(r"\mathcal{O}", "<b>O</b>")

    # Innermost \text{...} first:
    while re.search(r'\\text\{([^{}]+)\}', text):
        text = re.sub(r'\\text\{([^{}]+)\}', r'<span style="font-style:normal;">\1</span>', text)

    # Then \mathbf{...}:
    while re.search(r'\\mathbf\{([^{}]+)\}', text):
        text = re.sub(r'\\mathbf\{([^{}]+)\}', r'<b>\1</b>', text)

    # Subscripts and superscripts with braces:
    while re.search(r'_\{([^{}]+)\}', text):
        text = re.sub(r'_\{([^{}]+)\}', r'<sub>\1</sub>', text)
    while re.search(r'\^\{([^{}]+)\}', text):
        text = re.sub(r'\^\{([^{}]+)\}', r'<sup>\1</sup>', text)

    # Clean leftover backslashed commands e.g. \lim -> lim
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)

    # Single-char subscripts and superscripts outside tags
    tokens = re.split(r'(<[^>]+>)', text)
    for idx, tok in enumerate(tokens):
        if not (tok.startswith('<') and tok.endswith('>')):
            tok = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', tok)
            tok = re.sub(r'\^([a-zA-Z0-9])', r'<sup>\1</sup>', tok)
            tok = tok.replace('{', '').replace('}', '')
            tokens[idx] = tok
    text = ''.join(tokens)
    return text

if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "LUMINA_PAPER_ARXIV.md"
    dst = sys.argv[2] if len(sys.argv) > 2 else "LUMINA_PAPER_ARXIV_APA7.pdf"
    build_pdf(src, dst)
