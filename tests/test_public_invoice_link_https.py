"""Coil QA #149: the public invoice page's {link} substitution printed http:// in production,
while the PDF's own {link} (same invoice, same template) correctly printed https://.

`invoices/public.html` built the link with `url_for(..., _external=True)`, which derives its
scheme from the current request as Flask sees it. Behind Traefik (TLS terminated at the proxy,
plain HTTP to the container, no ProxyFix), that is always http. The PDF path never had this bug
because it already builds the link with `public_url()`, which reads the app's own BASE_URL
config instead of guessing the scheme from the request. The fix points the public page at the
same `public_url()` helper.

Run: .venv/bin/python -m pytest tests/test_public_invoice_link_https.py -q
"""
from tests.test_phase1_independent import app, staff  # noqa: F401


def test_public_page_link_substitution_uses_base_url_scheme_not_request_scheme(app, monkeypatch):
    monkeypatch.setitem(app.config, "BASE_URL", "https://testfirm.coil.legal")
    c, csrf = staff(app)
    with app.app_context():
        from app.extensions import db
        from app.models import Firm, Matter, Invoice

        firm = Firm.get()
        firm.invoice_payment_instructions = "Pay via {link}. QA #149 test."
        matter = Matter.query.filter_by(number="M-PHASE1").one()
        inv = Invoice(client_id=matter.client_id, matter_id=matter.id, number="QA-149",
                      status="sent", currency="USD", subtotal_cents=10000, total_cents=10000)
        db.session.add(inv)
        db.session.commit()
        token = inv.public_token
        inv_id = inv.id

    r = c.get(f"/p/{token}")
    assert r.status_code == 200
    html = r.data.decode()
    assert f"Pay via https://testfirm.coil.legal/p/{token}. QA #149 test." in html
    assert "http://testfirm.coil.legal" not in html

    r = c.get(f"/invoices/{inv_id}/pdf")
    assert r.status_code == 200
