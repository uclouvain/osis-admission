##############################################################################
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
##############################################################################
import itertools
import uuid
from typing import Dict, Set

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import StringAgg
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, IntegrityError
from django.db.models import OuterRef, Subquery, Q, F, Value, CharField, When, Case, BooleanField, Count, IntegerField
from django.db.models.fields.json import KeyTextTransform, KeyTransform
from django.db.models.functions import Concat, Coalesce, NullIf, Mod, Replace, JSONObject
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, get_language, pgettext_lazy
from osis_comment.models import CommentDeleteMixin
from osis_history.models import HistoryEntry

from admission.constants import (
    ADMISSION_POOL_ACADEMIC_CALENDAR_TYPES,
    CONTEXT_DOCTORATE,
    CONTEXT_GENERAL,
    CONTEXT_CONTINUING,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE,
    STATUTS_PROPOSITION_DOCTORALE_PEU_AVANCEE,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import (
    STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE,
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE,
)
from admission.ddd.admission.repository.i_proposition import CAMPUS_LETTRE_DOSSIER
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
    ADMISSION_CONTEXT_BY_ALL_OSIS_EDUCATION_TYPE,
)
from admission.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.models.form_item import ConfigurableModelFormItemField
from admission.models.functions import ToChar
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion, PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeStatus
from base.models.student import Student
from base.utils.cte import CTESubquery
from education_group.contrib.models import EducationGroupRoleModel
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from osis_document.contrib import FileField
from osis_role.contrib.models import EntityRoleModel
from osis_role.contrib.permissions import _get_relevant_roles
from program_management.models.education_group_version import EducationGroupVersion
from reference.models.country import Country

REFERENCE_SEQ_NAME = 'admission_baseadmission_reference_seq'


def admission_directory_path(admission: 'BaseAdmission', filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/{}'.format(
        admission.candidate.uuid,
        admission.uuid,
        filename,
    )


def training_campus_subquery(training_field: str):
    return Subquery(
        EducationGroupVersion.objects.filter(offer_id=OuterRef(training_field))
        .annotate(
            campus_name=StringAgg(
                'root_group__main_teaching_campus__name',
                delimiter=',',
                distinct=True,
            )
        )
        .values('campus_name')[:1]
    )


def teaching_campus_subquery(training_field: str):
    return Subquery(
        EducationGroupVersion.standard.filter(offer_id=OuterRef(training_field), transition_name='')
        .select_related('root_group__main_teaching_campus__country')
        .annotate(
            main_teaching_campus=JSONObject(
                uuid=F('root_group__main_teaching_campus__uuid'),
                name=F('root_group__main_teaching_campus__name'),
                postal_code=F('root_group__main_teaching_campus__postal_code'),
                city=F('root_group__main_teaching_campus__city'),
                country_code=Coalesce(F('root_group__main_teaching_campus__country__iso_code'), Value('')),
                fr_country_name=Coalesce(F('root_group__main_teaching_campus__country__name'), Value('')),
                en_country_name=Coalesce(F('root_group__main_teaching_campus__country__name_en'), Value('')),
                street=F('root_group__main_teaching_campus__street'),
                street_number=F('root_group__main_teaching_campus__street_number'),
                postal_box=F('root_group__main_teaching_campus__postal_box'),
                location=F('root_group__main_teaching_campus__location'),
                sic_enrollment_email=F('root_group__main_teaching_campus__sic_enrollment_email'),
            )
        )
        .values('main_teaching_campus')[:1]
    )


class BaseAdmissionQuerySet(models.QuerySet):
    def annotate_campus(self, training_field='training_id', annotation_name='teaching_campus'):
        """
        Annotate the queryset with the teaching campus.
        @param training_field: the name of the training field in the model
        @param annotation_name: the name of the output annotation
        """
        return self.annotate(**{annotation_name: training_campus_subquery(training_field)})

    def annotate_campus_info(self, training_field='training_id', annotation_name='teaching_campus_info'):
        """
        Annotate the queryset with the teaching campus information.
        @param training_field: the name of the training field in the model
        @param annotation_name: the name of the output annotation
        """
        return self.annotate(**{annotation_name: teaching_campus_subquery(training_field)})

    def annotate_pool_end_date(self):
        today = timezone.now().today()
        return self.annotate(
            pool_end_date=models.Subquery(
                AcademicCalendar.objects.filter(
                    reference=OuterRef('determined_pool'),
                    start_date__lte=today,
                    end_date__gte=today,
                ).values('end_date')[:1],
            ),
        )

    def annotate_training_management_entity(self):
        return self.annotate(
            sigle_entite_gestion=models.Subquery(
                EntityVersion.objects.filter(entity_id=OuterRef("training__management_entity_id"))
                .order_by('-start_date')
                .values("acronym")[:1]
            ),
            title_entite_gestion=models.Subquery(
                EntityVersion.objects.filter(entity_id=OuterRef("training__management_entity_id"))
                .order_by('-start_date')
                .values("title")[:1]
            ),
        )

    def annotate_last_status_update(self):
        return self.annotate(
            status_updated_at=Subquery(
                HistoryEntry.objects.filter(
                    object_uuid=OuterRef('uuid'),
                    tags__contains=['proposition', 'status-changed'],
                ).values('created')[:1]
            ),
        )

    def annotate_with_student_registration_id(self):
        return self.annotate(
            person_merge_proposal_noma=F('candidate__personmergeproposal__registration_id_sent_to_digit'),
            existing_student_noma=models.Subquery(
                Student.objects.filter(person_id=OuterRef('candidate_id'),).values(
                    'registration_id'
                )[:1]
            ),
        ).annotate(
            student_registration_id=Case(
                When(person_merge_proposal_noma__isnull=False, then='person_merge_proposal_noma'),
                When(existing_student_noma__isnull=False, then='existing_student_noma'),
                default=Value(''),
            )
        )

    def annotate_training_management_faculty(self):
        today = timezone.now().today()
        cte = EntityVersion.objects.with_children(entity_id=OuterRef("training__management_entity_id"))
        faculty = (
            cte.join(EntityVersion, id=cte.col.id)
            .with_cte(cte)
            .filter(Q(entity_type=EntityType.FACULTY.name) | Q(acronym__in=PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS))
            .exclude(end_date__lte=today)
        )

        return self.annotate(training_management_faculty=CTESubquery(faculty.values("acronym")[:1]))

    def annotate_with_reference(self, with_management_faculty=True):
        """
        Annotate the admission with its reference.
        Note that the query must previously be annotate with 'training_management_faculty' and 'sigle_entite_gestion'.
        """
        return self.annotate(
            formatted_reference=Concat(
                # Letter of the campus
                Case(
                    *(
                        When(Q(training__enrollment_campus__name__icontains=name), then=Value(letter))
                        for name, letter in CAMPUS_LETTRE_DOSSIER.items()
                    )
                ),
                Value('-'),
                # Management entity acronym
                Case(
                    When(
                        Q(training__education_group_type__name=TrainingType.PHD.name),
                        then=F('sigle_entite_gestion'),
                    ),
                    default=Coalesce(
                        NullIf(F('training_management_faculty'), Value('')),
                        F('sigle_entite_gestion'),
                    ),
                )
                if with_management_faculty
                else F('sigle_entite_gestion'),
                # Academic year
                Case(
                    # Before the submission, use the determined academic year if specified
                    When(
                        Q(submitted_at__isnull=True) & Q(determined_academic_year__isnull=False),
                        then=Mod('determined_academic_year__year', 100),
                    ),
                    # Otherwise, use the training academic year
                    default=Mod('training__academic_year__year', 100),
                ),
                Value('-'),
                # Formatted numero (e.g. 12 -> 000.012)
                Replace(ToChar(F('reference'), Value('fm9999,0000,0000')), Value(','), Value('.')),
                output_field=CharField(),
            )
        )

    def filter_submitted_only(self):
        return self.exclude(
            Q(generaleducationadmission__status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE)
            | Q(continuingeducationadmission__status__in=STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE)
            | Q(doctorateadmission__status__in=STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE),
        )

    def annotate_ordered_enum(self, field_name, ordering_field_name, enum_class):
        """
        Annotate the queryset with an equivalent numeric version of an enum field.
        :param field_name: The name of the enum field
        :param ordering_field_name: The name of the output field
        :param enum_class: The enum class
        :return: The annotated queryset
        """
        return self.annotate(
            **{
                ordering_field_name: Case(
                    *(When(**{field_name: member.name}, then=i) for i, member in enumerate(enum_class)),
                    output_field=IntegerField(),
                )
            },
        )

    def annotate_several_admissions_in_progress(self):
        return self.alias(
            admissions_in_progress_nb=Subquery(
                BaseAdmission.objects.filter(
                    candidate_id=OuterRef("candidate_id"),
                    determined_academic_year_id=OuterRef("determined_academic_year_id"),
                )
                .exclude(
                    Q(
                        generaleducationadmission__status__in=(
                            STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE
                        )
                    )
                    | Q(continuingeducationadmission__status__in=STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE)
                    | Q(doctorateadmission__status__in=STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE),
                )
                .values('candidate_id')
                .annotate(count=Count('pk'))
                .values('count')[:1],
            ),
        ).annotate(
            has_several_admissions_in_progress=Case(
                When(
                    Q(admissions_in_progress_nb__gt=1),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

    def annotate_with_status_update_date(self):
        return self.annotate(
            status_updated_at=Subquery(
                HistoryEntry.objects.filter(
                    object_uuid=OuterRef('uuid'),
                    tags__contains=['proposition', 'status-changed'],
                ).values('created')[:1]
            )
        )

    def filter_according_to_roles(self, demandeur_uuid, permission='admission.view_enrolment_application'):
        demandeur_user = User.objects.filter(person__uuid=demandeur_uuid).first()

        roles = _get_relevant_roles(demandeur_user, permission)

        # Filter managed entities
        entities_conditions = Q()
        for entity_aware_role in [r for r in roles if issubclass(r, EntityRoleModel)]:
            entities_conditions |= Q(
                training__management_entity_id__in=entity_aware_role.objects.filter(
                    person__uuid=demandeur_uuid
                ).get_entities_ids()
            )

        # Filter managed education groups
        education_group_conditions = Q()
        for education_aware_role in [r for r in roles if issubclass(r, EducationGroupRoleModel)]:
            education_group_conditions |= Q(
                training__education_group_id__in=education_aware_role.objects.filter(
                    person__uuid=demandeur_uuid
                ).values_list('education_group_id')
            )

        return self.filter(entities_conditions | education_group_conditions)

    def filter_in_quarantine(self):
        return self.filter(
            Q(candidate__personmergeproposal__isnull=False)
            & Q(
                Q(candidate__personmergeproposal__status__in=PersonMergeStatus.quarantine_statuses())
                |
                # Cas validation ticket Digit en erreur
                ~Q(candidate__personmergeproposal__validation__valid=True)
            )
        )

    def annotate_submitted_profile_countries_names(self):
        """
        Annotate the admission with the names of the countries specified in the submitted profile of the candidate.
        """
        country_title_field = 'name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en'

        return self.alias(
            # TODO to be simplified with the KT operator (>= Django 4.2)
            submitted_profile_country_of_citizenship=KeyTextTransform(
                'country_of_citizenship',
                KeyTransform('identification', 'submitted_profile'),
            ),
            submitted_profile_country=KeyTextTransform(
                'country',
                KeyTransform('coordinates', 'submitted_profile'),
            ),
        ).annotate(
            submitted_profile_country_of_citizenship_name=models.Subquery(
                Country.objects.filter(iso_code=OuterRef('submitted_profile_country_of_citizenship')).values(
                    country_title_field
                )[:1]
            ),
            submitted_profile_country_name=models.Subquery(
                Country.objects.filter(iso_code=OuterRef('submitted_profile_country')).values(country_title_field)[:1]
            ),
        )


class BaseAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def with_training_management_and_reference(self):
        return (
            self.get_queryset()
            .annotate_training_management_entity()
            .annotate_training_management_faculty()
            .annotate_with_reference()
            .annotate_campus()
        )

    def candidate_has_submission(self, candidate: Person):
        return (
            self.get_queryset()
            .filter(
                candidate=candidate,
            )
            .filter_submitted_only()
            .exists()
        )


class BaseAdmission(CommentDeleteMixin, models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Candidate"),
        related_name="%(class)ss",
        on_delete=models.PROTECT,
        editable=False,
    )
    type_demande = models.CharField(
        verbose_name=_("Type"),
        max_length=255,
        choices=TypeDemande.choices(),
        db_index=True,
        default=TypeDemande.ADMISSION.name,
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
        blank=True,
    )

    created_at = models.DateTimeField(verbose_name=_('Created'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=pgettext_lazy('feminine', 'Modified'), auto_now=True)

    professional_valuated_experiences = models.ManyToManyField(
        'osis_profile.ProfessionalExperience',
        blank=True,
        related_name='valuated_from_admission',
        verbose_name=_('The professional experiences that have been valuated from this admission.'),
        through='AdmissionProfessionalValuatedExperiences',
    )
    educational_valuated_experiences = models.ManyToManyField(
        'osis_profile.EducationalExperience',
        blank=True,
        related_name='valuated_from_admission',
        verbose_name=_('The educational experiences that have been valuated from this admission.'),
        through='AdmissionEducationalValuatedExperiences',
    )
    internal_access_titles = models.ManyToManyField(
        'epc.InscriptionProgrammeCycle',
        blank=True,
        related_name='+',
        verbose_name=_('The internal experiences chosen as access titles of this admission.'),
    )
    detailed_status = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    training = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=pgettext_lazy("admission", "Course"),
        related_name="+",
        on_delete=models.CASCADE,
    )
    determined_academic_year = models.ForeignKey(
        to="base.AcademicYear",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    determined_pool = models.CharField(
        choices=tuple((x.name, x.value) for x in AcademicCalendarTypes if x in ADMISSION_POOL_ACADEMIC_CALENDAR_TYPES),
        max_length=70,
        null=True,
        blank=True,
    )

    specific_question_answers = ConfigurableModelFormItemField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
        upload_to=admission_directory_path,
        education_field_name='training',
    )

    curriculum = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Curriculum'),
        max_files=1,
    )
    valuated_secondary_studies_person = models.ForeignKey(
        to='base.Person',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('The person whose the secondary studies have been valuated by this admission'),
    )
    are_secondary_studies_access_title = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are the secondary studies the access title for this admission?'),
    )
    confirmation_elements = models.JSONField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )
    submitted_at = models.DateTimeField(
        verbose_name=_("Submission date"),
        null=True,
    )

    submitted_profile = models.JSONField(
        verbose_name=_("Submitted profile"),
        default=dict,
    )

    reference = models.BigIntegerField(
        verbose_name=_("Reference"),
        unique=True,
        editable=False,
        null=True,
    )
    pdf_recap = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('PDF recap of the proposition'),
    )

    viewers = models.ManyToManyField(
        Person,
        through='AdmissionViewer',
        verbose_name=_('Viewed by'),
        related_name='viewed_admissions',
    )

    last_update_author = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Last update author"),
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
    )

    requested_documents = models.JSONField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
        verbose_name=_('Requested documents'),
    )
    uclouvain_sic_documents = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('UCLouvain SIC free documents'),
    )
    uclouvain_fac_documents = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('UCLouvain FAC free documents'),
    )

    checklist = models.JSONField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    objects = BaseAdmissionManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    # Only the candidate can be valuated
                    valuated_secondary_studies_person_id=models.F("candidate_id"),
                ),
                name='only_candidate_can_be_valuated',
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('admission_permission_{}'.format(self.uuid))

    @property
    def reference_str(self):
        reference = '{:08}'.format(self.reference)
        return f'{reference[:4]}.{reference[4:]}'

    def __str__(self):
        return self.reference_str

    def get_admission_context(self):

        if hasattr(self, 'generaleducationadmission'):
            return CONTEXT_GENERAL
        if hasattr(self, 'doctorateadmission'):
            return CONTEXT_DOCTORATE
        if hasattr(self, 'continuingeducationadmission'):
            return CONTEXT_CONTINUING

    @cached_property
    def admission_context(self):
        return self.get_admission_context()

    @cached_property
    def sent_to_epc(self):
        return any(
            injection.status == EPCInjectionStatus.OK.name
            for injection in self.epc_injection.filter(type=EPCInjectionType.DEMANDE.name)
        )

    @cached_property
    def is_in_quarantine(self):
        return BaseAdmission.objects.filter(pk=self.pk).filter_in_quarantine().exists()

    @cached_property
    def other_candidate_trainings(self) -> Dict[str, Set[str]]:
        # Retrieve the education group types from the admissions
        admission_training_types = (
            BaseAdmission.objects.filter(
                candidate_id=self.candidate_id,
            )
            .exclude(
                Q(pk=self.pk)
                | Q(generaleducationadmission__status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE)
                | Q(continuingeducationadmission__status__in=STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE)
                | Q(doctorateadmission__status__in=STATUTS_PROPOSITION_DOCTORALE_PEU_AVANCEE),
            )
            .values_list(
                'training__education_group_type__name',
                flat=True,
            )
        )

        # Retrieve the education group types from the internal trainings
        internal_training_types = (
            InscriptionProgrammeAnnuel.objects.filter(
                programme_cycle__etudiant__person_id=self.candidate_id,
                programme__isnull=False,
            )
            .exclude(
                etat_inscription__in=[
                    EtatInscriptionFormation.ERREUR.name,
                    EtatInscriptionFormation.ERREUR_PROCEDURE.name,
                ]
            )
            .values_list(
                'programme__root_group__education_group_type__name',
                flat=True,
            )
        )

        other_admissions = {
            CONTEXT_GENERAL: set(),
            CONTEXT_DOCTORATE: set(),
            CONTEXT_CONTINUING: set(),
        }

        for training in itertools.chain(internal_training_types, admission_training_types):
            other_admissions[ADMISSION_CONTEXT_BY_ALL_OSIS_EDUCATION_TYPE[training]].add(training)

        return other_admissions


class AdmissionEducationalValuatedExperiences(models.Model):
    baseadmission = models.ForeignKey(
        BaseAdmission,
        on_delete=models.CASCADE,
        to_field='uuid',
    )

    educationalexperience = models.ForeignKey(
        'osis_profile.EducationalExperience',
        on_delete=models.CASCADE,
        to_field='uuid',
        related_name='educational_valuated_experiences',
    )

    is_access_title = models.BooleanField(
        default=False,
        verbose_name=_('Is access title of the proposition?'),
    )


class AdmissionProfessionalValuatedExperiences(models.Model):
    baseadmission = models.ForeignKey(
        BaseAdmission,
        on_delete=models.CASCADE,
        to_field='uuid',
    )

    professionalexperience = models.ForeignKey(
        'osis_profile.ProfessionalExperience',
        on_delete=models.CASCADE,
        to_field='uuid',
        related_name='professional_valuated_experiences',
    )

    is_access_title = models.BooleanField(
        default=False,
        verbose_name=_('Is access title of the proposition?'),
    )


@receiver(post_save, sender=EducationGroupYear)
def _invalidate_doctorate_cache(sender, instance, **kwargs):
    admission_types = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.keys()
    if (
        instance.education_group_type.category == Categories.TRAINING.name
        and instance.education_group_type.name in admission_types
    ):  # pragma: no branch
        keys = [
            f'admission_permission_{a_uuid}'
            for a_uuid in BaseAdmission.objects.filter(training_id=instance.pk).values_list('uuid', flat=True)
        ]
        if keys:
            cache.delete_many(keys)


@receiver(post_save, sender=Person)
def _invalidate_candidate_cache(sender, instance, **kwargs):
    keys = [
        f'admission_permission_{a_uuid}'
        for a_uuid in BaseAdmission.objects.filter(candidate_id=instance.pk).values_list('uuid', flat=True)
    ]
    if keys:
        cache.delete_many(keys)


class AdmissionViewer(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        verbose_name=_('Person'),
    )
    admission = models.ForeignKey(
        BaseAdmission,
        on_delete=models.CASCADE,
        verbose_name=_('Admission'),
    )
    viewed_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Viewed at'),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['person', 'admission'],
                name='admission_viewer_unique',
            ),
        ]

    @classmethod
    def add_viewer(cls, person, admission):
        try:
            AdmissionViewer.objects.update_or_create(
                person=person,
                admission=admission,
            )
        except (IntegrityError, ValidationError):
            pass
