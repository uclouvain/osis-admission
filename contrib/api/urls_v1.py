from rest_framework.routers import DefaultRouter

from admission.contrib.api.views.doctorate import AdmissionDoctorateViewSet

app_name = "admission_api_v1"
router = DefaultRouter()
router.register(r'', AdmissionDoctorateViewSet, basename='doctorate')
urlpatterns = router.urls
