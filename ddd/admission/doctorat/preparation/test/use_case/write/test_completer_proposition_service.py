# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import attr
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    CompleterPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model._experience_precedente_recherche import (
    aucune_experience_precedente_recherche,
)
from admission.ddd.admission.doctorat.preparation.domain.model._financement import (
    financement_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixDoctoratDejaRealise,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


class TestCompleterPropositionService(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
            PersonneConnueUclDTOFactory(matricule="0123456"),
        )

        self.addCleanup(self.proposition_repository.reset)

        self.proposition_existante = PropositionAdmissionSC3DPMinimaleFactory()
        self.proposition_repository.save(self.proposition_existante)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = CompleterPropositionCommand(
            uuid=self.proposition_existante.entity_id.uuid,
            matricule_auteur="0123456",
            type_financement=ChoixTypeFinancement.WORK_CONTRACT.name,
            type_contrat_travail='assistant_uclouvain',
            titre_projet='Mon projet',
            resume_projet='LE résumé de mon projet',
            documents_projet=[],
            doctorat_deja_realise=ChoixDoctoratDejaRealise.YES.name,
            institution="psychiatrique",
            domaine_these="Psy",
        )

        self.doctorat_non_CDE = 'AGRO3DP'

    def test_should_completer(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(self.cmd.titre_projet, proposition.projet.titre)

    def test_should_completer_financement(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(ChoixTypeFinancement[self.cmd.type_financement], proposition.financement.type)
        self.assertEqual(self.cmd.type_contrat_travail, proposition.financement.type_contrat_travail)

    def test_should_completer_projet(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(self.cmd.titre_projet, proposition.projet.titre)
        self.assertEqual(self.cmd.resume_projet, proposition.projet.resume)
        self.assertEqual(self.cmd.documents_projet, proposition.projet.documents)

    def test_should_completer_experience_precedente(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(
            ChoixDoctoratDejaRealise[self.cmd.doctorat_deja_realise],
            proposition.experience_precedente_recherche.doctorat_deja_realise,
        )
        self.assertEqual(self.cmd.institution, proposition.experience_precedente_recherche.institution)

    def test_should_completer_sans_financement(self):
        cmd = attr.evolve(self.cmd, type_financement='', type_contrat_travail='')
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.financement, financement_non_rempli)

    def test_should_completer_sans_projet(self):
        cmd = attr.evolve(self.cmd, titre_projet='', resume_projet='', documents_projet=[])
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.projet.titre, '')
        self.assertEqual(proposition.projet.resume, '')
        self.assertEqual(proposition.projet.documents, [])

    def test_should_completer_sans_experience(self):
        cmd = attr.evolve(
            self.cmd,
            doctorat_deja_realise=ChoixDoctoratDejaRealise.NO.name,
            institution='',
            domaine_these='',
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.experience_precedente_recherche, aucune_experience_precedente_recherche)
