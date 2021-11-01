from bookmanager.views import LineCallbackAPIView

from django.urls import path

app_name = "bookmanager"

urlpatterns = [path("callback/", LineCallbackAPIView.as_view(), name="callback")]
