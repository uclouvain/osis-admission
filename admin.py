# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib import admin
from django import forms
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
from admission.contrib.models import (
    CddMailTemplate,
    DoctorateAdmission,
    Scholarship,
)
from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from admission.contrib.models.form_item import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite
from osis_mail_template.admin import MailTemplateAdmin

from base.models.education_group_type import EducationGroupType
from base.models.enums.education_group_categories import Categories
from osis_role.contrib.admin import RoleModelAdmin


# ##############################################################################
# Models


class DoctorateAdmissionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['training', 'thesis_institute']
    list_display = ['reference', 'candidate_fmt', 'doctorate', 'type', 'status']
    list_filter = ['status', 'type']
    list_select_related = ['candidate', 'training__academic_year']
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


class ScholarshipAdmin(admin.ModelAdmin):
    list_display = [
        'short_name',
        'long_name',
    ]
    search_fields = [
        'short_name',
        'long_name',
    ]
    list_filter = [
        'type',
    ]
    fields = [
        'type',
        'short_name',
        'long_name',
        'deleted',
    ]


class AdmissionFormItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'internal_label',
        'type',
        'active',
    ]
    search_fields = [
        'id',
        'internal_label',
    ]
    list_filter = [
        'type',
        'active',
    ]


class AdmissionFormItemInstantiationForm(forms.ModelForm):
    education_group_type = forms.ModelChoiceField(
        queryset=EducationGroupType.objects.filter(category=Categories.TRAINING.name),
        required=False,
    )

    class Meta:
        model = AdmissionFormItemInstantiation
        fields = '__all__'


class AdmissionFormItemInstantiationAdmin(admin.ModelAdmin):
    list_display = [
        'academic_year',
        'form_item',
        'required',
        'display_according_education',
    ]
    search_fields = ['form_item__id', 'form_item__internal_label', 'education_group__educationgroupyear__acronym']
    list_filter = [
        'required',
        'form_item__active',
        'display_according_education',
        'education_group_type',
        'tab',
        'candidate_nationality',
        'study_language',
        'vip_candidate',
        'academic_year',
    ]
    raw_id_fields = ['education_group']
    form = AdmissionFormItemInstantiationForm


admin.site.register(DoctorateAdmission, DoctorateAdmissionAdmin)
admin.site.register(CddMailTemplate, CddMailTemplateAdmin)
admin.site.register(CddConfiguration)
admin.site.register(Scholarship, ScholarshipAdmin)
admin.site.register(AdmissionFormItem, AdmissionFormItemAdmin)
admin.site.register(AdmissionFormItemInstantiation, AdmissionFormItemInstantiationAdmin)


class ActivityAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'context', 'get_category', 'ects', 'modified_at', 'status', 'is_course_completed')
    search_fields = ['doctorate__uuid', 'doctorate__reference']
    list_filter = [
        'context',
        'category',
        'status',
    ]
    fields = [
        'doctorate',
        'category',
        'parent',
        'ects',
        'course_completed',
        "type",
        "title",
        "participating_proof",
        "comment",
        "start_date",
        "end_date",
        "participating_days",
        "is_online",
        "country",
        "city",
        "organizing_institution",
        "website",
        "committee",
        "dial_reference",
        "acceptation_proof",
        "summary",
        "subtype",
        "subtitle",
        "authors",
        "role",
        "keywords",
        "journal",
        "publication_status",
        "hour_volume",
        "learning_unit_year",
        "can_be_submitted",
    ]
    readonly_fields = [
        'doctorate',
        'category',
        'parent',
        "type",
        "title",
        "participating_proof",
        "comment",
        "start_date",
        "end_date",
        "participating_days",
        "is_online",
        "country",
        "city",
        "organizing_institution",
        "website",
        "committee",
        "dial_reference",
        "acceptation_proof",
        "summary",
        "subtype",
        "subtitle",
        "authors",
        "role",
        "keywords",
        "journal",
        "publication_status",
        "hour_volume",
        "learning_unit_year",
        "can_be_submitted",
    ]
    list_select_related = ['doctorate', 'parent']

    @admin.display(description=_('Course completed'), boolean=True)
    def is_course_completed(self, obj: Activity):
        if obj.category == CategorieActivite.UCL_COURSE.name:
            return obj.course_completed

    @admin.display(description=_('Category'))
    def get_category(self, obj: Activity):
        if obj.parent_id:
            return f"({obj.parent.category}) {obj.category}"
        return obj.category


admin.site.register(Activity, ActivityAdmin)


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
