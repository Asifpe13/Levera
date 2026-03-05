import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader
from loguru import logger


def _generate_weekly_report_pdf(
    user_name: str,
    report_date: str,
    properties: list[dict],
    ai_summary: Optional[str] = None,
) -> bytes:
    """Generate a PDF report with clickable links to each property."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    except ImportError:
        logger.warning("reportlab not installed — PDF report skipped")
        return b""

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
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8,
    )
    normal_style = styles["Normal"]
    link_style = ParagraphStyle(
        "Link",
        parent=normal_style,
        textColor="blue",
        spaceAfter=14,
    )

    story = []
    story.append(Paragraph("דו\"ח שבועי — סוכן הנדל\"ן", title_style))
    story.append(Paragraph(f"שלום {xml_escape(user_name)}, תאריך: {xml_escape(report_date)}", normal_style))
    story.append(Spacer(1, 8 * mm))

    if ai_summary:
        story.append(Paragraph("סיכום:", heading_style))
        story.append(Paragraph(xml_escape(ai_summary[:500]), normal_style))
        story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("הדירות שנמצאו (עם קישורים למודעות):", heading_style))
    story.append(Spacer(1, 4 * mm))

    for i, prop in enumerate(properties):
        city = (prop.get("city") or "").strip() or "—"
        neighborhood = (prop.get("neighborhood") or "").strip()
        location = f"{city}, {neighborhood}" if neighborhood else city
        rooms = prop.get("rooms")
        rooms_str = str(rooms) if rooms is not None else "—"
        price = prop.get("price")
        price_str = f"{price:,.0f} ₪" if price else "—"
        score = prop.get("ai_score")
        score_str = f"ציון {score}" if score is not None else ""

        line = f"{xml_escape(location)} — {rooms_str} חדרים — {price_str}"
        if score_str:
            line += f" — {score_str}"
        story.append(Paragraph(line, normal_style))

        listing_url = (prop.get("listing_url") or "").strip()
        if listing_url:
            safe_url = xml_escape(listing_url)
            story.append(
                Paragraph(
                    f'<a href="{safe_url}" color="blue">צפה במודעה המלאה (קישור למודעה)</a>',
                    link_style,
                )
            )
        else:
            story.append(Paragraph("(קישור לא זמין)", normal_style))
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
