# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from typing import Dict

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.messages import info, warning
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext, pgettext_lazy, ngettext
from hijack.contrib.admin import HijackUserAdminMixin
from osis_document.contrib import FileField
from osis_mail_template.admin import MailTemplateAdmin

from admission.auth.roles.adre import AdreSecretary
from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.candidate import Candidate
from admission.auth.roles.cdd_configurator import CddConfigurator
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.doctorate_reader import DoctorateReader
from admission.auth.roles.jury_secretary import JurySecretary
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.promoter import Promoter
from admission.auth.roles.sceb import Sceb
from admission.auth.roles.sic_management import SicManagement
from admission.contrib.models import (
    AdmissionTask,
    AdmissionViewer,
    CddMailTemplate,
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
    Scholarship,
    Accounting,
    DiplomaticPost,
)
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.checklist import RefusalReasonCategory, RefusalReason, AdditionalApprovalCondition
from admission.contrib.models.doctoral_training import Activity
from admission.contrib.models.form_item import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.contrib.models.online_payment import OnlinePayment
from admission.ddd.admission.enums import CritereItemFormulaireFormation
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite, ContexteFormation
from admission.services.injection_epc import InjectionEPC
from admission.views.mollie_webhook import MollieWebHook
from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories
from base.models.person import Person
from education_group.auth.scope import Scope
from education_group.contrib.admin import EducationGroupRoleModelAdmin
from osis_profile.models import EducationalExperience, ProfessionalExperience
from osis_role.contrib.admin import EntityRoleModelAdmin, RoleModelAdmin


# ##############################################################################
# Models


class AdmissionAdminForm(forms.ModelForm):
    educational_valuated_experiences = forms.ModelMultipleChoiceField(
        queryset=EducationalExperience.objects.none(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('Educational experiences'), is_stacked=False),
    )
    professional_valuated_experiences = forms.ModelMultipleChoiceField(
        queryset=ProfessionalExperience.objects.none(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('Professional experiences'), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['educational_valuated_experiences'].queryset = self.instance.candidate.educationalexperience_set
        self.fields['professional_valuated_experiences'].queryset = self.instance.candidate.professionalexperience_set
        self.fields['valuated_secondary_studies_person'].queryset = Person.objects.filter(pk=self.instance.candidate.pk)


class ReadOnlyFilesMixin:
    def get_readonly_fields(self, request, obj=None):
        # Also mark all FileField as readonly (since we don't have admin widget yet)
        return self.readonly_fields + [
            field.name for field in self.model._meta.get_fields(include_parents=True) if isinstance(field, FileField)
        ]


class AdmissionAdminMixin(ReadOnlyFilesMixin, admin.ModelAdmin):
    form = AdmissionAdminForm

    list_display = [
        'reference',
        'candidate_fmt',
        'training',
        'type_demande',
        'status',
        'view_on_portal',
    ]
    search_fields = [
        'reference',
        'candidate__global_id',
        'candidate__last_name',
        'candidate__first_name',
    ]
    readonly_fields = [
        'detailed_status',
        "submitted_at",
        "last_update_author",
        "submitted_profile",
    ]
    list_select_related = [
        'candidate',
        'training__academic_year',
    ]
    list_filter = ['status', 'type_demande']

    def has_add_permission(self, request):
        # Prevent adding from admin site as we lose all business checks
        return False

    @admin.display(description=_('Candidate'))
    def candidate_fmt(self, obj):
        return '{} ({global_id})'.format(obj.candidate, global_id=obj.candidate.global_id)

    @admin.display(description=_('Search on portal'))
    def view_on_portal(self, obj):
        url = f"{settings.OSIS_PORTAL_URL}admin/auth/user/?q={obj.candidate.global_id}"
        return mark_safe(f'<a class="button" href="{url}" target="_blank">{_("Candidate on portal")}</a>')


class DoctorateAdmissionAdmin(AdmissionAdminMixin):
    autocomplete_fields = [
        'training',
        'thesis_institute',
        'international_scholarship',
    ]
    list_display = ['reference', 'candidate_fmt', 'doctorate', 'type', 'status', 'view_on_portal']
    list_filter = ['status', 'type']
    readonly_fields = [
        "detailed_status",
        "pre_admission_submission_date",
        "submitted_at",
        "last_update_author",
    ]
    exclude = ["valuated_experiences"]

    @staticmethod
    def view_on_site(obj):
        return resolve_url(f'admission:doctorate', uuid=obj.uuid)


class ContinuingEducationAdmissionAdmin(AdmissionAdminMixin):
    autocomplete_fields = ['training']

    @staticmethod
    def view_on_site(obj):
        return resolve_url(f'admission:continuing-education', uuid=obj.uuid)


class GeneralEducationAdmissionAdmin(AdmissionAdminMixin):
    autocomplete_fields = [
        'training',
        'double_degree_scholarship',
        'international_scholarship',
        'erasmus_mundus_scholarship',
        'additional_approval_conditions',
        'other_training_accepted_by_fac',
        'prerequisite_courses',
        'diplomatic_post',
        'refusal_reasons',
    ]
    actions = ['trigger_payment_hook']

    @staticmethod
    def view_on_site(obj):
        return resolve_url(f'admission:general-education', uuid=obj.uuid)

    def has_payment_hook_triggering_permission(self, request):
        return settings.DEBUG and request.user.is_staff

    @admin.action(description=_('Trigger the payment hook'), permissions=['payment_hook_triggering'])
    def trigger_payment_hook(self, request, queryset):
        """Manually trigger the payment hook as it's not always possible to do it automatically."""
        admissions_ids = set(request.POST.getlist('_selected_action'))

        payments = OnlinePayment.objects.filter(admission_id__in=admissions_ids)
        achieved_admissions_ids = set()

        for payment in payments:
            result = MollieWebHook.update_from_payment(paiement_id=payment.payment_id)
            if result:
                achieved_admissions_ids.add(payment.admission_id)

        if achieved_admissions_ids:
            info(
                request,
                ngettext(
                    'The following admission has been updated: {}.',
                    'The following admissions have been updated: {}.',
                    len(achieved_admissions_ids),
                ).format(', '.join(map(str, achieved_admissions_ids))),
            )

        not_achieved_admissions_ids = admissions_ids - achieved_admissions_ids
        if not_achieved_admissions_ids:
            warning(
                request,
                ngettext(
                    'The following admission has not been updated: {}.',
                    'The following admissions have not been updated: {}.',
                    len(not_achieved_admissions_ids),
                ).format(', '.join(map(str, not_achieved_admissions_ids))),
            )


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

    @staticmethod
    def view_on_site(obj):
        return resolve_url(f'admission:config:cdd-mail-template:preview', identifier=obj.identifier, pk=obj.pk)


class ScholarshipAdmin(admin.ModelAdmin):
    list_display = [
        'short_name',
        'long_name',
        'type',
        'enabled',
    ]
    search_fields = [
        'short_name',
        'long_name',
    ]
    list_filter = [
        'type',
        'disabled',
    ]
    fields = [
        'type',
        'short_name',
        'long_name',
        'disabled',
    ]

    @admin.display(description=_('Enabled'), boolean=True)
    def enabled(self, obj):
        return not obj.disabled


FORM_ITEM_MIN_YEAR = 2022


class EducationGroupTypeListFilter(admin.SimpleListFilter):
    title = _('education group type')

    parameter_name = 'education_group_type_id'

    def lookups(self, request, model_admin):
        return [
            (education.id, str(education))
            for education in EducationGroupType.objects.filter(
                category=Categories.TRAINING.name
            ).order_by_translated_name()
        ]

    def queryset(self, request, queryset):
        value = self.value()
        return queryset.filter(education_group_type__pk=value) if value else queryset


class AcademicYearListFilter(admin.SimpleListFilter):
    title = _('academic year')

    parameter_name = 'academic_year_id'

    def lookups(self, request, model_admin):
        return [
            (academic_year.id, str(academic_year))
            for academic_year in AcademicYear.objects.filter(year__gte=FORM_ITEM_MIN_YEAR)
        ]

    def queryset(self, request, queryset):
        value = self.value()
        return queryset.filter(academic_year__pk=value) if value else queryset


class SimpleListFilterWithDefaultValue(admin.SimpleListFilter):
    default_value = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used_parameters.setdefault(self.parameter_name, self.default_value)

    def choices(self, changelist):
        for lookup, title in [('all', _('All'))] + self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def filtered_queryset(self, value, request, queryset):
        raise NotImplementedError(
            'subclasses of SimpleListFilterWithDefaultValue must provide a filtered_queryset() method'
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value != 'all':
            return self.filtered_queryset(value, request, queryset)
        return queryset


class AdmissionFormItemFreeDocumentListFilter(SimpleListFilterWithDefaultValue):
    title = _("use")
    parameter_name = "use"
    default_value = 'without_free_documents'

    def lookups(self, request, model_admin):
        return [
            ('without_free_documents', _("Without free documents")),
            ('free_documents', _("Free documents")),
        ]

    def filtered_queryset(self, value, request, queryset):
        filter_by = models.Q(
            admissionformiteminstantiation__display_according_education=(
                CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name
            )
        )
        return queryset.filter(filter_by if value == 'free_documents' else ~filter_by)


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
        AdmissionFormItemFreeDocumentListFilter,
    ]
    create_only_fields = {
        'internal_label',
    }

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super().get_readonly_fields(request, obj)
        if obj:
            return [field for field in read_only_fields if field not in self.create_only_fields]
        return read_only_fields

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Exclude inactive
        if (
            request.GET.get('model_name') == 'admissionformiteminstantiation'
            and request.GET.get('field_name') == 'form_item'
        ):
            queryset = queryset.filter(active=True).order_by('internal_label')

        return queryset, use_distinct


class AdmissionFormItemInstantiationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(year__gte=FORM_ITEM_MIN_YEAR)
        self.fields['education_group_type'].queryset = EducationGroupType.objects.filter(
            category=Categories.TRAINING.name
        ).order_by_translated_name()

    class Meta:
        model = AdmissionFormItemInstantiation
        fields = '__all__'


class AdmissionFormItemInstantiationFreeDocumentListFilter(AdmissionFormItemFreeDocumentListFilter):
    def filtered_queryset(self, value, request, queryset):
        filter_by = models.Q(display_according_education=CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name)
        return queryset.filter(filter_by if value == 'free_documents' else ~filter_by)


class AdmissionFormItemInstantiationAdmin(admin.ModelAdmin):
    list_display = [
        'academic_year',
        'form_item',
        'is_active',
        'weight',
        'required',
        'display_according_education',
        'education_group_type',
        'education_group_acronym',
        'candidate_nationality',
        'diploma_nationality',
        'study_language',
        'vip_candidate',
        'tab',
    ]
    search_fields = ['form_item__id', 'form_item__internal_label', 'education_group__educationgroupyear__acronym']
    list_filter = [
        'required',
        'form_item__active',
        'display_according_education',
        EducationGroupTypeListFilter,
        'tab',
        'candidate_nationality',
        'diploma_nationality',
        'study_language',
        'vip_candidate',
        AcademicYearListFilter,
        AdmissionFormItemInstantiationFreeDocumentListFilter,
    ]
    raw_id_fields = ['education_group']
    autocomplete_fields = ['form_item', 'admission']
    form = AdmissionFormItemInstantiationForm

    @admin.display(boolean=True, description=_('Is active?'))
    def is_active(self, obj):
        return obj.form_item.active

    @admin.display(description=pgettext('admission', 'Education'))
    def education_group_acronym(self, obj):
        if obj.education_group_id:
            return obj.education_group.most_recent_acronym


class AdmissionViewerAdmin(admin.ModelAdmin):
    list_display = ['admission', 'person', 'viewed_at']
    search_fields = ['admission__reference']
    autocomplete_fields = [
        'person',
        'admission',
    ]
    readonly_fields = [
        'viewed_at',
    ]


class AccountingAdmin(ReadOnlyFilesMixin, admin.ModelAdmin):
    autocomplete_fields = ['admission']
    list_display = ['admission']
    search_fields = ['admission__reference']
    readonly_fields = []


class BaseAdmissionAdmin(admin.ModelAdmin):
    # Only used to search admissions through autocomplete fields
    search_fields = ['reference']
    actions = [
        'injecter_dans_epc',
    ]

    @admin.action(description='Injecter la demande dans EPC')
    def injecter_dans_epc(self, request, queryset):
        for demande in queryset:
            # Check injection state when it exists
            InjectionEPC().injecter(demande)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class DisplayTranslatedNameMixin:
    search_fields = ['name_fr', 'name_en']


class RefusalReasonCategoryAdmin(DisplayTranslatedNameMixin, admin.ModelAdmin):
    list_display = ['name', 'order']
    search_fields = ['name']


class RefusalReasonAdmin(DisplayTranslatedNameMixin, admin.ModelAdmin):
    autocomplete_fields = ['category']
    list_display = ['safe_name', 'category', 'order']
    list_filter = ['category']

    @admin.display(description=_('Name'))
    def safe_name(self, obj):
        return mark_safe(obj.name)


class AdditionalApprovalConditionAdmin(DisplayTranslatedNameMixin, admin.ModelAdmin):
    list_display = ['safe_name_fr', 'safe_name_en']

    @admin.display(description=_('French name'))
    def safe_name_fr(self, obj):
        return mark_safe(obj.name_fr)

    @admin.display(description=_('English name'))
    def safe_name_en(self, obj):
        return mark_safe(obj.name_en)


class DiplomaticPostAdmin(admin.ModelAdmin):
    autocomplete_fields = ['countries']
    search_fields = ['name_fr', 'name_en']
    list_display = ['name_fr', 'name_en', 'email']


class OnlinePaymentAdmin(admin.ModelAdmin):
    search_fields = ['admission', 'payment_id']
    list_display = ['admission', 'payment_id', 'status', 'method']
    list_filter = ['status', 'method']


admin.site.register(DoctorateAdmission, DoctorateAdmissionAdmin)
admin.site.register(CddMailTemplate, CddMailTemplateAdmin)
admin.site.register(CddConfiguration)
admin.site.register(Scholarship, ScholarshipAdmin)
admin.site.register(AdmissionFormItem, AdmissionFormItemAdmin)
admin.site.register(AdmissionFormItemInstantiation, AdmissionFormItemInstantiationAdmin)
admin.site.register(GeneralEducationAdmission, GeneralEducationAdmissionAdmin)
admin.site.register(ContinuingEducationAdmission, ContinuingEducationAdmissionAdmin)
admin.site.register(BaseAdmission, BaseAdmissionAdmin)
admin.site.register(AdmissionViewer, AdmissionViewerAdmin)
admin.site.register(Accounting, AccountingAdmin)
admin.site.register(RefusalReasonCategory, RefusalReasonCategoryAdmin)
admin.site.register(RefusalReason, RefusalReasonAdmin)
admin.site.register(AdditionalApprovalCondition, AdditionalApprovalConditionAdmin)
admin.site.register(DiplomaticPost, DiplomaticPostAdmin)
admin.site.register(OnlinePayment, OnlinePaymentAdmin)


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

    @staticmethod
    def view_on_site(obj):
        context_mapping = {
            ContexteFormation.DOCTORAL_TRAINING.name: 'doctoral-training',
            ContexteFormation.COMPLEMENTARY_TRAINING.name: 'complementary-training',
            ContexteFormation.FREE_COURSE.name: 'course-enrollment',
        }
        context = (
            context_mapping[obj.context] if obj.category != CategorieActivite.UCL_COURSE.name else 'course-enrollment'
        )
        url = resolve_url(f'admission:doctorate:{context}', uuid=obj.doctorate.uuid)
        return url + f'#{obj.uuid}'


admin.site.register(Activity, ActivityAdmin)


class AdmissionTaskAdmin(admin.ModelAdmin):
    list_display = ['admission', 'task_uuid', 'task_status', 'type']
    list_select_related = ['task', 'admission']

    @admin.display(description="Task uuid")
    def task_uuid(self, obj):
        url = resolve_url('admin:osis_async_asynctask_change', obj.task.pk)
        return mark_safe(f'<a href="{url}" target="_blank">{obj.task.uuid}</a>')

    @admin.display(description="Task status")
    def task_status(self, obj):
        return obj.task.state

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


admin.site.register(AdmissionTask, AdmissionTaskAdmin)


# ##############################################################################
# Roles


class HijackRoleModelAdmin(HijackUserAdminMixin, RoleModelAdmin):
    list_select_related = ['person__user']

    def get_hijack_user(self, obj):
        return obj.person.user


class HijackEntityRoleModelAdmin(HijackUserAdminMixin, EntityRoleModelAdmin):
    list_select_related = ['person__user']

    def get_hijack_user(self, obj):
        return obj.person.user


class CddConfiguratorAdmin(HijackRoleModelAdmin):
    list_display = ('person', 'most_recent_acronym')
    search_fields = [
        'person__first_name',
        'person__last_name',
        'entity__entityversion__acronym',
    ]

    @admin.display(description=pgettext_lazy('admission', 'Entity'))
    def most_recent_acronym(self, obj):
        return obj.most_recent_acronym

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                most_recent_acronym=models.Subquery(
                    EntityVersion.objects.filter(
                        entity__id=models.OuterRef('entity_id'),
                    )
                    .order_by("-start_date")
                    .values('acronym')[:1]
                )
            )
        )


class FrontOfficeRoleModelAdmin(RoleModelAdmin):
    list_display = ('person', 'global_id', 'view_on_portal')

    @admin.display(description=_('Identifier'))
    def global_id(self, obj):
        return obj.person.global_id

    @admin.display(description=_('Search on portal'))
    def view_on_portal(self, obj):
        url = f"{settings.OSIS_PORTAL_URL}admin/auth/user/?q={obj.person.global_id}"
        return mark_safe(f'<a class="button" href="{url}" target="_blank">{_("Search on portal")}</a>')


class TypeField(forms.CheckboxSelectMultiple):
    def format_value(self, value):
        if isinstance(value, str):
            value = value.split(',')
        return super().format_value(value)


class CentralManagerAdmin(HijackUserAdminMixin, EntityRoleModelAdmin):
    list_select_related = ['person__user']
    list_display = ('person', 'entity', 'scopes')
    search_fields = ['person__first_name', 'person__last_name', 'entity__entityversion__acronym']
    raw_id_fields = (
        'person',
        'entity',
    )
    formfield_overrides = {ArrayField: {'widget': TypeField(choices=Scope.choices())}}

    def get_hijack_user(self, obj):
        return obj.person.user

    def _build_model_from_csv_row(self, csv_row: Dict):
        central_manager = super()._build_model_from_csv_row(csv_row)
        central_manager.scopes = csv_row.get('SCOPES', 'ALL').split("|")
        return central_manager


class ProgramManagerAdmin(HijackUserAdminMixin, EducationGroupRoleModelAdmin):
    list_select_related = ['person__user']
    list_display = ['person', 'education_group_most_recent_acronym']

    def get_hijack_user(self, obj):
        return obj.person.user


admin.site.register(Promoter, FrontOfficeRoleModelAdmin)
admin.site.register(CommitteeMember, FrontOfficeRoleModelAdmin)
admin.site.register(Candidate, FrontOfficeRoleModelAdmin)

admin.site.register(CddConfigurator, CddConfiguratorAdmin)

admin.site.register(CentralManager, CentralManagerAdmin)
admin.site.register(ProgramManager, ProgramManagerAdmin)
admin.site.register(SicManagement, HijackEntityRoleModelAdmin)
admin.site.register(AdreSecretary, HijackRoleModelAdmin)
admin.site.register(JurySecretary, HijackRoleModelAdmin)
admin.site.register(Sceb, HijackRoleModelAdmin)
admin.site.register(DoctorateReader, HijackRoleModelAdmin)
