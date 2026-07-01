from django.urls import path

from .views import (
    HospitalDetailView,
    HospitalListView,
    MyHospitalView,
    UpdateBedInventoryView,
    UpdateEquipmentView,
)

app_name = "hospitals"

urlpatterns = [
    path("", HospitalListView.as_view(), name="list"),
    path("mine/", MyHospitalView.as_view(), name="mine"),
    path("<int:pk>/", HospitalDetailView.as_view(), name="detail"),
    path("beds/<int:pk>/", UpdateBedInventoryView.as_view(), name="update-bed"),
    path("equipment/<int:pk>/", UpdateEquipmentView.as_view(), name="update-equipment"),
]
