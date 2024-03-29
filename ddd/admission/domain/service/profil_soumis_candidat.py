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
import datetime

from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from osis_common.ddd import interface


class ProfilSoumisCandidatTranslator(interface.DomainService):
    @classmethod
    def recuperer(
        cls,
        profil_candidat_translator: IProfilCandidatTranslator,
        matricule_candidat: str,
    ) -> ProfilCandidat:
        identification = profil_candidat_translator.get_identification(matricule_candidat)
        coordonnees = profil_candidat_translator.get_coordonnees(matricule_candidat)
        adresse = coordonnees.adresse_correspondance or coordonnees.domicile_legal
        return ProfilCandidat(
            nom=identification.nom,
            prenom=identification.prenom,
            genre=identification.genre,
            nationalite=identification.pays_nationalite,
            date_naissance=identification.date_naissance,
            rue=adresse.rue,
            code_postal=adresse.code_postal,
            ville=adresse.ville,
            pays=adresse.pays,
            numero_rue=adresse.numero_rue,
            boite_postale=adresse.boite_postale,
        )
