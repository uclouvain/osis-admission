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
import attr
from django.utils.timezone import now

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.doctorat.validation.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.doctorat.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.admission.doctorat.validation.domain.service.proposition_identity import (
    PropositionIdentityTranslator,
)
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository
from osis_common.ddd import interface


class DemandeService(interface.DomainService):
    @classmethod
    def recuperer(
        cls,
        demande_id: DemandeIdentity,
        demande_repository: IDemandeRepository,
    ) -> DemandeDTO:
        return demande_repository.get_dto(demande_id)

    @classmethod
    def initier(
        cls,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition_id: PropositionIdentity,
        matricule_candidat: str,
        type_admission: ChoixTypeAdmission,
    ) -> Demande:
        identification = profil_candidat_translator.get_identification(matricule_candidat)
        coordonnees = profil_candidat_translator.get_coordonnees(matricule_candidat)
        return Demande(
            entity_id=PropositionIdentityTranslator.convertir_en_demande(proposition_id),
            proposition_id=proposition_id,
            pre_admission_confirmee_le=now() if type_admission == ChoixTypeAdmission.PRE_ADMISSION else None,
            admission_confirmee_le=now() if type_admission == ChoixTypeAdmission.ADMISSION else None,
            profil_candidat=ProfilCandidat(
                nom=identification.nom,
                prenom=identification.prenom,
                genre=identification.genre,
                nationalite=identification.pays_nationalite,
                email=identification.email,
                **attr.asdict(coordonnees.adresse_correspondance or coordonnees.domicile_legal),
            ),
        )
