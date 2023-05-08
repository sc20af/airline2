from rest_framework import serializers
from .models import FlightInstance

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightInstance
        fields = '__all__'
