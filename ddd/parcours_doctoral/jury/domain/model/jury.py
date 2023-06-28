# ##############################################################################
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
# ##############################################################################
import datetime
from typing import List, Optional
import uuid

import attr

from admission.ddd.parcours_doctoral.jury.domain.model.enums import (
    RoleJury,
    TitreMembre,
    GenreMembre,
)
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    PromoteurPresidentException,
    PromoteurRetireException,
    PromoteurModifieException,
)
from admission.ddd.parcours_doctoral.jury.validator.validator_by_business_action import (
    JuryValidatorList,
    ModifierMembreValidatorList,
    RetirerMembreValidatorList,
    ModifierRoleMembreValidatorList,
    RecupererMembreValidatorList,
    AjouterMembreValidatorList,
)
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, eq=True, hash=True)
class MembreJury(interface.ValueObject):
    est_promoteur: bool
    matricule: Optional[str]
    institution: str
    autre_institution: Optional[str]
    pays: str
    nom: str
    prenom: str
    titre: Optional['TitreMembre']
    justification_non_docteur: Optional[str]
    genre: Optional['GenreMembre']
    email: str

    uuid: str = attr.Factory(uuid.uuid4)
    role: 'RoleJury' = RoleJury.MEMBRE.name


@attr.dataclass(frozen=True, slots=True)
class JuryIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Jury(interface.RootEntity):
    entity_id: 'JuryIdentity'
    titre_propose: str
    cotutelle: bool
    institution_cotutelle: str
    formule_defense: str
    date_indicative: datetime.date
    langue_redaction: str
    langue_soutenance: str
    commentaire: str
    situation_comptable: Optional[bool] = None
    approbation_pdf: List[str] = attr.Factory(list)

    # Optionals because we don't need them to update the rest of the information
    membres: Optional[List[MembreJury]] = None

    def validate(self):
        JuryValidatorList(self).validate()

    def ajouter_membre(self, membre: MembreJury):
        AjouterMembreValidatorList(jury=self, membre=membre).validate()
        self.membres.append(membre)

    def recuperer_membre(self, uuid_membre: str) -> MembreJury:
        RecupererMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        for membre in self.membres:
            if membre.uuid == uuid_membre:
                return membre

    def modifier_membre(self, membre: MembreJury):
        ModifierMembreValidatorList(jury=self, membre=membre).validate()
        ancien_membre = self.recuperer_membre(membre.uuid)
        if ancien_membre.est_promoteur:
            raise PromoteurModifieException(uuid_membre=membre.uuid, jury=self)
        self.membres.remove(ancien_membre)
        membre = attr.evolve(membre, role=ancien_membre.role, est_promoteur=ancien_membre.est_promoteur)
        self.membres.append(membre)

    def retirer_membre(self, uuid_membre: str):
        RetirerMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        membre = self.recuperer_membre(uuid_membre)
        if membre.est_promoteur:
            raise PromoteurRetireException(uuid_membre=uuid_membre, jury=self)
        self.membres.remove(membre)

    def modifier_role_membre(self, uuid_membre: str, role: str):
        ModifierRoleMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        ancien_membre = self.recuperer_membre(uuid_membre)
        if ancien_membre.est_promoteur and role == RoleJury.PRESIDENT.name:
            raise PromoteurPresidentException()
        # Set the current president / secretary as a member
        if role != RoleJury.MEMBRE.name:
            for membre in self.membres:
                if membre.uuid != uuid_membre and membre.role == role:
                    self.membres.remove(membre)
                    self.membres.append(attr.evolve(membre, role=RoleJury.MEMBRE.name))
        self.membres.remove(ancien_membre)
        self.membres.append(attr.evolve(ancien_membre, role=role, est_promoteur=ancien_membre.est_promoteur))
