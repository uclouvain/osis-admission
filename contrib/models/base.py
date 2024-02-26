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
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import StringAgg
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, IntegrityError
from django.db.models import OuterRef, Subquery, Q, F, Value, CharField, When, Case, BooleanField, Count
from django.db.models.fields.json import KeyTextTransform, KeyTransform
from django.db.models.functions import Concat, Coalesce, NullIf, Mod, Replace
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, get_language, pgettext_lazy
from osis_comment.models import CommentDeleteMixin
from osis_document.contrib import FileField

from admission.contrib.models.form_item import ConfigurableModelFormItemField
from admission.contrib.models.functions import ToChar
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import (
    STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion, PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from base.utils.cte import CTESubquery
from education_group.contrib.models import EducationGroupRoleModel
from osis_role.contrib.models import EntityRoleModel
from osis_role.contrib.permissions import _get_relevant_roles
from program_management.models.education_group_version import EducationGroupVersion
from reference.models.country import Country

REFERENCE_SEQ_NAME = 'admission_baseadmission_reference_seq'

CAMPUS_LETTRE_DOSSIER = {
    'Bruxelles Saint-Louis': 'B',
    'Charleroi': 'C',
    'Louvain-la-Neuve': 'L',
    'Mons': 'M',
    'Namur': 'N',
    'Tournai': 'T',
    'Bruxelles Woluwe': 'W',
    'Bruxelles Saint-Gilles': 'G',
    'Autre site': 'X',
}


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


class BaseAdmissionQuerySet(models.QuerySet):
    def annotate_campus(self, training_field='training_id', annotation_name='teaching_campus'):
        """
        Annotate the queryset with the teaching campus.
        @param training_field: the name of the training field in the model
        @param annotation_name: the name of the output annotation
        """
        return self.annotate(**{annotation_name: training_campus_subquery(training_field)})

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
                Mod('training__academic_year__year', 100),
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

    def annotate_several_admissions_in_progress(self):
        return self.alias(
            admissions_in_progress_nb=Subquery(
                BaseAdmission.objects.filter(
                    candidate_id=OuterRef("candidate_id"),
                    determined_academic_year_id=OuterRef("determined_academic_year_id"),
                )
                .exclude(
                    Q(generaleducationadmission__status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE)
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

    def filter_according_to_roles(self, demandeur_uuid):
        demandeur_user = User.objects.filter(person__uuid=demandeur_uuid).first()
        roles = _get_relevant_roles(demandeur_user, 'admission.view_enrolment_application')

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

        return self.filter(entities_conditions, education_group_conditions)

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
        choices=AcademicCalendarTypes.choices(),
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
    valuated_secondary_studies_person = models.OneToOneField(
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

    def __str__(self):
        reference = '{:08}'.format(self.reference)
        return f'{reference[:4]}.{reference[4:]}'


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


class BaseAdmissionProxy(BaseAdmission):
    """Proxy model of base.BaseAdmission"""

    objects = BaseAdmissionManager()

    class Meta:
        proxy = True


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
