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
import uuid

from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.parcours_doctoral.jury.domain.model.enums import RoleJury, TitreMembre, GenreMembre

__all__ = ['JuryMember']


class JuryMember(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        # db_comment="MembreJuryDTO.uuid",
    )
    role = models.CharField(
        verbose_name=pgettext_lazy('jury', 'Role'),
        choices=RoleJury.choices(),
        max_length=50,
        # db_comment="MembreJuryDTO.role",
    )
    doctorate = models.ForeignKey(
        'admission.DoctorateAdmission',
        verbose_name=_('PhD'),
        on_delete=models.CASCADE,
        related_name='jury_members',
        # db_comment="MembreJuryDTO.",
    )

    other_institute = models.CharField(
        verbose_name=_('Other institute'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="MembreJuryDTO.autre_institution",
    )

    # Promoter only
    promoter = models.ForeignKey(
        'admission.SupervisionActor',
        verbose_name=_('Supervisor'),
        on_delete=models.PROTECT,
        limit_choices_to={"type": ActorType.PROMOTER.name},
        null=True,
        blank=True,
        # db_comment="Pour promoteur uniquement : renseigne MembreJuryDTO.est_promoteur à True et remplis les informations de nom / ...",
    )

    # UCL member only
    person = models.ForeignKey(
        'base.Person',
        verbose_name=_("Person"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        # db_comment="Pour membre UCL uniquement : renseigne MembreJuryDTO.matricule ainsi que les informations de nom / ...",
    )

    # External member only
    institute = models.CharField(
        verbose_name=pgettext_lazy('jury', 'Institute'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.institution",
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.pays",
    )
    last_name = models.CharField(
        verbose_name=_('Surname'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.nom",
    )
    first_name = models.CharField(
        verbose_name=_('First name'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.prenom",
    )
    title = models.CharField(
        verbose_name=pgettext_lazy('admission', 'Title'),
        choices=TitreMembre.choices(),
        max_length=50,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.titre",
    )
    non_doctor_reason = models.TextField(
        verbose_name=_('Non doctor reason'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.justification_non_docteur",
    )
    gender = models.CharField(
        verbose_name=_('Gender'),
        choices=GenreMembre.choices(),
        max_length=50,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.genre",
    )
    email = models.EmailField(
        verbose_name=pgettext_lazy('admission', 'Email'),
        max_length=255,
        default='',
        blank=True,
        # db_comment="Pour membre externe uniquement : MembreJuryDTO.email",
    )

    class Meta:
        # db_table_comment = "Représente un membre de jury doctoral."
        constraints = [
            CheckConstraint(
                check=(
                    Q(promoter__isnull=False)
                    & Q(person__isnull=True)
                    & Q(institute='')
                    & Q(other_institute='')
                    & Q(country__isnull=True)
                    & Q(last_name='')
                    & Q(first_name='')
                    & Q(title='')
                    & Q(gender='')
                    & Q(email='')
                )
                | (
                    Q(promoter__isnull=True)
                    & Q(person__isnull=False)
                    & Q(institute='')
                    & Q(country__isnull=True)
                    & Q(last_name='')
                    & Q(first_name='')
                    & Q(title='')
                    & Q(gender='')
                    & Q(email='')
                )
                | (
                    Q(promoter__isnull=True)
                    & Q(person__isnull=True)
                    & ~Q(institute='')
                    & Q(country__isnull=False)
                    & ~Q(last_name='')
                    & ~Q(first_name='')
                    & ~Q(title='')
                    & ~Q(gender='')
                    & ~Q(email='')
                ),
                name='admission_jurymember_constraint',
            ),
        ]
