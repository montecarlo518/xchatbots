#!/usr/bin/env python3
"""
Fix heading hierarchy (h1→h3 skip, h2→h4 skip) across 6 xchatbots HTML files.
Run from the repo root: python3 fix_headings.py

Files fixed:
  alternatives/perchance-ai-alternatives.html
  best/ai-hentai-anime-generators.html
  best/nsfw-ai-chatbots.html
  nsfw-chat.html
  roleplay.html
  virtual-girlfriend.html
"""

import re, os

FILES = [
    "alternatives/perchance-ai-alternatives.html",
    "best/ai-hentai-anime-generators.html",
    "best/nsfw-ai-chatbots.html",
    "nsfw-chat.html",
    "roleplay.html",
    "virtual-girlfriend.html",
]

def fix_file(path):
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original = html

    # ── Fix 1 ──────────────────────────────────────────────────────────────
    # key-takeaways h3 → h2  (h1 → h3 skips h2)
    # The <h3> inside .key-takeaways is the first heading after <h1>, so it must be h2.
    # Pattern: <h3 ...>...</h3> immediately inside .key-takeaways div
    html = re.sub(
        r'(<div[^>]*class="[^"]*key-takeaways[^"]*"[^>]*>.*?)<h3([^>]*)>(.*?)</h3>',
        lambda m: m.group(1) + '<h2' + m.group(2) + '>' + m.group(3) + '</h2>',
        html, flags=re.DOTALL
    )
    # Also update the CSS selector inside <style> to match h2 instead of h3
    html = html.replace(
        '.key-takeaways h3{',
        '.key-takeaways h2{'
    )
    html = html.replace(
        '.key-takeaways h3 {',
        '.key-takeaways h2 {'
    )

    # ── Fix 2 ──────────────────────────────────────────────────────────────
    # faq-item h4 / faq-card h4 → h3  (h2 FAQ section → h4 skips h3)
    # These FAQ heading elements sit directly under an h2 FAQ section header.
    html = re.sub(
        r'(<div[^>]*class="[^"]*faq-(?:item|card)[^"]*"[^>]*>.*?)<h4([^>]*)>(.*?)</h4>',
        lambda m: m.group(1) + '<h3' + m.group(2) + '>' + m.group(3) + '</h3>',
        html, flags=re.DOTALL
    )
    # Update CSS selector
    html = html.replace('.faq-item h4{', '.faq-item h3{')
    html = html.replace('.faq-item h4 {', '.faq-item h3 {')
    html = html.replace('.faq-card h4{', '.faq-card h3{')
    html = html.replace('.faq-card h4 {', '.faq-card h3 {')

    # ── Fix 3 (ai-hentai only) ─────────────────────────────────────────────
    # Split paragraphs longer than ~120 words into two paragraphs.
    # We do this only for the content-section paragraphs (not inside tool cards).
    if "ai-hentai" in path:
        def split_long_para(m):
            tag_open = m.group(1)
            content = m.group(2)
            words = content.split()
            if len(words) <= 100:
                return m.group(0)
            # Find a split point around word 60–80 at a sentence boundary
            mid = len(words) // 2
            # Walk backward from mid to find a sentence end
            split_at = mid
            for i in range(mid, max(mid - 25, 0), -1):
                if words[i].endswith(('.', '!', '?', '."', '!"', '?\"')):
                    split_at = i + 1
                    break
            first = ' '.join(words[:split_at])
            second = ' '.join(words[split_at:])
            return f'<p>{first}</p>\n            <p>{second}</p>'

        html = re.sub(
            r'<p>((?:\S+\s+){100,})</p>',
            split_long_para,
            html,
            flags=re.DOTALL
        )

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  FIXED: {path}")
    else:
        print(f"  NO CHANGE: {path} (patterns not found — check manually)")


if __name__ == "__main__":
    for path in FILES:
        print(f"Processing {path}...")
        fix_file(path)
    print("\nDone. Commit and deploy.")
