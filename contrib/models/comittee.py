# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.db import models

from admission.contrib.models.enums.actor_type import ActorType
from osis_signature.models import Actor


class CommitteeActor(Actor):
    type = models.CharField(
        default=ActorType.choices(),
        max_length=50,
    )

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)

        other_main_promoter = CommitteeActor.objects.filter(
            actor_ptr__process_id=self.process_id,
            type=ActorType.MAIN_PROMOTER.name,
        )
        if self.type == ActorType.MAIN_PROMOTER.name and other_main_promoter.exists():
            raise ValidationError(
                message='There is already another main promoter for this committee.',
                code='unique_main_promoter',
            )
