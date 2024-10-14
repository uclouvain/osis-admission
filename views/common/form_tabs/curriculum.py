# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import uuid
from typing import Union, List
from uuid import UUID

from django.contrib import messages
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import ProtectedError, QuerySet, OuterRef, Exists, Q
from django.forms import forms
from django.shortcuts import redirect, get_object_or_404, resolve_url
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.models import EPCInjection as AdmissionEPCInjection
from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.checklist import FreeAdditionalApprovalCondition
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.utils import copy_documents
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from osis_profile.models import ProfessionalExperience, EducationalExperience, EducationalExperienceYear
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from osis_profile.views.delete_experience_academique import DeleteExperienceAcademiqueView
from osis_profile.views.delete_experience_non_academique import DeleteExperienceNonAcademiqueView
from osis_profile.views.edit_experience_academique import EditExperienceAcademiqueView
from osis_profile.views.edit_experience_non_academique import EditExperienceNonAcademiqueView
from osis_profile.views.parcours_externe_mixins import DeleteEducationalExperienceMixin

__all__ = [
    'CurriculumEducationalExperienceFormView',
    'CurriculumEducationalExperienceDeleteView',
    'CurriculumEducationalExperienceDuplicateView',
    'CurriculumEducationalExperienceValuateView',
    'CurriculumNonEducationalExperienceFormView',
    'CurriculumNonEducationalExperienceDeleteView',
    'CurriculumNonEducationalExperienceDuplicateView',
    'CurriculumNonEducationalExperienceValuateView',
]


__namespace__ = 'curriculum'


class CurriculumEducationalExperienceFormView(AdmissionFormMixin, LoadDossierViewMixin, EditExperienceAcademiqueView):
    urlpatterns = {
        'educational': 'educational/<uuid:experience_uuid>',
        'educational_create': 'educational/create',
    }
    template_name = 'admission/forms/curriculum_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
    update_admission_author = True

    def has_permission(self):
        return super().has_permission() and (
            not self.educational_experience
            or not any(
                getattr(self.educational_experience, field)
                for field in ['external_id', 'cv_injection', 'admission_injection']
            )
        )

    def traitement_specifique(self, experience_uuid: UUID, experiences_supprimees: List[UUID] = None):
        pass

    @property
    def educational_experience_filter_uuid(self):
        return {'uuid': self.experience_id}

    @property
    def educational_experience_annotations(self):
        return {
            'admission_injection': Exists(
                AdmissionEPCInjection.objects.filter(
                    admission__admissioneducationalvaluatedexperiences__educationalexperience_id=OuterRef('uuid'),
                    type=EPCInjectionType.DEMANDE.name,
                    status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
            'cv_injection': Exists(
                CurriculumEPCInjection.objects.filter(
                    experience_uuid=OuterRef('uuid'),
                    status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
        }

    def traitement_specifique_de_creation(self):
        # Consider the experience as valuated
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission_id=self.admission.uuid,
            educationalexperience_id=self._experience_id,
        )
        # Add the experience to the checklist
        if 'current' in self.admission.checklist and 'parcours_anterieur' in self.admission.checklist['current']:
            admission = self.admission
            experience_checklist = Checklist.initialiser_checklist_experience(self._experience_id).to_dict()
            admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
            admission.save(update_fields=['checklist'])

    @property
    def person(self):
        return self.admission.candidate

    def get_success_url(self):
        if self.next_url:
            return self.next_url

        if self.is_general:
            return resolve_url(
                f'{self.base_namespace}:update:curriculum:educational',
                uuid=self.admission_uuid,
                experience_uuid=self.experience_id,
            )

        return resolve_url(f'{self.base_namespace}:curriculum', uuid=self.admission_uuid)

    def delete_url(self):
        if self.experience_id:
            return resolve_url(
                f'{self.base_namespace}:update:curriculum:educational_delete',
                uuid=self.admission_uuid,
                experience_uuid=self.experience_id,
            )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.is_continuing or self.is_doctorate:
            context_data['next_url'] = self.get_success_url()
            context_data['prevent_quitting_template'] = 'admission/includes/back_to_cv_overview_link.html'
        else:
            context_data['prevent_quitting_template'] = 'admission/includes/prevent_quitting_button.html'

        return context_data


class CurriculumNonEducationalExperienceFormView(
    AdmissionFormMixin,
    LoadDossierViewMixin,
    EditExperienceNonAcademiqueView,
):
    urlpatterns = {
        'non_educational': 'non_educational/<uuid:experience_uuid>',
        'non_educational_create': 'non_educational/create',
    }
    template_name = 'admission/forms/curriculum_non_educational_experience.html'
    permission_required = 'admission.change_admission_curriculum'
    update_admission_author = True

    @property
    def non_educational_experience_annotations(self):
        return {
            'admission_injection': Exists(
                AdmissionEPCInjection.objects.filter(
                    admission__admissionprofessionalvaluatedexperiences__professionalexperience_id=OuterRef('uuid'),
                    type=EPCInjectionType.DEMANDE.name,
                    status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
            'cv_injection': Exists(
                CurriculumEPCInjection.objects.filter(
                    experience_uuid=OuterRef('uuid'),
                    status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
        }

    def has_permission(self):
        return super().has_permission() and (
            not self.non_educational_experience
            or not any(
                getattr(self.non_educational_experience, field)
                for field in ['external_id', 'cv_injection', 'admission_injection']
            )
        )

    def traitement_specifique(self, experience_uuid: UUID, experiences_supprimees: List[UUID] = None):
        pass

    @property
    def person(self):
        return self.admission.candidate

    def traitement_specifique_de_creation(self):
        # Consider the experience as valuated
        AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission_id=self.admission.uuid,
            professionalexperience_id=self._experience_id,
        )
        # Add the experience to the checklist
        if 'current' in self.admission.checklist and 'parcours_anterieur' in self.admission.checklist['current']:
            admission = self.admission
            experience_checklist = Checklist.initialiser_checklist_experience(self._experience_id).to_dict()
            admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)
            admission.save(update_fields=['checklist'])

    def get_success_url(self):
        if self.next_url:
            return self.next_url

        if self.is_general:
            return resolve_url(
                f'{self.base_namespace}:update:curriculum:non_educational',
                uuid=self.admission_uuid,
                experience_uuid=self.experience_id,
            )

        return resolve_url(f'{self.base_namespace}:curriculum', uuid=self.admission_uuid)

    def delete_url(self):
        if self.experience_id:
            return resolve_url(
                f'{self.base_namespace}:update:curriculum:non_educational_delete',
                uuid=self.admission_uuid,
                experience_uuid=self.experience_id,
            )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.is_continuing or self.is_doctorate:
            context_data['next_url'] = self.get_success_url()
            context_data['prevent_quitting_template'] = 'admission/includes/back_to_cv_overview_link.html'
        else:
            context_data['prevent_quitting_template'] = 'admission/includes/prevent_quitting_button.html'

        return context_data


class CurriculumBaseDeleteView(LoadDossierViewMixin, DeleteEducationalExperienceMixin):
    permission_required = 'admission.delete_admission_curriculum'
    template_name = 'admission/empty_template.html'

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                cv_injection=Exists(
                    CurriculumEPCInjection.objects.filter(
                        experience_uuid=self.experience_id,
                        status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                    ),
                ),
            )
        )

    def has_permission(self):
        self.object = self.get_object()
        return super().has_permission() and not any(
            getattr(self.object, field) for field in ['external_id', 'cv_injection', 'admission_injection']
        )

    @property
    def person(self):
        return self.admission.candidate

    def delete(self, request, *args, **kwargs):
        # Delete the experience
        try:
            delete = super().delete(request, *args, **kwargs)
        except ProtectedError as e:
            free_approval_condition = next(
                (obj for obj in e.protected_objects if isinstance(obj, FreeAdditionalApprovalCondition)),
                None,
            )
            error_message = (
                _(
                    'Cannot delete the experience because it is used as additional condition for the '
                    'proposition {admission}.'.format(admission=free_approval_condition.admission)
                )
                if free_approval_condition
                else _('Cannot delete the experience because it is used in another context.')
            )
            messages.error(self.request, error_message)
            return redirect(self.next_url or self.get_failure_url())

        # Delete the information of the experience from the checklist
        admission: BaseAdmission = self.admission

        if 'current' in admission.checklist and 'parcours_anterieur' in admission.checklist['current']:
            experiences = admission.checklist['current']['parcours_anterieur']['enfants']

            experience_uuid = str(self.kwargs.get('experience_uuid'))

            for index, experience in enumerate(experiences):
                if experience.get('extra', {}).get('identifiant') == experience_uuid:
                    experiences.pop(index)
                    break

        admission.last_update_author = self.request.user.person

        admission.save()

        return delete

    def get_success_url(self):
        kwargs = {
            'uuid': self.admission_uuid,
        }
        return (
            self.next_url or reverse(f'{self.base_namespace}:checklist', kwargs=kwargs)
            if self.is_general
            else reverse(f'{self.base_namespace}:curriculum', kwargs=kwargs)
        )


class CurriculumEducationalExperienceDeleteView(CurriculumBaseDeleteView, DeleteExperienceAcademiqueView):
    urlpatterns = {'educational_delete': 'educational/<uuid:experience_uuid>/delete'}

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                admission_injection=Exists(
                    AdmissionEPCInjection.objects.filter(
                        admission__admissioneducationalvaluatedexperiences__educationalexperience_id=OuterRef('uuid'),
                        type=EPCInjectionType.DEMANDE.name,
                        status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
            )
        )

    def traitement_specifique(self, experience_uuid: UUID, experiences_supprimees: List[UUID]):
        pass

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumNonEducationalExperienceDeleteView(CurriculumBaseDeleteView, DeleteExperienceNonAcademiqueView):
    urlpatterns = {'non_educational_delete': 'non_educational/<uuid:experience_uuid>/delete'}

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                admission_injection=Exists(
                    AdmissionEPCInjection.objects.filter(
                        admission__admissionprofessionalvaluatedexperiences__professionalexperience_id=OuterRef('uuid'),
                        type=EPCInjectionType.DEMANDE.name,
                        status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
            )
        )

    def traitement_specifique(self, experience_uuid: UUID, experiences_supprimees: List[UUID]):
        pass

    def get_failure_url(self):
        return reverse(
            self.base_namespace + ':update:curriculum:non_educational',
            kwargs={
                'uuid': self.admission_uuid,
                'experience_uuid': self.experience_id,
            },
        )


class CurriculumBaseExperienceDuplicateView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    """
    View to duplicate a curriculum experience.
    """

    permission_required = 'admission.change_admission_curriculum'
    slug_field = 'uuid'
    slug_url_kwarg = 'experience_uuid'
    template_name = 'admission/empty_template.html'
    form_class = forms.Form
    update_admission_author = True

    experience_model = None  # Name of the model of the experience to duplicate
    valuated_experience_model = None  # Name of the model of the valuated experience
    valuated_experience_field_id_name = None  # Name of the field of the experience in the valuated experience model

    @property
    def experience_id(self):
        return self.kwargs.get('experience_uuid', None)

    def additional_duplications(self, duplicated_experience):
        """
        Create additional objects that must be duplicated in addition to the duplicated experience.
        :param duplicated_experience: The duplicated experience.
        :return: The list of additional objects.
        """
        return []

    def additional_duplications_save(self, duplicated_objects):
        """
        Save additional objects that must be duplicated in addition to the duplicated experience.
        :param duplicated_objects: The list of additional objects returned by the 'additional_duplications' method.
        """
        pass

    def form_valid(self, form):
        # Retrieve the experience to duplicate
        duplicated_experience = get_object_or_404(
            self.experience_model.objects.select_related('person'),
            uuid=self.experience_id,
        )

        # Retrieve the valuations of the experience to duplicate
        valuated_admissions: QuerySet[
            Union[AdmissionProfessionalValuatedExperiences, AdmissionEducationalValuatedExperiences]
        ] = self.valuated_experience_model.objects.filter(
            **{self.valuated_experience_field_id_name: self.experience_id}
        ).select_related(
            'baseadmission'
        )

        # Initialize the new experience
        duplicated_experience.pk = None
        duplicated_experience.external_id = None
        duplicated_experience.uuid = uuid.uuid4()
        duplicated_experience._state_adding = True

        # Initialize the sub models if necessary
        additional_duplications = self.additional_duplications(duplicated_experience=duplicated_experience)

        all_duplications = [duplicated_experience]

        if additional_duplications:
            all_duplications += additional_duplications

        # Make a copy of all documents and affect them to the new experience and to the sub models, if any
        copy_documents(all_duplications)

        # Save the new experience
        duplicated_experience.save()

        # Save the sub models, if any
        self.additional_duplications_save(additional_duplications)

        initial_checklist = Checklist.initialiser_checklist_experience(duplicated_experience.uuid).to_dict()

        new_valuations = []
        admissions_to_update = []

        # Loop over the valuated admissions by the experience
        for current_valuation in valuated_admissions:

            # Initialize the valuation of the admission by the new experience
            new_valuations.append(
                self.valuated_experience_model(
                    **{
                        'baseadmission_id': current_valuation.baseadmission_id,
                        self.valuated_experience_field_id_name: duplicated_experience.uuid,
                    },
                )
            )

            # Initialize the checklist of the duplicated experience
            admission_experience_checklists = (
                current_valuation.baseadmission.checklist.get('current', {})
                .get('parcours_anterieur', {})
                .get('enfants')
            )
            if admission_experience_checklists is not None:
                admission_experience_checklists.append(initial_checklist)
                admissions_to_update.append(current_valuation.baseadmission)

        if new_valuations:
            self.valuated_experience_model.objects.bulk_create(new_valuations)

        if admissions_to_update:
            BaseAdmission.objects.bulk_update(admissions_to_update, ['checklist'])

        return super().form_valid(form)

    def get_success_url(self):
        kwargs = {
            'uuid': self.admission_uuid,
        }
        return (
            self.next_url or reverse(f'{self.base_namespace}:checklist', kwargs=kwargs)
            if self.is_general
            else reverse(f'{self.base_namespace}:curriculum', kwargs=kwargs)
        )


class CurriculumNonEducationalExperienceDuplicateView(CurriculumBaseExperienceDuplicateView):
    """
    View to duplicate a professional experience.
    """

    urlpatterns = {'non_educational_duplicate': 'non_educational/<uuid:experience_uuid>/duplicate'}
    experience_model = ProfessionalExperience
    valuated_experience_model = AdmissionProfessionalValuatedExperiences
    valuated_experience_field_id_name = 'professionalexperience_id'


class CurriculumEducationalExperienceDuplicateView(CurriculumBaseExperienceDuplicateView):
    """
    View to duplicate an educational experience.
    """

    urlpatterns = {'educational_duplicate': 'educational/<uuid:experience_uuid>/duplicate'}
    experience_model = EducationalExperience
    valuated_experience_model = AdmissionEducationalValuatedExperiences
    valuated_experience_field_id_name = 'educationalexperience_id'

    def additional_duplications(self, duplicated_experience):
        experience_years = EducationalExperienceYear.objects.filter(
            educational_experience__uuid=self.experience_id
        ).select_related('educational_experience__person')

        for duplicated_experience_year in experience_years:
            duplicated_experience_year.pk = None
            duplicated_experience_year.external_id = None
            duplicated_experience_year._state_adding = True
            duplicated_experience_year.uuid = uuid.uuid4()
            duplicated_experience_year.educational_experience = duplicated_experience

        return experience_years

    def additional_duplications_save(self, duplicated_objects):
        EducationalExperienceYear.objects.bulk_create(duplicated_objects)


class CurriculumBaseExperienceValuateView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    permission_required = 'admission.change_admission_curriculum'
    form_class = forms.Form
    experience_model = None
    valuated_experience_model = None
    valuated_experience_field_id_name = None
    update_admission_author = True
    message_on_success = _('The experience has been valuated.')

    @cached_property
    def experience(self) -> Union[EducationalExperience, ProfessionalExperience]:
        return get_object_or_404(self.experience_model, uuid=self.experience_id)

    @property
    def experience_id(self):
        return str(self.kwargs.get('experience_uuid', None))

    def get_success_url(self):
        return self.next_url or reverse(self.base_namespace + ':checklist', kwargs={'uuid': self.admission_uuid})

    def form_valid(self, form):
        self.valuated_experience_model.objects.create(
            baseadmission=self.admission,
            **{self.valuated_experience_field_id_name: self.experience.uuid},
        )
        return super().form_valid(form)

    def update_current_admission_on_form_valid(self, form, admission):
        # Add the experience to the checklist if it's not already there
        if (
            'current' in admission.checklist
            and 'parcours_anterieur' in admission.checklist['current']
            and not any(
                experience
                for experience in admission.checklist['current']['parcours_anterieur']['enfants']
                if experience.get('extra', {}).get('identifiant') == self.experience_id
            )
        ):
            experience_checklist = Checklist.initialiser_checklist_experience(self.experience_id).to_dict()
            admission.checklist['current']['parcours_anterieur']['enfants'].append(experience_checklist)


class CurriculumNonEducationalExperienceValuateView(CurriculumBaseExperienceValuateView):
    urlpatterns = {'non_educational_valuate': 'non_educational/<uuid:experience_uuid>/valuate'}
    experience_model = ProfessionalExperience
    valuated_experience_model = AdmissionProfessionalValuatedExperiences
    valuated_experience_field_id_name = 'professionalexperience_id'


class CurriculumEducationalExperienceValuateView(CurriculumBaseExperienceValuateView):
    urlpatterns = {'educational_valuate': 'educational/<uuid:experience_uuid>/valuate'}
    experience_model = EducationalExperience
    valuated_experience_model = AdmissionEducationalValuatedExperiences
    valuated_experience_field_id_name = 'educationalexperience_id'
