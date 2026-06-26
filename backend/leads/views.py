import os
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Lead
from .serializers import LeadCreateSerializer, LeadSerializer

# Transparent 1x1 GIF byte data
PIXEL_GIF_DATA = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'


class LeadListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lead.objects.all().order_by('-submission_time')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LeadCreateSerializer
        return LeadSerializer

    def classify_lead(self, requirement):
        req_lower = requirement.lower()
        if any(word in req_lower for word in ['chatbot', 'automation', 'ai', 'agent', 'workflow']):
            return 'AI Automation', 'High'
        elif any(word in req_lower for word in ['website', 'web', 'landing page', 'ecommerce']):
            return 'Web Development', 'Medium'
        elif any(word in req_lower for word in ['marketing', 'leads', 'email', 'campaign']):
            return 'Marketing Automation', 'Medium'
        else:
            return 'General Inquiry', 'Low'

    # ------------------------------------------------------------------ #
    #  Background email helper – runs in a daemon thread                  #
    # ------------------------------------------------------------------ #
    def _send_email_in_background(self, lead_id):
        """Send email asynchronously. Never raises – logs everything."""
        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            print(f"[EMAIL THREAD] Lead id={lead_id} not found. Aborting.")
            return

        # ---- SMTP debug info (safe for logs) ----
        print("=" * 50)
        print("SMTP EMAIL STARTED")
        print(f"  SMTP EMAIL TO: {lead.email}")
        print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        print(f"  EMAIL_TIMEOUT: {settings.EMAIL_TIMEOUT}")
        print(f"  EMAIL_HOST_USER EXISTS: {bool(settings.EMAIL_HOST_USER)}")
        print(f"  EMAIL_HOST_PASSWORD EXISTS: {bool(settings.EMAIL_HOST_PASSWORD)}")
        print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print("=" * 50)

        from_email = settings.DEFAULT_FROM_EMAIL or 'yatins113@gmail.com'
        backend_url = os.environ.get('BACKEND_URL', 'https://admexo-assignment.onrender.com')

        tracking_pixel = (
            f'<img src="{backend_url}/api/track/open/{lead.tracking_id}/" '
            f'width="1" height="1" alt="" />'
        )
        tracking_link = f'{backend_url}/api/track/click/{lead.tracking_id}/'

        html_content = f"""
        <p>Hi {lead.full_name},</p>
        <p>Thank you for reaching out.</p>
        <p>We received your requirement:<br/>
        "{lead.requirement}"</p>
        <p>Learn more: <a href="{tracking_link}">Click here</a></p>
        <p>Regards,<br/>Team</p>
        {tracking_pixel}
        """

        text_content = (
            f"Hi {lead.full_name},\n\n"
            f"Thank you for reaching out.\n\n"
            f"We received your requirement:\n\"{lead.requirement}\"\n\n"
            f"Learn more: {tracking_link}\n\n"
            f"Regards,\nTeam"
        )

        subject = "Thank you for reaching out"

        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [lead.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            # Success – update lead
            lead.email_sent = True
            lead.email_sent_at = timezone.now()
            lead.save(update_fields=['email_sent', 'email_sent_at'])
            print(f"[EMAIL THREAD] Email sent successfully to {lead.email}")

        except Exception as e:
            print("SMTP EMAIL ERROR:", repr(e))
            # email_sent stays False (default)

    # ------------------------------------------------------------------ #
    #  DRF hooks                                                          #
    # ------------------------------------------------------------------ #
    def perform_create(self, serializer):
        requirement = serializer.validated_data.get('requirement', '')
        category, priority = self.classify_lead(requirement)
        lead = serializer.save(ai_category=category, ai_priority=priority)

        # Fire-and-forget background thread
        thread = threading.Thread(
            target=self._send_email_in_background,
            args=(lead.id,),
        )
        thread.daemon = True
        thread.start()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        # Return full lead data immediately (email will arrive in background)
        lead = Lead.objects.get(id=serializer.instance.id)
        response_data = LeadSerializer(lead).data
        response_data['email_status_msg'] = 'Email is being sent in the background.'

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class DashboardAPIView(APIView):
    def get(self, request):
        total_leads = Lead.objects.count()
        total_emails_sent = Lead.objects.filter(email_sent=True).count()
        total_emails_opened = Lead.objects.filter(email_opened=True).count()
        total_links_clicked = Lead.objects.filter(link_clicked=True).count()

        open_rate = round((total_emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0, 2)
        click_rate = round((total_links_clicked / total_emails_opened * 100) if total_emails_opened > 0 else 0, 2)

        recent_leads = LeadSerializer(Lead.objects.all().order_by('-submission_time')[:10], many=True).data

        category_breakdown_qs = Lead.objects.values('ai_category').annotate(count=Count('ai_category'))
        category_breakdown = {item['ai_category'] or 'Unknown': item['count'] for item in category_breakdown_qs}

        return Response({
            'total_leads': total_leads,
            'total_emails_sent': total_emails_sent,
            'total_emails_opened': total_emails_opened,
            'open_rate': open_rate,
            'total_links_clicked': total_links_clicked,
            'click_rate': click_rate,
            'recent_leads': recent_leads,
            'category_breakdown': category_breakdown
        })


class TrackOpenAPIView(APIView):
    def get(self, request, tracking_id):
        try:
            lead = Lead.objects.get(tracking_id=tracking_id)
            if not lead.email_opened:
                lead.email_opened = True
                lead.email_opened_at = timezone.now()
            lead.open_count += 1
            lead.save()
        except Lead.DoesNotExist:
            pass

        response = HttpResponse(PIXEL_GIF_DATA, content_type='image/gif')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response


class TrackClickAPIView(APIView):
    def get(self, request, tracking_id):
        try:
            lead = Lead.objects.get(tracking_id=tracking_id)
            if not lead.link_clicked:
                lead.link_clicked = True
                lead.link_clicked_at = timezone.now()
            lead.click_count += 1
            lead.save()
        except Lead.DoesNotExist:
            pass

        frontend_url = os.environ.get('FRONTEND_URL', 'https://admexo-assignment-q37j.vercel.app')
        if not (frontend_url.startswith('http://') or frontend_url.startswith('https://')):
            frontend_url = f'https://{frontend_url}'
        return redirect(f"{frontend_url.rstrip('/')}/thank-you")


class TestEmailAPIView(APIView):
    """
    GET /api/test-email/?to=someone@example.com
    Quick SMTP verification endpoint.
    """
    def get(self, request):
        to_email = request.query_params.get('to')
        if not to_email:
            return Response(
                {'success': False, 'error': 'Missing `to` query parameter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from_email = settings.DEFAULT_FROM_EMAIL or 'yatins113@gmail.com'
        subject = 'SMTP Test – ADMEXO Assignment'
        text = 'This is a test email to verify your Gmail SMTP configuration.'
        html = f'<p>{text}</p>'

        try:
            msg = EmailMultiAlternatives(subject, text, from_email, [to_email])
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=False)
            return Response({'success': True})
        except Exception as e:
            print("TEST EMAIL ERROR:", repr(e))
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
