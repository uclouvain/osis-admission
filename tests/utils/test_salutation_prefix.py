# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.test import TestCase

from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.tests.factories.supervision import ExternalPromoterFactory, PromoterFactory
from admission.utils import get_salutation_prefix, get_ca_member_salutation_prefix
from base.tests import QueriesAssertionsMixin
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class SalutationPrefixTestCase(QueriesAssertionsMixin, TestCase):
    def test_get_salutation_prefix(self):
        person = PersonFactory(gender='', language=settings.LANGUAGE_CODE_FR)
        self.assertEqual(get_salutation_prefix(person=person), 'Cher·ère')

        person.gender = ChoixGenre.X.name
        person.save(update_fields=['gender'])
        self.assertEqual(get_salutation_prefix(person=person), 'Cher·ère')

        person.gender = ChoixGenre.F.name
        person.save(update_fields=['gender'])
        self.assertEqual(get_salutation_prefix(person=person), 'Chère')

        person.gender = ChoixGenre.H.name
        person.save(update_fields=['gender'])
        self.assertEqual(get_salutation_prefix(person=person), 'Cher')

        person.language = settings.LANGUAGE_CODE_EN
        person.save(update_fields=['language'])
        self.assertEqual(get_salutation_prefix(person=person), 'Dear')

    def test_get_ca_member_salutation_prefix_with_an_external_member_who_is_doctor(self):
        supervision_actor = ExternalPromoterFactory(language=settings.LANGUAGE_CODE_FR, is_doctor=True)

        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professeur·e')

        supervision_actor.language = settings.LANGUAGE_CODE_EN
        supervision_actor.save(update_fields=['language'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professor')

    def test_get_ca_member_salutation_prefix_with_an_external_member_who_is_not_doctor(self):
        supervision_actor = ExternalPromoterFactory(language=settings.LANGUAGE_CODE_FR, is_doctor=False)

        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Cher·ère')

        supervision_actor.language = settings.LANGUAGE_CODE_EN
        supervision_actor.save(update_fields=['language'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Dear')

    def test_get_ca_member_salutation_prefix_with_an_internal_member_who_is_doctor(self):
        supervision_actor = PromoterFactory(actor_ptr__person__language=settings.LANGUAGE_CODE_FR)
        tutor = TutorFactory(person=supervision_actor.person)

        supervision_actor.person.gender = ChoixGenre.X.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professeur·e')

        supervision_actor.person.gender = ChoixGenre.F.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professeure')

        supervision_actor.person.gender = ChoixGenre.H.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professeur')

        supervision_actor.person.language = settings.LANGUAGE_CODE_EN
        supervision_actor.person.save(update_fields=['language'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Professor')

    def test_get_ca_member_salutation_prefix_with_an_internal_member_who_is_not_doctor(self):
        supervision_actor = PromoterFactory(actor_ptr__person__language=settings.LANGUAGE_CODE_FR)

        supervision_actor.person.gender = ChoixGenre.X.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Cher·ère')

        supervision_actor.person.gender = ChoixGenre.F.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Chère')

        supervision_actor.person.gender = ChoixGenre.H.name
        supervision_actor.person.save(update_fields=['gender'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Cher')

        supervision_actor.person.language = settings.LANGUAGE_CODE_EN
        supervision_actor.person.save(update_fields=['language'])
        self.assertEqual(get_ca_member_salutation_prefix(actor=supervision_actor), 'Dear')
