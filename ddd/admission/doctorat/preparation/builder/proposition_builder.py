##############################################################################
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
##############################################################################
from typing import Optional, Union

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import projet_non_rempli
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    InitierPropositionValidatorList,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class PropositionBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Proposition':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'InitierPropositionCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def initier_proposition(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_id: 'DoctoratIdentity',
        proposition_repository: 'IPropositionRepository',
        bourse_translator: 'IBourseTranslator',
    ) -> 'Proposition':
        InitierPropositionValidatorList(
            type_admission=cmd.type_admission,
            justification=cmd.justification,
        ).validate()
        commission_proximite: Optional[
            Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS, ChoixSousDomaineSciences]
        ] = None
        if cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            commission_proximite = ChoixCommissionProximiteCDEouCLSM[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            commission_proximite = ChoixCommissionProximiteCDSS[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixSousDomaineSciences.get_names():
            commission_proximite = ChoixSousDomaineSciences[cmd.commission_proximite]
        reference = "{}-{}".format(
            doctorat_id.annee % 100,
            Proposition.valeur_reference_base + proposition_repository.get_next_reference(),
        )
        bourse_erasmus = bourse_translator.get(cmd.bourse_erasmus_mundus) if cmd.bourse_erasmus_mundus else None
        return Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutProposition.IN_PROGRESS,
            justification=cmd.justification,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            doctorat_id=doctorat_id,
            matricule_candidat=cmd.matricule_candidat,
            commission_proximite=commission_proximite,
            projet=projet_non_rempli,
            bourse_erasmus_mundus_id=bourse_erasmus,
        )
