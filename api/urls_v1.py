from rest_framework.routers import DefaultRouter

from admission.api.views import AdmissionDoctorateViewSet

app_name = "admission_api_v1"
router = DefaultRouter()
router.register(r'', AdmissionDoctorateViewSet, basename='doctorate')
urlpatterns = router.urls
