# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationPropositionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear


def specifier_informations_acceptation_proposition_par_sic(
    cmd: SpecifierInformationsAcceptationPropositionParSicCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    statut_original = proposition.statut

    proposition_dto = proposition_repository.get_dto(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
    comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=profil_candidat_translator,
        annee_courante=annee_courante,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )
    documents_dto = emplacements_documents_demande_translator.recuperer_emplacements_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        avec_documents_libres=False,
    )

    # THEN
    proposition.specifier_informations_acceptation_par_sic(
        auteur_modification=cmd.gestionnaire,
        documents_dto=documents_dto,
        avec_conditions_complementaires=cmd.avec_conditions_complementaires,
        uuids_conditions_complementaires_existantes=cmd.uuids_conditions_complementaires_existantes,
        conditions_complementaires_libres=cmd.conditions_complementaires_libres,
        avec_complements_formation=cmd.avec_complements_formation,
        uuids_complements_formation=cmd.uuids_complements_formation,
        commentaire_complements_formation=cmd.commentaire_complements_formation,
        nombre_annees_prevoir_programme=cmd.nombre_annees_prevoir_programme,
        nom_personne_contact_programme_annuel=cmd.nom_personne_contact_programme_annuel,
        email_personne_contact_programme_annuel=cmd.email_personne_contact_programme_annuel,
        droits_inscription_montant=cmd.droits_inscription_montant,
        droits_inscription_montant_autre=cmd.droits_inscription_montant_autre,
        dispense_ou_droits_majores=cmd.dispense_ou_droits_majores,
        tarif_particulier=cmd.tarif_particulier,
        refacturation_ou_tiers_payant=cmd.refacturation_ou_tiers_payant,
        annee_de_premiere_inscription_et_statut=cmd.annee_de_premiere_inscription_et_statut,
        est_mobilite=cmd.est_mobilite,
        nombre_de_mois_de_mobilite=cmd.nombre_de_mois_de_mobilite,
        doit_se_presenter_en_sic=cmd.doit_se_presenter_en_sic,
        communication_au_candidat=cmd.communication_au_candidat,
        doit_fournir_visa_etudes=cmd.doit_fournir_visa_etudes,
    )

    proposition_repository.save(entity=proposition)

    historique.historiser_specification_informations_acceptation_sic(
        proposition=proposition,
        gestionnaire=cmd.gestionnaire,
        statut_original=statut_original,
    )

    return proposition.entity_id
