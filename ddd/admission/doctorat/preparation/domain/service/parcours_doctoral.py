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
from typing import Optional

from django.apps import apps

from admission.ddd.admission.doctorat.preparation.domain.model.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralValueObject,
)
from ddd.logic.reference.domain.builder.bourse_identity import BourseIdentityBuilder
from infrastructure.utils import MessageBus
from osis_common.ddd import interface


class ParcoursDoctoralTranslator(interface.DomainService):
    @classmethod
    def recuperer(
        cls,
        uuid_proposition: Optional[str],
        message_bus: MessageBus,
    ) -> Optional[ParcoursDoctoralValueObject]:
        if uuid_proposition and apps.is_installed('parcours_doctoral'):
            from parcours_doctoral.ddd.commands import (
                RecupererParcoursDoctoralPropositionQuery,
            )
            from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO

            parcours_doctoral_dto: ParcoursDoctoralDTO = message_bus.invoke(
                RecupererParcoursDoctoralPropositionQuery(
                    proposition_uuid=uuid_proposition,
                )
            )

            return ParcoursDoctoralValueObject(
                uuid=parcours_doctoral_dto.uuid,
                matricule_doctorant=parcours_doctoral_dto.matricule_doctorant,
                justification=parcours_doctoral_dto.justification,
                commission_proximite=parcours_doctoral_dto.commission_proximite,
                financement_type=parcours_doctoral_dto.financement.type,
                financement_type_contrat_travail=parcours_doctoral_dto.financement.type_contrat_travail,
                financement_eft=parcours_doctoral_dto.financement.eft,
                financement_bourse_recherche=(
                    BourseIdentityBuilder.build_from_uuid(parcours_doctoral_dto.financement.bourse_recherche.uuid)
                    if parcours_doctoral_dto.financement.bourse_recherche
                    else None
                ),
                financement_autre_bourse_recherche=parcours_doctoral_dto.financement.autre_bourse_recherche,
                financement_bourse_date_debut=parcours_doctoral_dto.financement.bourse_date_debut,
                financement_bourse_date_fin=parcours_doctoral_dto.financement.bourse_date_fin,
                financement_bourse_preuve=parcours_doctoral_dto.financement.bourse_preuve,
                financement_duree_prevue=parcours_doctoral_dto.financement.duree_prevue,
                financement_temps_consacre=parcours_doctoral_dto.financement.temps_consacre,
                financement_est_lie_fnrs_fria_fresh_csc=parcours_doctoral_dto.financement.est_lie_fnrs_fria_fresh_csc,
                financement_commentaire=parcours_doctoral_dto.financement.commentaire,
                projet_langue_redaction_these=parcours_doctoral_dto.projet.langue_redaction_these,
                projet_institut_these=(
                    str(parcours_doctoral_dto.projet.institut_these)
                    if parcours_doctoral_dto.projet.institut_these
                    else ''
                ),
                projet_lieu_these=parcours_doctoral_dto.projet.lieu_these,
                projet_titre=parcours_doctoral_dto.projet.titre,
                projet_resume=parcours_doctoral_dto.projet.resume,
                projet_doctorat_deja_realise=parcours_doctoral_dto.projet.doctorat_deja_realise,
                projet_institution=parcours_doctoral_dto.projet.institution,
                projet_domaine_these=parcours_doctoral_dto.projet.domaine_these,
                projet_date_soutenance=parcours_doctoral_dto.projet.date_soutenance,
                projet_raison_non_soutenue=parcours_doctoral_dto.projet.raison_non_soutenue,
                projet_projet_doctoral_deja_commence=parcours_doctoral_dto.projet.projet_doctoral_deja_commence,
                projet_projet_doctoral_institution=parcours_doctoral_dto.projet.projet_doctoral_institution,
                projet_projet_doctoral_date_debut=parcours_doctoral_dto.projet.projet_doctoral_date_debut,
                projet_documents_projet=parcours_doctoral_dto.projet.documents_projet,
                projet_graphe_gantt=parcours_doctoral_dto.projet.graphe_gantt,
                projet_proposition_programme_doctoral=parcours_doctoral_dto.projet.proposition_programme_doctoral,
                projet_projet_formation_complementaire=parcours_doctoral_dto.projet.projet_formation_complementaire,
                projet_lettres_recommandation=parcours_doctoral_dto.projet.lettres_recommandation,
            )
