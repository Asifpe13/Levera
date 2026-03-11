import os
import smtplib
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader
from loguru import logger

# ---------------------------------------------------------------------------
# Hebrew font helpers
# ---------------------------------------------------------------------------

_FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
_FONT_PATH = _FONT_DIR / "Heebo-Regular.ttf"
_FONT_NAME = "Heebo"
_FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/heebo/static/Heebo-Regular.ttf"
)
# Common system paths where a Unicode font with Hebrew glyphs might live
_SYSTEM_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/Library/Fonts/Arial Unicode MS.ttf",
]


def _find_or_download_font() -> str | None:
    """Return a path to a Hebrew-capable TrueType font.

    Priority:
    1. Cached Heebo in backend/fonts/
    2. Common system fonts
    3. Download Heebo from Google Fonts GitHub and cache it
    """
    if _FONT_PATH.exists() and _FONT_PATH.stat().st_size > 10_000:
        return str(_FONT_PATH)

    for path in _SYSTEM_FONT_CANDIDATES:
        if Path(path).exists():
            return path

    try:
        _FONT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading Heebo font for PDF Hebrew support…")
        urllib.request.urlretrieve(_FONT_URL, str(_FONT_PATH))
        if _FONT_PATH.exists() and _FONT_PATH.stat().st_size > 10_000:
            logger.info("Heebo font downloaded successfully")
            return str(_FONT_PATH)
    except Exception as exc:
        logger.warning(f"Could not download Hebrew font: {exc}")

    return None


def _register_hebrew_font() -> str:
    """Register a Hebrew-capable TTFont with ReportLab. Returns the font name to use."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return "Helvetica"

    font_path = _find_or_download_font()
    if not font_path:
        logger.warning("No Hebrew font found — PDF will show squares for Hebrew text")
        return "Helvetica"

    font_name = _FONT_NAME if "Heebo" in font_path else "DejaVuSans"
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name
    except Exception as exc:
        logger.warning(f"Could not register Hebrew font: {exc}")
        return "Helvetica"


def _bidi(text: str) -> str:
    """Apply the Unicode bidi algorithm so Hebrew reads RTL inside a LTR PDF.

    Requires python-bidi==0.4.2 (pure Python).  Falls back to the original
    text if the library is absent or raises, so the PDF always generates.
    """
    try:
        from bidi.algorithm import get_display  # type: ignore[import]
        return get_display(text)
    except ImportError:
        logger.debug("python-bidi not installed — Hebrew PDF text will be LTR")
        return text
    except Exception:
        return text


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def _generate_weekly_report_pdf(
    user_name: str,
    report_date: str,
    properties: list[dict],
    ai_summary: Optional[str] = None,
) -> bytes:
    """Generate a PDF report with clickable links and correct Hebrew rendering."""
    try:
        from reportlab.lib.colors import HexColor
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except ImportError:
        logger.warning("reportlab not installed — PDF report skipped")
        return b""

    font_name = _register_hebrew_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    def _style(name: str, parent_name: str = "Normal", **kwargs) -> ParagraphStyle:
        return ParagraphStyle(
            name,
            parent=styles[parent_name],
            fontName=font_name,
            **kwargs,
        )

    title_style = _style("HTitle", "Heading1", fontSize=18, spaceAfter=10)
    heading_style = _style("HHeading", "Heading2", fontSize=13, spaceAfter=7)
    normal_style = _style("HNormal", fontSize=10, spaceAfter=4)
    link_style = _style(
        "HLink", fontSize=10, textColor=HexColor("#0066cc"), spaceAfter=12
    )

    def p(text: str, style=None) -> Paragraph:
        return Paragraph(_bidi(text), style or normal_style)

    story = []
    story.append(p('דו"ח שבועי — Levera', title_style))
    story.append(p(f"שלום {xml_escape(user_name)}, תאריך: {xml_escape(report_date)}"))
    story.append(Spacer(1, 8 * mm))

    if ai_summary:
        story.append(p("סיכום:", heading_style))
        story.append(p(xml_escape(ai_summary[:500])))
        story.append(Spacer(1, 6 * mm))

    story.append(p("הדירות שנמצאו (עם קישורים למודעות):", heading_style))
    story.append(Spacer(1, 4 * mm))

    for prop in properties:
        city = (prop.get("city") or "").strip() or "—"
        neighborhood = (prop.get("neighborhood") or "").strip()
        location = f"{city}, {neighborhood}" if neighborhood else city
        rooms = prop.get("rooms")
        rooms_str = str(rooms) if rooms is not None else "—"
        price = prop.get("price")
        price_str = f"{price:,.0f} ₪" if price else "—"
        score = prop.get("ai_score")
        score_str = f" — ציון {score}" if score is not None else ""

        story.append(p(f"{xml_escape(location)} — {rooms_str} חדרים — {price_str}{score_str}"))

        listing_url = (prop.get("listing_url") or "").strip()
        if listing_url:
            safe_url = xml_escape(listing_url)
            story.append(
                Paragraph(
                    f'<a href="{safe_url}" color="#0066cc">'
                    + _bidi("צפה במודעה המלאה")
                    + "</a>",
                    link_style,
                )
            )
        else:
            story.append(p("(קישור לא זמין)"))
        story.append(Spacer(1, 3 * mm))

    doc.build(story)
    return buffer.getvalue()


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.sender = os.getenv("EMAIL_SENDER", "")
        self.password = os.getenv("EMAIL_PASSWORD", "")
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachment_filename: Optional[str] = None,
        attachment_bytes: Optional[bytes] = None,
    ) -> bool:
        if not self.sender or not self.password:
            logger.warning("Email credentials not configured — skipping send")
            logger.info(f"Would have sent to {to_email}: {subject}")
            return False

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if attachment_filename and attachment_bytes:
            part = MIMEBase("application", "pdf")
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=("utf-8", "", attachment_filename),
            )
            msg.attach(part)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_property_alert(self, to_email: str, properties: list[dict]) -> bool:
        """Send an instant alert email when matching properties are found."""
        template = self.jinja_env.get_template("email_alert.html")
        html = template.render(properties=properties)
        count = len(properties)
        subject = f"🏠 נמצאו {count} דירות חדשות שמתאימות לך!" if count > 1 else "🏠 נמצאה דירה חדשה שמתאימה לך!"
        return self._send_email(to_email, subject, html)

    def send_weekly_report(self, to_email: str, user_name: str,
                           properties: list[dict], ai_summary: Optional[str] = None) -> bool:
        """Send the Thursday 21:00 weekly digest with HTML body and PDF attachment (with links)."""
        template = self.jinja_env.get_template("weekly_report.html")
        report_date = datetime.now().strftime("%d/%m/%Y")

        prices = [p.get("price", 0) for p in properties if p.get("price")]
        scores = [p.get("ai_score", 0) for p in properties if p.get("ai_score")]

        html = template.render(
            user_name=user_name,
            report_date=report_date,
            total_properties=len(properties),
            avg_price=sum(prices) / len(prices) if prices else 0,
            top_score=max(scores) if scores else 0,
            ai_summary=ai_summary,
            properties=properties,
        )

        pdf_bytes = _generate_weekly_report_pdf(
            user_name=user_name,
            report_date=report_date,
            properties=properties,
            ai_summary=ai_summary,
        )
        attachment_filename = None
        attachment_bytes = None
        if pdf_bytes:
            attachment_filename = f"weekly_report_{report_date.replace('/', '-')}.pdf"
            attachment_bytes = pdf_bytes

        subject = f"📊 דו\"ח שבועי | {len(properties)} דירות נמצאו השבוע"
        return self._send_email(
            to_email,
            subject,
            html,
            attachment_filename=attachment_filename,
            attachment_bytes=attachment_bytes,
        )
