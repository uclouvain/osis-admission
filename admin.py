# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import Optional

from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


from admission.auth.roles.adre import AdreSecretary
from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.candidate import Candidate
from admission.auth.roles.cdd_manager import CddManager
from admission.auth.roles.doctorate_reader import DoctorateReader
from admission.auth.roles.jury_secretary import JurySecretary
from admission.auth.roles.promoter import Promoter
from admission.auth.roles.sceb import Sceb
from admission.auth.roles.sic_director import SicDirector
from admission.auth.roles.sic_manager import SicManager
from admission.contrib.models import CddMailTemplate, DoctorateAdmission
from admission.contrib.models.cdd_config import CddConfiguration
from osis_mail_template.admin import MailTemplateAdmin

from admission.contrib.models.form_item import AdmissionFormItem
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from osis_role.contrib.admin import RoleModelAdmin

# ##############################################################################
# Models


class DoctorateAdmissionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['doctorate', 'thesis_institute']
    list_display = ['reference', 'candidate_fmt', 'doctorate', 'type', 'status']
    list_filter = ['status', 'type']
    list_select_related = ['candidate', 'doctorate']
    readonly_fields = [
        "project_document",
        "gantt_graph",
        "program_proposition",
        "additional_training_project",
        "recommendation_letters",
        "cotutelle_opening_request",
        "cotutelle_convention",
        "cotutelle_other_documents",
        "detailed_status",
        "submitted_profile",
        "pre_admission_submission_date",
        "admission_submission_date",
        "professional_valuated_experiences",
        "educational_valuated_experiences",
        "scholarship_proof",
    ]
    exclude = ["valuated_experiences"]

    def candidate_fmt(self, obj):
        return "{} ({global_id})".format(obj.candidate, global_id=obj.candidate.global_id)

    candidate_fmt.short_description = _("Candidate")


class CddMailTemplateAdmin(MailTemplateAdmin):
    list_display = ('name', 'identifier', 'language', 'cdd')
    search_fields = [
        'cdd__acronym',
        'idenfier',
    ]
    list_filter = [
        'cdd',
        'language',
        'identifier',
    ]


class TabularFormItemAdmin(admin.TabularInline):
    fields = (
        'weight',
        'type',
        'internal_label',
        'required',
        'title',
        'text',
        'help_text',
        'config',
        'deleted',
    )

    model = AdmissionFormItem
    extra = 1


class EducationGroupYearAdmin(admin.ModelAdmin):
    list_display = ['acronym', 'partial_acronym', 'title', 'academic_year', 'education_group_type']
    search_fields = ['acronym', 'partial_acronym', 'title', 'id']

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[EducationGroupYear] = ...) -> bool:
        return False

    fields = ['acronym']
    readonly_fields = ['acronym']

    inlines = [TabularFormItemAdmin]


class AdmissionTrainingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(education_group_type__category=Categories.MINI_TRAINING.name)


class AdmissionTrainingConfiguration(EducationGroupYear):
    objects = AdmissionTrainingManager()

    class Meta:
        proxy = True
        verbose_name = _("Training configuration for admission")
        verbose_name_plural = _("Training configurations for admission")


admin.site.register(DoctorateAdmission, DoctorateAdmissionAdmin)
admin.site.register(CddMailTemplate, CddMailTemplateAdmin)
admin.site.register(CddConfiguration)
admin.site.register(AdmissionTrainingConfiguration, EducationGroupYearAdmin)


# ##############################################################################
# Roles


class ExternalCommitteeMemberAdmin(RoleModelAdmin):
    list_display = ('person', 'is_external', 'title', 'institute', 'city', 'country')
    list_filter = ['is_external']
    list_select_related = ['person', 'country']


class CDDRoleModelAdmin(RoleModelAdmin):
    list_display = ('person', 'entity')
    search_fields = [
        'person__first_name',
        'person__last_name',
        'entity__entityversion__acronym',
    ]


admin.site.register(Promoter, ExternalCommitteeMemberAdmin)
admin.site.register(CommitteeMember, ExternalCommitteeMemberAdmin)
admin.site.register(SicManager, RoleModelAdmin)
admin.site.register(SicDirector, RoleModelAdmin)
admin.site.register(AdreSecretary, RoleModelAdmin)
admin.site.register(Candidate, RoleModelAdmin)
admin.site.register(JurySecretary, RoleModelAdmin)
admin.site.register(Sceb, RoleModelAdmin)
admin.site.register(CddManager, CDDRoleModelAdmin)
admin.site.register(DoctorateReader, RoleModelAdmin)
