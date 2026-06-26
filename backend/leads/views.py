import os
import requests
from datetime import datetime
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

    def send_email(self, lead):
        api_key = os.environ.get('RESEND_API_KEY')
        from_email = os.environ.get('FROM_EMAIL', 'onboarding@resend.dev')
        backend_url = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000')
        
        if not api_key:
            return False, "Resend API key is missing."

        tracking_pixel = f'<img src="{backend_url}/api/track/open/{lead.tracking_id}/" width="1" height="1" alt="" />'
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

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "from": from_email,
            "to": [lead.email],
            "subject": "Thank you for reaching out",
            "html": html_content
        }

        try:
            response = requests.post('https://api.resend.com/emails', json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                return True, "Email sent successfully."
            else:
                return False, f"Resend API error: {response.text}"
        except Exception as e:
            return False, str(e)

    def perform_create(self, serializer):
        requirement = serializer.validated_data.get('requirement', '')
        category, priority = self.classify_lead(requirement)
        lead = serializer.save(ai_category=category, ai_priority=priority)
        
        # Send email
        email_success, email_msg = self.send_email(lead)
        if email_success:
            lead.email_sent = True
            lead.email_sent_at = timezone.now()
            lead.save(update_fields=['email_sent', 'email_sent_at'])
            
        self.email_status_msg = email_msg

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        
        # Get the saved lead data using full serializer to include tracking_id
        lead = Lead.objects.get(id=serializer.instance.id)
        response_data = LeadSerializer(lead).data
        response_data['email_status_msg'] = getattr(self, 'email_status_msg', 'Unknown')
        
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
            
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/thank-you")
