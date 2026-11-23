"""Receipt for one payment (or refund): data for the app and a one-page PDF."""
import io

from django.db.models import Q
from django.utils import timezone

from .models import Payment


def _f(v):
    return round(float(v or 0), 2)


def receipt_data(p):
    i = p.invoice
    clinic = i.clinic
    # invoice position right after this payment (payments/refunds up to and including it)
    upto = Payment.objects.filter(invoice=i).filter(
        Q(paid_at__lt=p.paid_at) | Q(paid_at=p.paid_at, id__lte=p.id))
    paid = sum((x.amount for x in upto if x.kind == 'payment'), 0)
    refunded = sum((x.amount for x in upto if x.kind == 'refund'), 0)
    credited = sum((x.amount for x in upto if x.kind == 'refund' and x.adjusts_invoice), 0)
    balance_after = max(i.total - credited - (paid - refunded), 0) if i.status != 'void' else 0
    appt = i.appointment if i.appointment_id else None
    is_refund = p.kind == 'refund'
    return {
        'type':           'refund' if is_refund else 'payment',
        'title':          'Refund receipt' if is_refund else 'Payment receipt',
        'receipt_number': p.receipt_number,
        'payment_id':     p.id,
        'date':           timezone.localtime(p.paid_at).strftime('%Y-%m-%d %H:%M'),
        'clinic': {
            'name':    clinic.legal_name or clinic.name,
            'tax_id':  clinic.tax_id,
            'address': clinic.billing_address,
            'phone':   clinic.billing_phone,
            'email':   clinic.billing_email,
        },
        'patient': {'id': i.patient.patient_id, 'name': i.patient.name, 'phone': i.patient.phone,
                    'email': i.patient.email or ''} if i.patient_id and i.patient else None,
        'invoice': {'id': i.id, 'invoice_number': i.invoice_number, 'issue_date': str(i.issue_date),
                    'total': _f(i.total), 'tax_amount': _f(i.tax_amount)},
        'appointment': {'id': appt.id, 'date_time': timezone.localtime(appt.date_time).strftime('%Y-%m-%d %H:%M')
                        if appt.date_time else None,
                        'treatment': appt.treatment.name if appt.treatment_id and appt.treatment else None}
                       if appt else None,
        'amount':         _f(p.amount),
        'currency':       'eur',
        'method':         p.method,
        'method_label':   dict(Payment.METHOD_CHOICES).get(p.method, p.method),
        'reference':      p.reference,
        'reason':         p.reason if is_refund else '',
        'refund_of_receipt': p.refund_of.receipt_number if is_refund and p.refund_of_id else None,
        'received_by':    (p.created_by.username or p.created_by.email.split('@')[0]) if p.created_by_id else None,
        'paid_to_date':   _f(paid - refunded),
        'balance_after':  _f(balance_after),
    }


def receipt_pdf(d):
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    w, h = A5
    x, y = 14 * mm, h - 18 * mm

    def line(text, size=9, bold=False, dy=5 * mm, right=None):
        nonlocal y
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        if right is not None:
            c.drawRightString(w - 14 * mm, y, str(right))
        c.drawString(x, y, str(text))
        y -= dy

    cl = d['clinic']
    line(cl['name'] or 'Clinic', 13, True, 6 * mm)
    for t in (cl['tax_id'] and f"NIF/CIF: {cl['tax_id']}", cl['address'], cl['phone'], cl['email']):
        if t:
            for part in str(t).splitlines():
                line(part, 8, dy=4 * mm)
    y -= 4 * mm
    line(d['title'], 14, True, 7 * mm)
    line('Receipt no.', 9, right=d['receipt_number'] or '-')
    line('Date', 9, right=d['date'])
    line('Invoice', 9, right=d['invoice']['invoice_number'])
    if d['refund_of_receipt']:
        line('Refund of receipt', 9, right=d['refund_of_receipt'])
    y -= 2 * mm
    if d['patient']:
        line('Patient', 9, right=f"{d['patient']['name']} ({d['patient']['id']})")
    if d['appointment'] and d['appointment']['treatment']:
        line('Treatment', 9, right=f"{d['appointment']['treatment']} · {d['appointment']['date_time'] or ''}")
    y -= 3 * mm
    c.line(x, y + 2 * mm, w - 14 * mm, y + 2 * mm)
    y -= 2 * mm
    sign = '-' if d['type'] == 'refund' else ''
    line('Amount ' + ('refunded' if d['type'] == 'refund' else 'received'), 12, True, 7 * mm,
         right=f"{sign}€{d['amount']:.2f}")
    line('Method', 9, right=d['method_label'])
    if d['reference']:
        line('Reference', 9, right=d['reference'])
    if d['reason']:
        line('Reason', 9, right=d['reason'][:60])
    y -= 3 * mm
    line('Invoice total', 9, right=f"€{d['invoice']['total']:.2f}")
    line('Paid to date', 9, right=f"€{d['paid_to_date']:.2f}")
    line('Balance due', 9, True, right=f"€{d['balance_after']:.2f}")
    y -= 4 * mm
    if d['received_by']:
        line(f"Recorded by {d['received_by']}", 8)
    line('Prices include tax. This receipt confirms a payment; the invoice is the tax document.', 7)
    c.showPage()
    c.save()
    return buf.getvalue()
