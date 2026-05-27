#!/usr/bin/env python3
"""Apply all xchatbots changes: footer nav, FAQ entries, FAQ schema."""
import os, json, re

BASE = '/home/user/xchatbots'

FAQ_Q = "How does Xchatbots rank and review tools?"
FAQ_A_TEXT = ("We test every tool for a minimum of 7 days using a standardized scoring rubric across "
              "five dimensions including censorship freedom, roleplay depth, and value for money. "
              "Paid placements are always labeled separately from editorial picks. "
              "Full methodology at x-chatbots.com/how-we-review.")
FAQ_A_HTML = (
    'We test every tool for a minimum of 7 days using a standardized scoring rubric across '
    'five dimensions including censorship freedom, roleplay depth, and value for money. '
    'Paid placements are always labeled separately from editorial picks. '
    '<a href="/how-we-review">Full methodology at x-chatbots.com/how-we-review</a>.'
)

H4_ITEM = f'<div class="faq-item"><h4>{FAQ_Q}</h4><p>{FAQ_A_HTML}</p></div>'
H3_CLASS_ITEM = (
    f'<div class="faq-item">\n'
    f'                <h3 class="faq-question">{FAQ_Q}</h3>\n'
    f'                <p class="faq-answer">{FAQ_A_HTML}</p>\n'
    f'            </div>'
)
ACCORDION_ITEM = (
    f'<div class="faq-item">'
    f'<div class="faq-question"><h3>{FAQ_Q}</h3>'
    f'<div class="faq-toggle"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
    f'<path d="M6 9l6 6 6-6"/></svg></div></div>'
    f'<div class="faq-answer"><div class="faq-answer-content">{FAQ_A_HTML}</div></div></div>'
)
FAQ_CARD_ITEM = (
    f'<div class="faq-card">\n'
    f'                <h4>{FAQ_Q}</h4>\n'
    f'                <p>{FAQ_A_HTML}</p>\n'
    f'            </div>'
)

SCHEMA_ENTRY = {
    "@type": "Question",
    "name": FAQ_Q,
    "acceptedAnswer": {"@type": "Answer", "text": FAQ_A_TEXT}
}


def rf(path):
    with open(os.path.join(BASE, path), 'r', encoding='utf-8') as f:
        return f.read()


def wf(path, c):
    with open(os.path.join(BASE, path), 'w', encoding='utf-8') as f:
        f.write(c)


def add_footer_how_we_review(path, link_href='/how-we-review', link_text='How We Review'):
    """Insert How We Review link into Resources footer column."""
    c = rf(path)

    m = re.search(r'<h4>Resources</h4>', c)
    if not m:
        print(f"  WARN [{path}]: no Resources h4 found")
        return

    after = c[m.end():]
    ul_m = re.search(r'</ul>', after)
    if not ul_m:
        print(f"  WARN [{path}]: no </ul> after Resources")
        return

    # Detect inline vs multiline
    before_ul = after[:ul_m.start()]
    last_nl = before_ul.rfind('\n')

    new_li = f'<li><a href="{link_href}">{link_text}</a></li>'

    if last_nl >= 0:
        # Multiline: match the indentation of existing li items
        # Find last li's indentation
        li_m = list(re.finditer(r'\n(\s*)<li>', before_ul))
        if li_m:
            indent = li_m[-1].group(1)
        else:
            # Use whitespace before </ul>
            ul_ws = before_ul[last_nl+1:]
            indent = re.match(r'^\s*', ul_ws).group(0) + '    '
        insert_text = f'\n{indent}{new_li}'
    else:
        insert_text = new_li

    insert_pos = m.end() + ul_m.start()
    new_c = c[:insert_pos] + insert_text + c[insert_pos:]
    wf(path, new_c)
    print(f"  Footer OK: {path}")


def add_faq_schema(path):
    """Add new Question to FAQPage JSON-LD schema."""
    c = rf(path)

    # Find each individual script block (don't cross </script> boundaries)
    script_pat = re.compile(
        r'(<script type="application/ld\+json">)(.*?)(</script>)',
        re.DOTALL
    )

    found = False
    for m in script_pat.finditer(c):
        json_raw = m.group(2).strip()
        if '"FAQPage"' not in json_raw:
            continue

        try:
            data = json.loads(json_raw)
        except json.JSONDecodeError as e:
            print(f"  WARN [{path}]: JSON parse error: {e}")
            return

        if not isinstance(data, dict) or data.get('@type') != 'FAQPage':
            continue

        entities = data.get('mainEntity', [])
        if any(isinstance(q, dict) and q.get('name') == FAQ_Q for q in entities):
            print(f"  SKIP [{path}]: schema entry exists")
            return

        data['mainEntity'].append(SCHEMA_ENTRY)

        multiline = '\n' in json_raw
        new_json = (
            json.dumps(data, indent=2, ensure_ascii=False)
            if multiline else
            json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        )

        c = c[:m.start()] + m.group(1) + new_json + m.group(3) + c[m.end():]
        wf(path, c)
        print(f"  Schema OK: {path}")
        found = True
        break

    if not found:
        print(f"  WARN [{path}]: no FAQPage schema found")


def add_faq_html_before_section_close(path, item_html, container_class='faq-section'):
    """Insert new FAQ item before the closing tag of the faq-section (or container)."""
    c = rf(path)

    open_m = re.search(
        rf'<(div|section)\b[^>]*class="{re.escape(container_class)}[^"]*"',
        c
    )
    if not open_m:
        print(f"  WARN [{path}]: no {container_class} found")
        return

    outer_tag = open_m.group(1)
    pos = open_m.end()
    depth = 1
    close_pos = -1

    while pos < len(c) and depth > 0:
        open_tag = re.search(rf'<{re.escape(outer_tag)}\b', c[pos:])
        close_tag = re.search(rf'</{re.escape(outer_tag)}>', c[pos:])

        if close_tag is None:
            break
        open_abs = pos + open_tag.start() if open_tag else len(c)
        close_abs = pos + close_tag.start()

        if open_abs < close_abs:
            depth += 1
            pos = pos + open_tag.end()
        else:
            depth -= 1
            if depth == 0:
                close_pos = close_abs
                break
            pos = pos + close_tag.end()

    if close_pos == -1:
        print(f"  WARN [{path}]: could not find closing tag for {container_class}")
        return

    # Detect indentation of last faq-item or faq-card
    content_before = c[open_m.end():close_pos]
    item_matches = list(re.finditer(r'\n(\s*)<div class="faq-(?:item|card)"', content_before))
    if item_matches:
        indent = item_matches[-1].group(1)
    else:
        # Fall back: indentation right before closing tag
        nl_pos = c.rfind('\n', 0, close_pos)
        indent = re.match(r'^\s*', c[nl_pos+1:close_pos]).group(0) + '    '

    insert = f'\n{indent}{item_html}'
    new_c = c[:close_pos] + insert + '\n' + c[close_pos:]
    wf(path, new_c)
    print(f"  FAQ HTML OK: {path}")


def add_faq_html_before_grid_close(path, item_html):
    """Insert new FAQ item before faq-grid closing div (for best/ and crushon/janitor pages)."""
    c = rf(path)

    grid_m = re.search(r'<div class="faq-grid">', c)
    if not grid_m:
        print(f"  WARN [{path}]: no faq-grid found")
        return

    pos = grid_m.end()
    depth = 1
    close_pos = -1

    while pos < len(c) and depth > 0:
        next_open = c.find('<div', pos)
        next_close = c.find('</div>', pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                close_pos = next_close
                break
            pos = next_close + 6

    if close_pos == -1:
        print(f"  WARN [{path}]: could not find faq-grid closing tag")
        return

    content_before = c[grid_m.end():close_pos]
    # Look for faq-card or faq-item
    item_matches = list(re.finditer(r'\n(\s*)<div class="faq-(?:card|item)"', content_before))
    indent = item_matches[-1].group(1) if item_matches else '            '

    insert = f'\n{indent}{item_html}'
    new_c = c[:close_pos] + insert + '\n' + c[close_pos:]
    wf(path, new_c)
    print(f"  FAQ HTML OK (grid): {path}")


def add_faq_html_before_last_category_close(path, item_html):
    """For faq.html: insert new accordion item before last faq-category closing div."""
    c = rf(path)

    # Find all faq-category divs
    cat_matches = list(re.finditer(r'<div class="faq-category">', c))
    if not cat_matches:
        print(f"  WARN [{path}]: no faq-category found")
        return

    last_cat = cat_matches[-1]
    pos = last_cat.end()
    depth = 1
    close_pos = -1

    while pos < len(c) and depth > 0:
        next_open = c.find('<div', pos)
        next_close = c.find('</div>', pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                close_pos = next_close
                break
            pos = next_close + 6

    if close_pos == -1:
        print(f"  WARN [{path}]: could not find last faq-category close")
        return

    content_before = c[last_cat.end():close_pos]
    item_matches = list(re.finditer(r'\n(\s*)<div class="faq-item"', content_before))
    indent = item_matches[-1].group(1) if item_matches else '            '

    insert = f'\n{indent}{item_html}'
    new_c = c[:close_pos] + insert + '\n' + c[close_pos:]
    wf(path, new_c)
    print(f"  FAQ HTML OK (category): {path}")


# ===== APPLY CHANGES =====

# Files with standard h4/p FAQ format + FAQPage schema
std_h4_files = [
    'virtual-girlfriend.html',
    'nsfw-chat.html',
    'nsfw-image-generation.html',
    'nsfw-video-generation.html',
    'roleplay.html',
    'alternatives/character-ai-alternatives.html',
    'alternatives/crushon-ai-alternatives.html',
    'alternatives/janitor-ai-alternatives.html',
    'alternatives/perchance-ai-alternatives.html',
]

# Files with h3.faq-question format + FAQPage schema
h3_class_files = [
    'what-is/uncensored-ai.html',
    'alternatives/spicychat-alternatives.html',
]

# All pages that need footer update (all except how-we-review.html which already has it)
all_pages = [
    'index.html',
    'about.html',
    'privacy.html',
    'terms.html',
    'virtual-girlfriend.html',
    'nsfw-chat.html',
    'nsfw-image-generation.html',
    'nsfw-video-generation.html',
    'roleplay.html',
    'faq.html',
    'categories.html',
    'advertise.html',
    'submit.html',
    'contact.html',
    'best/nsfw-ai-chatbots.html',
    'best/undress-ai.html',
    'what-is/uncensored-ai.html',
    'alternatives/character-ai-alternatives.html',
    'alternatives/crushon-ai-alternatives.html',
    'alternatives/janitor-ai-alternatives.html',
    'alternatives/perchance-ai-alternatives.html',
    'alternatives/spicychat-alternatives.html',
]

print("=== FOOTER UPDATES ===")
for p in all_pages:
    href = 'how-we-review.html' if p in ('index.html', 'about.html', 'privacy.html', 'terms.html') else '/how-we-review'
    add_footer_how_we_review(p, link_href=href)

print("\n=== FAQ HTML UPDATES ===")
# Standard h4/p pages with faq-section class (most pages)
std_h4_section_files = [
    'virtual-girlfriend.html',
    'nsfw-chat.html',
    'nsfw-image-generation.html',
    'nsfw-video-generation.html',
    'roleplay.html',
    'alternatives/character-ai-alternatives.html',
    'alternatives/perchance-ai-alternatives.html',
]
for p in std_h4_section_files:
    add_faq_html_before_section_close(p, H4_ITEM)

# crushon and janitor use faq-grid (not faq-section)
add_faq_html_before_grid_close('alternatives/crushon-ai-alternatives.html', H4_ITEM)
add_faq_html_before_grid_close('alternatives/janitor-ai-alternatives.html', H4_ITEM)

# h3.faq-question pages
for p in h3_class_files:
    add_faq_html_before_section_close(p, H3_CLASS_ITEM)

# best/ pages (faq-card inside faq-grid)
add_faq_html_before_grid_close('best/nsfw-ai-chatbots.html', FAQ_CARD_ITEM)
add_faq_html_before_grid_close('best/undress-ai.html', FAQ_CARD_ITEM)

# faq.html accordion
add_faq_html_before_last_category_close('faq.html', ACCORDION_ITEM)

print("\n=== SCHEMA UPDATES ===")
all_schema_files = std_h4_section_files + [
    'alternatives/crushon-ai-alternatives.html',
    'alternatives/janitor-ai-alternatives.html',
] + h3_class_files + ['best/nsfw-ai-chatbots.html', 'best/undress-ai.html']
for p in all_schema_files:
    add_faq_schema(p)

print("\nDone!")
