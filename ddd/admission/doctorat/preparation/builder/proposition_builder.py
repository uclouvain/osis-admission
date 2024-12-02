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
from abc import abstractmethod
from typing import Optional, Union

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import projet_non_rempli
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import DoctoratFormation
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    InitierPropositionValidatorList,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class IPropositionBuilder(interface.RootEntityBuilder):
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
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'PropositionIdentity ':
        if cmd.pre_admission_associee:
            return cls.initier_nouvelle_proposition_attachee_a_pre_admission(
                cmd,
                doctorat_translator,
                proposition_repository,
            )
        else:
            return cls.initier_nouvelle_proposition_non_attachee_a_pre_admission(
                cmd,
                doctorat_translator,
                proposition_repository,
            )

    @classmethod
    def initier_nouvelle_proposition_non_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'PropositionIdentity':
        doctorat = doctorat_translator.get(cmd.sigle_formation, cmd.annee_formation)
        InitierPropositionValidatorList(
            type_admission=cmd.type_admission,
            justification=cmd.justification,
            commission_proximite=cmd.commission_proximite,
            doctorat=doctorat,
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
        reference = proposition_repository.recuperer_reference_suivante()
        proposition = Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON,
            justification=cmd.justification,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            formation_id=doctorat.entity_id,
            matricule_candidat=cmd.matricule_candidat,
            commission_proximite=commission_proximite,
            projet=projet_non_rempli,
            auteur_derniere_modification=cmd.matricule_candidat,
        )
        proposition_repository.save(proposition)

        return proposition.entity_id

    @classmethod
    @abstractmethod
    def initier_nouvelle_proposition_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'PropositionIdentity':
        raise NotImplementedError
