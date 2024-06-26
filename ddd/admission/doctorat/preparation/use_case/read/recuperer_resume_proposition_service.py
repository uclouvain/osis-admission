##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import RecupererResumePropositionQuery
from admission.ddd.admission.doctorat.preparation.domain.service.groupe_de_supervision_dto import GroupeDeSupervisionDto
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.profil.repository.i_profil import IProfilRepository


def recuperer_resume_proposition(
    cmd: 'RecupererResumePropositionQuery',
    proposition_repository: 'IPropositionRepository',
    i_profil_candidat_translator: 'IProfilRepository',
    i_comptabilite_translator: 'IComptabiliteTranslator',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
    academic_year_repository: 'IAcademicYearRepository',
) -> 'ResumePropositionDTO':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_dto = proposition_repository.get_dto(entity_id=proposition_id)
    comptabilite_dto = i_comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    groupe_supervision_dto = GroupeDeSupervisionDto().get(
        uuid_proposition=cmd.uuid_proposition,
        repository=groupe_supervision_repository,
        promoteur_translator=promoteur_translator,
        membre_ca_translator=membre_ca_translator,
    )
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )

    # WHEN
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=i_profil_candidat_translator,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        groupe_supervision_dto=groupe_supervision_dto,
        annee_courante=annee_courante,
        experiences_cv_recuperees=ExperiencesCVRecuperees.TOUTES
        if proposition_dto.est_non_soumise
        else ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )

    # THEN
    return resume_dto
