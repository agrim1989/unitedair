# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .serailizers import *
from django.http import JsonResponse
from rest_framework.viewsets import generics
import datetime
from django.conf import settings
import math
import requests


def event_data(events, page_no):
    page_no = int(page_no)
    start, end, page = 0,10, 1
    if page_no == 1:
        events = events[start:end]
    else:
        count = page_no - page
        start = start + count * 10
        end = end + count * 10
        events = events[start:end]

    response = []
    for e in events:
        response.append(
            dict(
                id=e.id,
                heading=e.heading,
                description=e.description,
                event_image=e.event_image,
                event_date=e.event_date,
                event_time=e.event_time,
                event_address=e.event_address,
                latitude=e.latitude,
                longitude=e.longitude
            )
        )

    return response


def blog_data(events):
    response = []
    for e in events:
        response.append(
            dict(
                category=e.category.name,
                id=e.id,
                heading=e.heading,
                description=e.description,
                event_image=e.blog_image,
                create_date=e.created_date,
            )
        )

    return response


def color_return(val):
    val = float(val)
    if 0.0 <= val < 30.0:
        return "16734"
    elif 31.0 <= val <= 60.0:
        return "01a84d"
    elif 61.0 <= val <= 90.0:
        return "d0bc18"
    elif 91.0 <= val <= 120.0:
        return "eb9413"
    elif 120.0 <= val <= 250.0:
        return "e11a23"
    else:
        return "94150d"


def quality_return(val):
    val = float(val)
    if 0.0 <= val < 30.0:
        return 'GOOD'
    elif 31.0 <= val <= 60.0:
        return 'SATISFACTORY'
    elif 61.0 <= val <= 90.0:
        return 'MODERATE'
    elif 91.0 <= val <= 120.0:
        return 'POOR'
    elif 121.0 <= val <= 250.0:
        return 'VERY POOR'
    else:
        return 'SEVERELY POLLUTED'


def quality_color(quality):
    response = []
    for q in quality:
        response.append({
            "name":q.name,
            "display_text": q.display_text,
            "color": q.color_code,
            "level": "({} - {})".format(q.minimum, q.maximum) if q.maximum < 999 else "> {}".format(q.minimum)
        })
    return response


class EventGeneric(generics.CreateAPIView):
    queryset = Events.objects.all()
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:

            today = datetime.datetime.now().date()
            events_future = Events.objects.filter(event_date__gte=today).order_by("event_date")
            events_past = Events.objects.filter(event_date__lt=today).order_by("-event_date")
            future_events = event_data(events_future, page_no=1)
            past_events = event_data(events_past, page_no=1)
            return JsonResponse(dict(status=200,
                                message="success",
                                payload=dict(upcoming_event=future_events[:5], past_events=past_events[:5],
                                             past_event_count=events_past.count(),
                                             upcoming_event_count=events_future.count(),
                                             )
                                ))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class EventSearchGeneric(generics.CreateAPIView):
    queryset = Events.objects.all()
    serializer_class = EventSearchSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    search_text = request.data['search_text']
                    search_type = request.data['search_type']
                    page_no = request.data['page_no']
                else:
                    search_text = request.POST.get('search_text',"")
                    search_type = request.POST.get('search_type',"")
                    page_no = request.POST.get('page_no',"")
            except Exception:
                return JsonResponse(dict(status=400, message="Heading Missing", payload={}))
            if not search_type or not page_no:
                return JsonResponse(dict(status=400, message="All Fields Required", payload={}))
            today = datetime.datetime.now().date()
            search_type = search_type.lower()
            if search_text and search_type == "upcoming":
                event = Events.objects.filter(heading__icontains=search_text, event_date__gte=today).order_by("-event_date")
            elif search_text and search_type == "past":
                event = Events.objects.filter(heading__icontains=search_text, event_date__lt=today).order_by("-event_date")
            elif search_type == "upcoming":
                event = Events.objects.filter(event_date__gte=today).order_by("-event_date")
            elif search_type == "past":
                event = Events.objects.filter(event_date__lt=today).order_by("-event_date")
            elif search_type == "all" and search_text:
                event = Events.objects.filter(heading__icontains=search_text).order_by("-event_date")
            else:
                event = Events.objects.all().order_by("-event_date")

            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=dict(events=event_data(event, page_no), page_no=page_no, total_records=event.count()
                                     )))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class EventDetailGeneric(generics.CreateAPIView):
    queryset = Events.objects.all()
    serializer_class = EventDetailSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    event_id = request.data['event_id']
                    device_id = request.data['device_id']
                else:
                    event_id = request.POST.get('event_id', "")
                    device_id = request.POST.get('device_id', "")
            except Exception:
                return JsonResponse(dict(status=400, message="Event ID Missing", payload={}))

            event = Events.objects.get(id=int(event_id))
            interested = InterestedEvent.objects.filter(event=event)
            user_interest = InterestedEvent.objects.filter(device_id=device_id)
            response = dict(
                id=event.id,
                heading=event.heading,
                description=event.description,
                event_image=event.event_image,
                event_date=event.event_date,
                event_time=event.event_time,
                event_address=event.event_address,
                latitude=event.latitude,
                longitude=event.longitude,
                interested_users=interested.count(),
                user_interest=1 if len(user_interest) > 0 else 0
            )
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=dict(event=response)))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class AddEventInterestedGeneric(generics.CreateAPIView):
    queryset = InterestedEvent.objects.all()
    serializer_class = AddEventInterestedSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    event_id = request.data['event_id']
                    device_id = request.data['device_id']
                else:
                    event_id = request.POST.get('event_id', "")
                    device_id = request.POST.get('device_id', "")
            except Exception:
                return JsonResponse(dict(status=400, message="Event ID or Device ID Missing", payload={}))

            event = Events.objects.get(id=int(event_id))
            try:
                interested = InterestedEvent.objects.get(event=event, device_id=device_id)
                message = "Already Exists"
            except Exception:
                interested = InterestedEvent.objects.create(event=event, device_id=device_id)
                message = "success"
            return JsonResponse(dict(status=200,
                                     message=message,
                                     payload={}))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class BlogCategoryGeneric(generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogCategorySerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            event = BlogCategories.objects.all().order_by("-name")
            response = []
            for e in event:
                blog = Blog.objects.filter(category=e)
                response.append(
                    {
                        "id": e.id,
                        "name": e.name,
                        "image": e.blog_image,
                        "blog_count": blog.count()
                    }
                )
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=response))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class BlogCategoryListGeneric(generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    category_id = request.data['category_id']
                else:
                    category_id = request.POST.get('category_id', "")
                blog_category = BlogCategories.objects.get(id=int(category_id))

            except Exception:
                return JsonResponse(dict(status=400, message="Blog Category ID Missing", payload={}))
            blog = Blog.objects.filter(category=blog_category).order_by("-created_date")
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=blog_data(blog)))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class BlogDetailGeneric(generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    blog_id = request.data['blog_id']
                else:
                    blog_id = request.POST.get('blog_id', "")
                blog_category = Blog.objects.get(id=int(blog_id))

            except Exception:
                return JsonResponse(dict(status=400, message="Blog Category ID Missing", payload={}))
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=dict(
                                                    id=blog_category.id,
                                                    heading=blog_category.heading,
                                                    description=blog_category.description,
                                                    event_image=blog_category.blog_image,
                                                    create_date=blog_category.created_date,
                                                )))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class BlogSearchGeneric(generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSearchSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    heading = request.data['heading']
                else:
                    heading = request.POST.get('heading', "")
            except Exception:
                return JsonResponse(dict(status=400, message="Heading Missing", payload={}))

            event = Blog.objects.filter(heading__icontains=heading).order_by("-created_date")
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=dict(events=blog_data(event)
                                     )))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class AirQualityGeneric(generics.CreateAPIView):
    queryset = AirQuality.objects.all()
    serializer_class = AirQualitySerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and \
                request.META.get('HTTP_X_API_VERSION', None) == settings.API_VERSION:
            event = AirQuality.objects.all().order_by('id')
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=dict(event_list=quality_color(event))))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


def nearest_tower(event, lat, lon):
    x1 = float(lat) - event[0].latitude
    y1 = float(lon) - event[0].longitude
    x2 = float(lat) - event[1].latitude
    y2 = float(lon) - event[1].longitude
    a = math.sqrt(math.pow(x1, 2) + math.pow(y1, 2))
    b = math.sqrt(math.pow(x2, 2) + math.pow(y2, 2))
    if a < b or a == 0:
        return "ENV1"
    elif b < a or b == 0:
        return "ENV2"


def distance(data, points):
    min_dist = 99999
    resp = ()
    for i in range(len(data)):
        vals = data[i]
        dist = (vals[0] - points[0]) ** 2 + (vals[1] - points[1]) ** 2
        eucd = math.sqrt(dist)
        if eucd < min_dist:
            min_dist = eucd
            resp = vals
    return resp


class AirPollutionGeneric(generics.CreateAPIView):
    queryset = AirPollution.objects.all()
    serializer_class = AirPollutionSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    lat = request.data['lat']
                    lon = request.data['lon']
                else:
                    lat = request.POST.get('lat', "")
                    lon = request.POST.get('lon', "")

            except Exception:
                return JsonResponse(dict(status=400, message="Latitude or Longitude Missing", payload={}))

            event = Towers.objects.all()
            nearest = nearest_tower(event, lat, lon)
            if nearest == "ENV1":
                url = "http://www.envirotechlive.com/app/ajax_cpcb.php"

                querystring = {"method": "requestRecent", "isMultiStation": "1", "stationType": "aqmsp",
                               "lastDataDate": "15-11-2018 00:00:00", "pagenum": "1", "pagesize": "50",
                               "infoTypeRadio": "grid", "graphTypeRadio": "line", "exportTypeRadio": "csv",
                               "fromDate": "21-11-2018 01:00", "toDate": "21-11-2018 18:04", "timeBase": "1hour",
                               "valueTypeRadio": "normal", "timeBaseQuick": "30min", "locationsSelect": "168",
                               "stationsSelect": "283", "channelNos_283[]": ["1", "2"]}

                response = requests.request("GET", url=url, params=querystring)
            else:
                url = "http://www.envirotechlive.com/app/ajax_cpcb.php"

                querystring = {"method": "requestRecent", "isMultiStation": "1", "stationType": "aqmsp",
                               "lastDataDate": "15-11-2018 00:00:00", "pagenum": "1", "pagesize": "50",
                               "infoTypeRadio": "grid", "graphTypeRadio": "line", "exportTypeRadio": "csv",
                               "fromDate": "21-11-2018 01:00", "toDate": "21-11-2018 18:04", "timeBase": "1hour",
                               "valueTypeRadio": "normal", "timeBaseQuick": "30min", "locationsSelect": "168",
                               "stationsSelect": "284", "channelNos_284[]": ["2", "1"]}

                response = requests.request("GET", url=url, params=querystring)
            data = response.json()
            channels = data[0]['channelsData']

            pm10_values = channels[0]
            pm25_values = channels[1]
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload={
                                         "PM10":dict(value=pm10_values['ch1avg'], color=color_return(pm10_values['ch1avg']), quality=quality_return(pm10_values['ch1avg'])),
                                         "PM2.5":dict(value=pm25_values['ch2avg'], color=color_return(pm25_values['ch2avg']), quailty=quality_return(pm25_values['ch2avg']))
                                     }))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class AirPollutionWeekGeneric(generics.CreateAPIView):
    queryset = AirPollution.objects.all()
    serializer_class = AirPollutionSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    lat = request.data['lat']
                    lon = request.data['lon']
                else:
                    lat = request.POST.get('lat', "")
                    lon = request.POST.get('lon', "")

            except Exception:
                return JsonResponse(dict(status=400, message="Latitude or Longitude Missing", payload={}))
            event = Towers.objects.all()
            nearest = nearest_tower(event, lat, lon)
            response_data = []
            if nearest == "ENV1":
                url = "http://www.envirotechlive.com/app/ajax_cpcb.php"
                for i in range(1,8):
                    querystring = {"method": "requestStationReport", "quickReportType": "last7days",
                                   "isMultiStation": "1","stationType": "aqmsp", "pagenum": i,"pagesize": "50",
                                   "infoTypeRadio": "grid","graphTypeRadio": "line","exportTypeRadio": "csv",
                                   "timeBase": "1hour", "valueTypeRadio": "normal", "timeBaseQuick": "24hours",
                                   "locationsSelect": "168", "stationsSelect": "283","channelNos_283[]": ["1", "2"]
                                   }

                    response = requests.request("GET", url, params=querystring)
                    data = response.json()

                    if len(data['data']) > 0:
                        response_data.append(data['data'])
            else:
                url = "http://www.envirotechlive.com/app/ajax_cpcb.php"

                for i in range(1, 8):
                    querystring = {"method": "requestStationReport", "quickReportType": "last7days",
                                   "isMultiStation": "1","stationType": "aqmsp", "pagenum": i, "pagesize": "50",
                                   "infoTypeRadio": "grid","graphTypeRadio": "line", "exportTypeRadio": "csv",
                                   "timeBase": "1hour","valueTypeRadio": "normal", "timeBaseQuick": "24hours",
                                   "locationsSelect": "168","stationsSelect": "284", "channelNos_284[]": ["1", "2"]
                                   }

                    response = requests.request("GET", url, params=querystring)
                    data = response.json()
                    if len(data['data']) > 0:
                        response_data.append(data['data'])
            resp = []
            for d in response_data:
                values = d.values()
                keys = d.keys()
                if len(keys) == 1:
                    keys, values = keys[0], values[0]
                    date = keys.split(" ")[0]
                    pm25 = values[1]
                    pm10 = values[0]
                    resp.append({"date": date, "pm2.5":pm25, "pm10": pm10,"color": color_return(pm10)})
                else:
                    keys1, values1 = keys[0], values[0]
                    date = keys1.split(" ")[0]
                    pm25 = values1[1]
                    pm10 = values1[0]
                    resp.append({"date": date, "pm2.5": pm25, "pm10": pm10,"color": color_return(pm10)})
                    key, value = keys[1], values[1]
                    date = key.split(" ")[0]
                    pm25 = value[1]
                    pm10 = value[0]
                    resp.append({"date": date, "pm2.5": pm25, "pm10": pm10, "color": color_return(pm10)})
            return JsonResponse(dict(status=200,
                                     message="success",
                                     payload=resp))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))


class RegistrationGeneric(generics.CreateAPIView):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        if request.method == "POST" and request.META.get("HTTP_X_API_KEY") == settings.HTTP_API_KEY and request.META.get('HTTP_X_API_VERSION', None) ==settings.API_VERSION:
            try:
                if request.data:
                    name = request.data['name']
                    email = request.data['email']
                    phone = request.data['phone']
                    device_id = request.data['device_id']
                else:
                    name = request.POST.get('name', "")
                    email = request.POST.get('email', "")
                    phone = request.POST.get('phone', "")
                    device_id = request.POST.get('device_id', "")
            except Exception:
                return JsonResponse(dict(status=400, message="All key are mandatory", payload={}))

            try:
                device = Registration.objects.get(email=email)
                return JsonResponse(dict(status=200, message="Already registered", payload={}))
            except Exception:
                device = Registration.objects.create(email=email, name=name, phone=phone, device_id=device_id)
                return JsonResponse(dict(status=200, message="User Eegistered", payload={}))
        else:
            return JsonResponse(dict(status=400, message="Key missing", payload={}))