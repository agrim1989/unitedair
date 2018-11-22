from rest_framework import serializers
from .models import *
import string, random
import re
from django.utils.translation import ugettext_lazy as _


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events


class EventSearchSerializer(serializers.ModelSerializer):
    search_text = serializers.CharField(required=False, help_text=_("Event Heading"))
    search_type = serializers.CharField(required=True, help_text=_("Event Heading"))
    page_no = serializers.IntegerField(required=True)

    class Meta:
        model = Events
        fields = ['search_text', 'search_type', "page_no"]


class EventDetailSerializer(serializers.ModelSerializer):
    event_id = serializers.CharField(required=True, help_text=_("Event ID(Integer)"))

    class Meta:
        model = Events
        fields = ['event_id']


class AddEventInterestedSerializer(serializers.ModelSerializer):
    event_id = serializers.CharField(required=True, help_text=_("Event ID"))
    device_id = serializers.CharField(required=True, help_text=_("Device ID"))

    class Meta:
        model = Events
        fields = ['event_id', "device_id"]


class BlogCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogCategories


class BlogSerializer(serializers.ModelSerializer):
    category_id = serializers.CharField(required=True, help_text=_("Blog Category ID"))

    class Meta:
        model = Blog
        fields = ["category_id"]


class BlogDetailsSerializer(serializers.ModelSerializer):
    blog_id = serializers.CharField(required=True, help_text=_("Blog ID"))

    class Meta:
        model = Blog
        fields = ['blog_id']


class BlogSearchSerializer(serializers.ModelSerializer):
    heading = serializers.CharField(required=True, help_text=_("Blog ID"))

    class Meta:
        model = Blog
        fields = ['heading']


class AirQualitySerializer(serializers.ModelSerializer):

    class Meta:
        model = AirQuality


class AirPollutionSerializer(serializers.ModelSerializer):
    lat = serializers.CharField(required=True, help_text=_("Latitude"))
    lon = serializers.CharField(required=True, help_text=_("Longitude"))

    class Meta:
        model = AirPollution
        fields = ['lat', "lon"]