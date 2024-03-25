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
from email.message import EmailMessage

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.domain.service.i_historique import IHistorique, PropositionAdmission


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_initiation(cls, proposition: PropositionAdmission):
        pass

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_demande_complements_sic(cls, proposition: PropositionAdmission, acteur: str, message: EmailMessage):
        pass

    @classmethod
    def historiser_demande_complements_fac(cls, proposition: PropositionAdmission, acteur: str, message: EmailMessage):
        pass

    @classmethod
    def historiser_completion_documents_par_candidat(cls, proposition: PropositionAdmission):
        pass

    @classmethod
    def historiser_annulation_reclamation_documents(cls, proposition: PropositionAdmission, acteur: str, par_fac: bool):
        pass
