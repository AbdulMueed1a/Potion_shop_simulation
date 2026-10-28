from django.urls import path
from simulator import views

urlpatterns = [path("", views.index, name="index")]
