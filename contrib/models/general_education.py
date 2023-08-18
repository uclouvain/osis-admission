# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from contextlib import suppress

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import api_settings

from admission.constants import PDF_MIME_TYPE
from admission.contrib.models.base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path
from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    PoursuiteDeCycle,
)
from base.models.academic_year import AcademicYear
from base.models.person import Person
from osis_common.ddd.interface import BusinessException
from osis_document.contrib import FileField


class GeneralEducationAdmission(BaseAdmission):
    status = models.CharField(
        choices=ChoixStatutPropositionGenerale.choices(),
        max_length=30,
        default=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
    )

    double_degree_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("Dual degree scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    international_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("International scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    erasmus_mundus_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("Erasmus Mundus scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_belgian_bachelor = models.BooleanField(
        verbose_name=_("Is belgian bachelor"),
        null=True,
    )
    is_external_reorientation = models.BooleanField(
        verbose_name=_("Is an external reorientation"),
        null=True,
    )
    registration_change_form = FileField(
        verbose_name=_("Change of enrolment form"),
        max_files=1,
        upload_to=admission_directory_path,
        blank=True,
    )
    is_external_modification = models.BooleanField(
        verbose_name=_("Is an external modification"),
        null=True,
    )
    regular_registration_proof = FileField(
        verbose_name=_("Proof of regular registration"),
        max_files=1,
        upload_to=admission_directory_path,
        blank=True,
    )
    is_non_resident = models.BooleanField(
        verbose_name=_("Is non-resident (as defined in decree)"),
        null=True,
    )

    diploma_equivalence = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Diploma equivalence'),
    )
    late_enrollment = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Late enrollment'),
    )
    cycle_pursuit = models.CharField(
        choices=PoursuiteDeCycle.choices(),
        max_length=30,
        default=PoursuiteDeCycle.TO_BE_DETERMINED.name,
    )
    additional_documents = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Additional documents'),
    )

    # Fac approval
    fac_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Approval certificate of faculty'),
        mimetypes=[PDF_MIME_TYPE],
    )
    fac_refusal_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Refusal certificate of faculty'),
        mimetypes=[PDF_MIME_TYPE],
    )
    fac_refusal_reason = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        to='admission.RefusalReason',
        verbose_name=_('Faculty refusal reason'),
    )
    other_fac_refusal_reason = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Other faculty refusal reason'),
    )
    with_additional_approval_conditions = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are there any additional conditions (subject to ...)?'),
    )
    additional_approval_conditions = models.ManyToManyField(
        blank=True,
        related_name='+',
        to='admission.AdditionalApprovalCondition',
        verbose_name=_('Additional approval conditions'),
    )
    free_additional_approval_conditions = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        default=list,
        verbose_name=_('Free additional approval conditions'),
    )
    other_training_accepted_by_fac = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
        to='base.EducationGroupYear',
        verbose_name=_('Other course accepted by the faculty'),
    )
    with_prerequisite_courses = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are there any prerequisite courses?'),
    )
    prerequisite_courses = models.ManyToManyField(
        to='base.LearningUnitYear',
        blank=True,
        through='AdmissionPrerequisiteCourses',
        through_fields=(
            'admission',
            'course',
        ),
        verbose_name=_('Prerequisite courses'),
    )
    prerequisite_courses_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Other information about prerequisite courses'),
    )
    program_planned_years_number = models.SmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Number of years required for the full program (including prerequisite courses)'),
        validators=[MinValueValidator(DUREE_MINIMALE_PROGRAMME), MaxValueValidator(DUREE_MAXIMALE_PROGRAMME)],
    )
    annual_program_contact_person_name = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Name of the contact person for the design of the annual program'),
    )
    annual_program_contact_person_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=_('Email of the contact person for the design of the annual program'),
    )
    join_program_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Faculty comment about the collaborative program'),
    )

    class Meta:
        verbose_name = _("General education admission")
        ordering = ('-created_at',)
        permissions = []

    def update_detailed_status(self, author: 'Person' = None):
        """Gather exceptions from verification and update determined pool and academic year"""
        from admission.ddd.admission.formation_generale.commands import (
            VerifierPropositionQuery,
            DeterminerAnneeAcademiqueEtPotQuery,
        )
        from admission.utils import gather_business_exceptions
        from infrastructure.messages_bus import message_bus_instance

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        self.detailed_status = gather_business_exceptions(VerifierPropositionQuery(self.uuid)).get(error_key, [])
        self.last_update_author = author

        update_fields = [
            'detailed_status',
            'determined_academic_year',
            'determined_pool',
        ]

        if author:
            self.last_update_author = author
            update_fields.append('last_update_author')

        with suppress(BusinessException):
            dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(DeterminerAnneeAcademiqueEtPotQuery(self.uuid))
            self.determined_academic_year = AcademicYear.objects.get(year=dto.annee)
            self.determined_pool = dto.pool.name

        self.save(update_fields=update_fields)

    def update_requested_documents(self):
        """Update the requested documents depending on the admission data."""
        from admission.ddd.admission.formation_generale.commands import (
            RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(RecalculerEmplacementsDocumentsNonLibresPropositionCommand(self.uuid))


class AdmissionPrerequisiteCourses(models.Model):
    """Prerequisite courses of an admission."""

    admission = models.ForeignKey(
        GeneralEducationAdmission,
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        'base.LearningUnitYear',
        on_delete=models.PROTECT,
        related_name='+',
        to_field='uuid',
    )


class GeneralEducationAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "candidate__country_of_citizenship",
                "training__academic_year",
                "training__education_group_type",
                "determined_academic_year",
                "double_degree_scholarship",
                "international_scholarship",
                "erasmus_mundus_scholarship",
                "fac_refusal_reason",
            )
            .annotate_pool_end_date()
        )

    def for_dto(self):
        return (
            self.get_queryset()
            .select_related(
                "training__main_domain",
                "training__enrollment_campus",
            )
            .annotate_campus()
            .annotate_training_management_entity()
            .annotate_training_management_faculty()
            .annotate_with_reference()
        )

    def for_manager_dto(self):
        return self.for_dto().annotate_campus(
            training_field='other_training_accepted_by_fac',
            annotation_name='other_training_accepted_by_fac_teaching_campus',
        )


class GeneralEducationAdmissionProxy(GeneralEducationAdmission):
    """Proxy model of base.GeneralEducationAdmission"""

    objects = GeneralEducationAdmissionManager()

    class Meta:
        proxy = True
