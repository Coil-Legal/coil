"""Issues #98 and #99, from Bot 1's accessibility batch (axe-core 4.10.3) on testfirm.

#98: axe flagged color-contrast (serious) on the status badges that use --ok/--warn text
on their tinted backgrounds, and on the --muted weekday headers on the calendar, all below
4.5:1; and link-in-text-block (serious) on links sitting next to plain text in the same
block (the client link under a matter title, invoice links in dashboard rows, contact
links in the contacts list, the templates link on the new-matter form) with no non-color
cue. Fixed by darkening --ok/--warn/--muted until every pairing clears 4.5:1, and by
underlining links inside .muted text and inside table cells (excluding .btn-styled links,
which are not running text).

#99: at a 640px window or 200% zoom in a 1280px window, the dashboard and the matters list
scrolled sideways. Root cause, confirmed locally with Playwright against a seeded
instance: a plain HTML <table> cannot shrink below the sum of its columns' minimum
content widths, so a many-column table (dashboard's recent matters, the matters list)
forces its .card, and the whole page, wider than the viewport. Fixed by giving .card
overflow-x:auto so an oversized table scrolls inside its own card instead of pushing the
page wide. Confirmed before the fix the matters list reached 786px of document
scrollWidth in a 640px viewport (a 739px-wide table inside a 640px-wide .card); after the
fix scrollWidth stays at 640 and the table scrolls inside the card.

Run: .venv/bin/python -m pytest tests/test_accessibility_contrast_reflow.py -q
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(ROOT, "app", "static", "app.css")


def _css():
    with open(CSS_PATH) as f:
        return f.read()


def _hex_var(css, name):
    m = re.search(r"--" + name + r":(#[0-9a-fA-F]{6})", css)
    assert m, f"--{name} not found in app.css"
    return m.group(1)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexcolor):
    hexcolor = hexcolor.lstrip("#")
    r, g, b = int(hexcolor[0:2], 16), int(hexcolor[2:4], 16), int(hexcolor[4:6], 16)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _contrast(c1, c2):
    l1, l2 = _luminance(c1), _luminance(c2)
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


def test_ok_warn_muted_clear_wcag_aa_on_their_badge_and_calendar_backgrounds():
    css = _css()
    ok, warn, muted = _hex_var(css, "ok"), _hex_var(css, "warn"), _hex_var(css, "muted")
    # .badge.open/.paid/.signed/.clear/.converted background
    assert _contrast(ok, "#dff3e8") >= 4.5
    # .badge.draft/.waived/.unresolved background (also .draft.score-badge)
    assert _contrast(warn, "#f4e9d2") >= 4.5
    # .cal .dow weekday header background in calendar/index.html
    assert _contrast(muted, "#eef1f4") >= 4.5


def test_links_in_running_text_get_a_non_color_cue():
    css = _css()
    assert re.search(r"\.muted a[^{]*\{[^}]*text-decoration:underline", css)
    assert re.search(r"td a:not\(\.btn\)[^{]*\{[^}]*text-decoration:underline", css)


def test_card_scrolls_its_own_overflow_instead_of_widening_the_page():
    css = _css()
    assert re.search(r"\.card\{[^}]*overflow-x:auto", css)


def test_links_in_empty_states_and_definition_lists_are_underlined():
    """Bot 1's final rescan (cases 1457, 1460): the "add splits" link in a matter's empty
    fee-split state and the conflict-check link on a lead's details list were still told
    apart by colour only."""
    css = _css()
    assert re.search(r"\.empty a[^{]*\{[^}]*text-decoration:underline", css)
    assert re.search(r"dd a[^{]*\{[^}]*text-decoration:underline", css)
