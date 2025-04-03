from django.urls import path
from .views import ChatAPIView, ChatAPISystemView

urlpatterns = [
    path('predict/', ChatAPIView.as_view(), name='predict'),
    path('predict-withsys/', ChatAPISystemView.as_view(), name='sys_predict'),
]