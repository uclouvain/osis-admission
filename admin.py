from django.contrib import admin

from admission.contrib.models import AdmissionDoctorate


class AdmissionDoctorateAdmin(admin.ModelAdmin):
    def save_form(self, request, form, change):
        """
        Set the author if the admission doctorate is being created
        """
        admission_doctorate = form.save(commit=False)
        if not change:
            admission_doctorate.author = request.user.person
        return admission_doctorate


admin.site.register(AdmissionDoctorate, AdmissionDoctorateAdmin)
