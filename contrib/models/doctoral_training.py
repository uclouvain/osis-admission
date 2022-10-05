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
import contextlib
from uuid import uuid4

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.ddd.parcours_doctoral.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ChoixStatutPublication,
    ContexteFormation,
    StatutActivite,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_document.contrib import FileField

__all__ = [
    "Activity",
]


def training_activity_directory_path(instance: 'Activity', filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/training/{}'.format(
        instance.doctorate.candidate.uuid,
        instance.doctorate.uuid,
        filename,
    )


class ActivityQuerySet(models.QuerySet):
    def for_doctoral_training(self, doctorate_uuid):
        return (
            self.filter(
                doctorate__uuid=doctorate_uuid,
                context=ContexteFormation.DOCTORAL_TRAINING.name,
            )
            .exclude(Q(category=CategorieActivite.UCL_COURSE.name, course_completed=False))
            .prefetch_related('children')
            .select_related('learning_unit_year')
        )

    def for_complementary_training(self, doctorate_uuid):
        return (
            self.filter(
                doctorate__uuid=doctorate_uuid,
                context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
            )
            .exclude(Q(category=CategorieActivite.UCL_COURSE.name, course_completed=False))
            .prefetch_related('children')
            .select_related('learning_unit_year')
        )

    def for_enrollment_courses(self, doctorate_uuid):
        return (
            self.filter(
                doctorate__uuid=doctorate_uuid,
                category=CategorieActivite.UCL_COURSE.name,
            )
            .select_related('learning_unit_year')
            .order_by('context')
        )


class Activity(models.Model):
    uuid = models.UUIDField(
        default=uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    doctorate = models.ForeignKey(
        'admission.DoctorateAdmission',
        on_delete=models.CASCADE,
    )
    context = models.CharField(
        max_length=30,
        choices=ContexteFormation.choices(),
        default=ContexteFormation.DOCTORAL_TRAINING.name,
    )
    ects = models.DecimalField(
        verbose_name=_("ECTS credits"),
        max_digits=4,
        decimal_places=2,
        blank=True,
        default=0,
    )
    status = models.CharField(
        max_length=20,
        choices=StatutActivite.choices(),
        default=StatutActivite.NON_SOUMISE.name,
    )
    category = models.CharField(
        max_length=50,
        choices=CategorieActivite.choices(),
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    # Common
    type = models.CharField(
        max_length=100,
        default="",
        blank=True,
        verbose_name=_("Activity type"),
    )

    # Conference, communication, publication
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        default="",
        blank=True,
    )

    participating_proof = FileField(
        verbose_name=_("Participation certification"),
        max_files=1,
        blank=True,
        upload_to=training_activity_directory_path,
    )
    comment = models.TextField(
        verbose_name=_("Comment"),
        default="",
        blank=True,
    )

    # Conference
    start_date = models.DateField(
        verbose_name=_("Activity begin date"),
        null=True,
        blank=True,
    )
    end_date = models.DateField(
        verbose_name=_("Activity end date"),
        null=True,
        blank=True,
    )
    participating_days = models.DecimalField(
        verbose_name=_("Number of days participating"),
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )
    is_online = models.BooleanField(
        verbose_name=_("Online event"),
        choices=((False, _("In person")), (True, _("Online"))),
        null=True,
        default=None,  # to prevent messing with choices
        blank=True,
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    city = models.CharField(
        max_length=100,
        verbose_name=_("City"),
        default="",
        blank=True,
    )
    organizing_institution = models.CharField(
        max_length=100,
        verbose_name=_("Organizing institution"),
        default="",
        blank=True,
    )
    website = models.URLField(
        default="",
        verbose_name=_("Website"),
        blank=True,
    )

    # communication, publication
    committee = models.CharField(
        max_length=100,
        choices=ChoixComiteSelection.choices(),
        blank=True,
        default="",
    )
    dial_reference = models.CharField(
        max_length=100,
        verbose_name=_("Reference DIAL.Pr"),
        default="",
        blank=True,
    )
    acceptation_proof = FileField(
        verbose_name=_("Participation certification"),
        max_files=1,
        blank=True,
        upload_to=training_activity_directory_path,
    )

    # Communication
    summary = FileField(
        verbose_name=pgettext_lazy("paper summary", "Summary"),
        max_files=1,
        blank=True,
        upload_to=training_activity_directory_path,
    )
    subtype = models.CharField(
        verbose_name=_("Activity subtype"),
        max_length=100,
        default="",
        blank=True,
    )
    subtitle = models.TextField(
        blank=True,
        default="",
    )

    # Publication
    authors = models.CharField(
        verbose_name=_("Authors"),
        max_length=100,
        default="",
        blank=True,
    )
    role = models.CharField(
        verbose_name=_("Role"),
        max_length=100,
        default="",
        blank=True,
    )
    keywords = models.CharField(
        verbose_name=_("Keywords"),
        max_length=100,
        default="",
        blank=True,
    )
    journal = models.CharField(
        verbose_name=_("Journal"),
        max_length=100,
        default="",
        blank=True,
    )

    publication_status = models.CharField(
        max_length=100,
        choices=ChoixStatutPublication.choices(),
        blank=True,
        default="",
    )

    # Seminaires
    hour_volume = models.CharField(
        verbose_name=_("Total hourly volume"),
        max_length=100,
        default="",
        blank=True,
    )

    # UCL Course
    learning_unit_year = models.ForeignKey(
        'base.LearningUnitYear',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    course_completed = models.BooleanField(
        blank=True,
        default=False,
    )

    # Process
    reference_promoter_assent = models.BooleanField(
        verbose_name=_("Reference promoter assent"),
        null=True,
    )
    reference_promoter_comment = models.TextField(
        verbose_name=_("Reference promoter comment"),
        default="",
    )
    cdd_comment = models.TextField(
        verbose_name=_("CDD manager comment"),
        default="",
    )

    # Management
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modified at"),
    )
    can_be_submitted = models.BooleanField(
        default=False,
        verbose_name=_("Can be submitted"),
    )

    objects = models.Manager.from_queryset(ActivityQuerySet)()

    def __str__(self) -> str:
        return f"{self.get_category_display()} ({self.ects} ects, {self.get_status_display()})"

    class Meta:
        verbose_name = _("Training activity")
        verbose_name_plural = _("Training activities")
        ordering = ['-created_at']


@receiver(post_save, sender=Activity)
def _activity_update_can_be_submitted(sender, instance, **kwargs):
    from admission.ddd.parcours_doctoral.formation.builder.activite_identity_builder import ActiviteIdentityBuilder
    from admission.ddd.parcours_doctoral.formation.domain.service.soumettre_activites import SoumettreActivites
    from admission.infrastructure.parcours_doctoral.formation.repository.activite import ActiviteRepository

    activite_identity = ActiviteIdentityBuilder.build_from_uuid(instance.uuid)
    activite = ActiviteRepository.get(activite_identity)
    activite_dto = ActiviteRepository.get_dto(activite_identity)
    can_be_submitted = False

    # When communication seminar activity, update the parent uuid
    is_communication_seminar = (
        activite.categorie == CategorieActivite.COMMUNICATION
        and activite.categorie_parente == CategorieActivite.SEMINAR
    )
    instance_uuid = instance.uuid if not is_communication_seminar else instance.parent.uuid

    with contextlib.suppress(MultipleBusinessExceptions):
        SoumettreActivites().verifier_activite(activite, activite_dto, ActiviteRepository())

        if is_communication_seminar:
            # We must also trigger parent check (to check all children) for communication seminar activities
            instance.parent.save()
            return

        can_be_submitted = True
    Activity.objects.filter(uuid=instance_uuid).update(can_be_submitted=can_be_submitted)
