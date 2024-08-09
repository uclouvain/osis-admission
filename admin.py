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
from datetime import datetime
from typing import Dict

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.messages import info, warning
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext, pgettext_lazy, ngettext, get_language
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_json_widget.widgets import JSONEditorWidget
from hijack.contrib.admin import HijackUserAdminMixin
from ordered_model.admin import OrderedModelAdmin
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
from admission.contrib.models.categorized_free_document import CategorizedFreeDocument
from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.checklist import (
    RefusalReasonCategory,
    RefusalReason,
    AdditionalApprovalCondition,
    FreeAdditionalApprovalCondition,
)
from admission.contrib.models.doctoral_training import Activity
from admission.contrib.models.epc_injection import EPCInjection, EPCInjectionStatus, EPCInjectionType
from admission.contrib.models.form_item import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.contrib.models.online_payment import OnlinePayment
from admission.contrib.models.working_list import WorkingList
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums import CritereItemFormulaireFormation
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import ORGANISATION_ONGLETS_CHECKLIST
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite, ContexteFormation
from admission.forms.checklist_state_filter import ChecklistStateFilterField
from admission.services.injection_epc.injection_dossier import InjectionEPCAdmission
from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique
from admission.tasks import bulk_create_digit_persons_tickets, injecter_signaletique_a_epc_task
from admission.views.mollie_webhook import MollieWebHook
from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories
from base.models.person import Person
from education_group.auth.scope import Scope
from education_group.contrib.admin import EducationGroupRoleModelAdmin
from epc.models.inscription_programme_cycle import InscriptionProgrammeCycle
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
    internal_access_titles = forms.ModelMultipleChoiceField(
        queryset=InscriptionProgrammeCycle.objects.none(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_('Internal experiences to choose as access titles'),
            is_stacked=False,
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['educational_valuated_experiences'].queryset = self.instance.candidate.educationalexperience_set
        self.fields['professional_valuated_experiences'].queryset = self.instance.candidate.professionalexperience_set
        self.fields['valuated_secondary_studies_person'].queryset = Person.objects.filter(pk=self.instance.candidate.pk)
        self.fields['internal_access_titles'].queryset = InscriptionProgrammeCycle.objects.filter(
            etudiant__person=self.instance.candidate,
        )


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
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

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
    autocomplete_fields = [
        'training',
        'last_email_sent_by',
    ]

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

    readonly_fields = AdmissionAdminMixin.readonly_fields + [
        'financability_computed_rule',
        'financability_computed_rule_situation',
        'financability_computed_rule_on',
        'financability_rule_established_by',
        'financability_dispensation_first_notification_on',
        'financability_dispensation_first_notification_by',
        'financability_dispensation_last_notification_on',
        'financability_dispensation_last_notification_by',
    ]

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


class BaseAdmissionStatutFilter(SimpleListFilter):
    title = 'statut'
    parameter_name = 'statut'

    def lookups(self, request, model_admin):
        return set(
            ChoixStatutPropositionGenerale.choices()
            + ChoixStatutPropositionContinue.choices()
            + ChoixStatutPropositionDoctorale.choices()
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(generaleducationadmission__status=self.value()) |
                Q(doctorateadmission__status=self.value()) |
                Q(continuingeducationadmission__status=self.value())
            )
        return queryset


class BaseAdmissionTypeFormationFilter(SimpleListFilter):
    title = 'type_formation'
    parameter_name = 'type_formation'

    def lookups(self, request, model_admin):
        return (
            ('general-education', 'Formation générale'),
            ('doctorate', 'Doctorat'),
            ('continuing-education', 'Formation continue'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(generaleducationadmission__isnull=self.value() != 'general-education') &
                Q(doctorateadmission__isnull=self.value() != 'doctorate') &
                Q(continuingeducationadmission__isnull=self.value() != 'continuing-education')
            )
        return queryset


class BaseAdmissionAdmin(admin.ModelAdmin):
    # Only used to search admissions through autocomplete fields
    search_fields = ['reference', 'candidate__last_name', 'candidate__global_id', 'training__acronym']
    list_display = (
        'reference',
        'candidate',
        'training',
        'type_demande',
        'created_at',
        'statut',
        'type_formation'
    )
    readonly_fields = ['uuid']
    actions = [
        'injecter_dans_epc',
    ]
    list_filter = [
        'type_demande',
        BaseAdmissionTypeFormationFilter,
        BaseAdmissionStatutFilter,
        ('training__academic_year', RelatedDropdownFilter),
        'accounting__sport_affiliation',
    ]

    @admin.action(description='Injecter la demande dans EPC')
    def injecter_dans_epc(self, request, queryset):
        for demande in queryset:
            # Check injection state when it exists
            InjectionEPCAdmission().injecter(demande)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Statut')
    def statut(self, obj):
        admission = (
            getattr(obj, 'generaleducationadmission', None)
            or getattr(obj, 'doctorateadmission', None)
            or getattr(obj, 'continuingeducationadmission', None)
        )
        return admission.get_status_display()

    @admin.display(description='Type formation')
    def type_formation(self, obj):
        if hasattr(obj, 'generaleducationadmission'):
            return 'Formation générale'
        if hasattr(obj, 'doctorateadmission'):
            return 'Doctorat'
        if hasattr(obj, 'continuingeducationadmission'):
            return 'Formation continue'


class DisplayTranslatedNameMixin:
    search_fields = ['name_fr', 'name_en']


class RefusalReasonCategoryAdmin(DisplayTranslatedNameMixin, OrderedModelAdmin):
    list_display = ['name', 'move_up_down_links', 'order']
    search_fields = ['name']


class RefusalReasonAdmin(DisplayTranslatedNameMixin, OrderedModelAdmin):
    autocomplete_fields = ['category']
    list_display = ['safe_name', 'category', 'move_up_down_links', 'order']
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


class EPCInjectionAdmin(admin.ModelAdmin):
    search_fields = ['admission__reference', 'admission__candidate__global_id', 'admission__candidate__last_name']
    list_display = ['admission', 'type', 'status', 'errors_messages', 'last_attempt_date', 'last_response_date']
    list_filter = ['status', 'type']
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    raw_id_fields = ['admission']
    actions = [
        'reinjecter_la_signaletique_dans_epc',
        'reinjecter_la_demande_dans_epc',
    ]

    def errors_messages(self, obj):
        return obj.html_errors

    @admin.action(description="Réinjecter la signalétique dans EPC")
    def reinjecter_la_signaletique_dans_epc(self, request, queryset):
        admissions_references = queryset.filter(
            type=EPCInjectionType.SIGNALETIQUE.name
        ).values_list('admission__reference', flat=True)
        injecter_signaletique_a_epc_task.run(admissions_references=list(admissions_references))

    @admin.action(description="Réinjecter la demande dans EPC")
    def reinjecter_la_demande_dans_epc(self, request, queryset):
        for injection in queryset.filter(
            type=EPCInjectionType.DEMANDE.name
        ).exclude(
            status=EPCInjectionStatus.OK.name
        ):
            injection.last_attempt_date = datetime.now()
            injection.save()
            InjectionEPCAdmission().envoyer_admission_dans_queue(
                donnees=injection.payload,
                admission_reference=injection.admission.reference,
                admission_uuid=injection.admission.uuid
            )


class FreeAdditionalApprovalConditionAdminForm(forms.ModelForm):
    related_experience = forms.ModelMultipleChoiceField(
        queryset=EducationalExperience.objects.none(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('Educational experiences'), is_stacked=False),
        to_field_name='uuid',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_experience'].queryset = self.instance.admission.candidate.educationalexperience_set


class FreeAdditionalApprovalConditionAdmin(admin.ModelAdmin):
    form = FreeAdditionalApprovalConditionAdminForm
    list_display = ['name_fr', 'name_en', 'admission']
    search_fields = ['admission__reference']
    autocomplete_fields = [
        'related_experience',
        'admission',
    ]


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
admin.site.register(FreeAdditionalApprovalCondition, FreeAdditionalApprovalConditionAdmin)


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
    list_filter = ['task__state', 'type']
    list_select_related = ['task', 'admission']
    search_fields = ['admission__reference']

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


class CandidateAdmin(FrontOfficeRoleModelAdmin):
    actions = ['send_selected_to_digit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display += ('person_ticket_sent_to_digit', 'person_ticket_done_in_digit')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('person__personticketcreation_set')

    def person_digit_creation_ticket(self, obj):
        return obj.person.personticketcreation_set.all().first()

    @admin.display(description=_('Sent to digit'), boolean=True)
    def person_ticket_sent_to_digit(self, obj):
        return bool(self.person_digit_creation_ticket(obj))

    @admin.display(description=_('Done (DigIT)'), boolean=True)
    def person_ticket_done_in_digit(self, obj):
        ticket = self.person_digit_creation_ticket(obj)
        if ticket:
            return self.person_digit_creation_ticket(obj).status in ["DONE", "DONE_WITH_WARNINGS"]
        return False

    @admin.action(description=_('Send selected candidate to digit'))
    def send_selected_to_digit(self, request, queryset):
        global_ids = queryset.values_list('person__global_id', flat=True)
        bulk_create_digit_persons_tickets.run(request=request, global_ids=global_ids)


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


class AdmissionReaderAdmin(HijackUserAdminMixin, EducationGroupRoleModelAdmin):
    list_display = (
        'person',
        'education_group_most_recent_acronym',
        'cohort',
        'changed',
    )

    def get_hijack_user(self, obj):
        return obj.person.user


class ProgramManagerAdmin(HijackUserAdminMixin, EducationGroupRoleModelAdmin):
    list_select_related = ['person__user']
    list_display = ['person', 'education_group_most_recent_acronym']

    def get_hijack_user(self, obj):
        return obj.person.user


class WorkingListForm(forms.ModelForm):
    checklist_filters = ChecklistStateFilterField(
        configurations=ORGANISATION_ONGLETS_CHECKLIST,
        label=_('Checklist filters'),
        required=False,
    )

    admission_statuses = forms.TypedMultipleChoiceField(
        label=_('Admission statuses'),
        required=False,
        choices=CHOIX_STATUT_TOUTE_PROPOSITION,
    )

    class Meta:
        model = WorkingList
        fields = '__all__'


class WorkingListAdmin(OrderedModelAdmin):
    list_display = ['translated_name', 'move_up_down_links', 'order']
    search_fields = ['name']
    form = WorkingListForm

    @admin.display(description=_('Name'))
    def translated_name(self, obj):
        return obj.name.get(get_language())

    class Media:
        css = {
            'all': [
                'admission/working_list_admin.css',
            ],
        }


class CategorizedFreeDocumentAdmin(admin.ModelAdmin):
    model = CategorizedFreeDocument
    list_display = [
        'short_label_fr',
        'checklist_tab',
        'admission_context',
    ]
    list_filter = [
        ('checklist_tab', admin.EmptyFieldListFilter),
        'checklist_tab',
        'admission_context',
    ]
    search_fields = [
        'short_label_en',
        'short_label_fr',
    ]


admin.site.register(CategorizedFreeDocument, CategorizedFreeDocumentAdmin)
admin.site.register(WorkingList, WorkingListAdmin)
admin.site.register(Promoter, FrontOfficeRoleModelAdmin)
admin.site.register(CommitteeMember, FrontOfficeRoleModelAdmin)
admin.site.register(Candidate, CandidateAdmin)

admin.site.register(CddConfigurator, CddConfiguratorAdmin)

admin.site.register(CentralManager, CentralManagerAdmin)
admin.site.register(ProgramManager, ProgramManagerAdmin)
admin.site.register(SicManagement, HijackEntityRoleModelAdmin)
admin.site.register(AdreSecretary, HijackRoleModelAdmin)
admin.site.register(JurySecretary, HijackRoleModelAdmin)
admin.site.register(Sceb, HijackRoleModelAdmin)
admin.site.register(DoctorateReader, HijackRoleModelAdmin)
admin.site.register(EPCInjection, EPCInjectionAdmin)
