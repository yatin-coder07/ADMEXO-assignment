from rest_framework import serializers
from .models import Lead

class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['full_name', 'email', 'phone', 'company', 'requirement']

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
