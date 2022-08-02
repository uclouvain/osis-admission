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
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.db.models.signals import post_save

from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ChoixStatutPublication,
    StatutActivite,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_document.contrib import FileField


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
        verbose_name=_("Référence DIAL.Pr"),
        default="",
        blank=True,
    )
    acceptation_proof = FileField(
        verbose_name=_("Participation certification"),
        max_files=1,
        blank=True,
    )

    # Communication
    summary = FileField(
        verbose_name=pgettext_lazy("paper summary", "Summary"),
        max_files=1,
        blank=True,
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

    def __str__(self) -> str:
        return f"{self.get_category_display()} ({self.ects} ects, {self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']


@receiver(post_save, sender=Activity)
def _activity_update_can_be_submitted(sender, instance, **kwargs):
    from admission.ddd.projet_doctoral.doctorat.formation.builder.activite_identity_builder import (
        ActiviteIdentityBuilder,
    )
    from admission.ddd.projet_doctoral.doctorat.formation.domain.service.soumettre_activite import SoumettreActivites
    from admission.infrastructure.projet_doctoral.doctorat.formation.repository.activite import ActiviteRepository

    activite_identity = ActiviteIdentityBuilder.build_from_uuid(instance.uuid)
    activite = ActiviteRepository.get(activite_identity)
    activite_dto = ActiviteRepository.get_dto(activite_identity)
    can_be_submitted = False
    with contextlib.suppress(MultipleBusinessExceptions):
        SoumettreActivites().verifier_activite(activite, activite_dto)
        if activite.categorie == CategorieActivite.SEMINAR:
            # We must check children too for seminar activities
            for sous_activite in ActiviteRepository.search(parent_id=activite.entity_id):
                sous_activite_dto = ActiviteRepository.get_dto(sous_activite.entity_id)
                SoumettreActivites().verifier_activite(sous_activite, sous_activite_dto)
        can_be_submitted = True
    Activity.objects.filter(uuid=instance.uuid).update(can_be_submitted=can_be_submitted)
