from django.urls import path
from .views import (
    LeadListCreateAPIView,
    DashboardAPIView,
    TrackOpenAPIView,
    TrackClickAPIView,
    TestEmailAPIView,
)

urlpatterns = [
    path('leads/', LeadListCreateAPIView.as_view(), name='lead-list-create'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('track/open/<uuid:tracking_id>/', TrackOpenAPIView.as_view(), name='track-open'),
    path('track/click/<uuid:tracking_id>/', TrackClickAPIView.as_view(), name='track-click'),
    path('test-email/', TestEmailAPIView.as_view(), name='test-email'),
]
