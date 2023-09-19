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

import json

import requests
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

__all__ = [
    "RequestDigitAccountCreationView",
    "SearchDigitAccountView"
]

from django.views.generic import FormView

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import RechercherCompteExistantQuery
from base.views.common import display_error_messages

from django.utils.translation import gettext_lazy as _


class RequestDigitAccountCreationView(FormView):

    urlpatterns = {'request-account': 'request-account/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        admission = BaseAdmission.objects.get(uuid=kwargs['uuid'])

        if self._is_valid_for_account_creation(request, admission):
            return redirect(to=reverse('admission:doctorate:coordonnees', kwargs={'uuid': kwargs['uuid']}))

        response = request_digit_account_creation({
            "last_name": admission.candidate.last_name,
            "first_name": admission.candidate.first_name,
            "birth_date": str(admission.candidate.birth_date),
            "gender": admission.candidate.gender,
            "national_register": admission.candidate.national_number,
            "nationality": admission.candidate.country_of_citizenship.iso_code,
            "registration_id": "",  # noma à déterminer
            "residence_address": admission.candidate.personaddress_set.first(),  # adresse de résidence à déterminer
        })
        return response

    @staticmethod
    def _is_valid_for_account_creation(request, admission):
        candidate_required_fields = [
            "last_name", "first_name", "birth_date", "gender", "national_number", "country_of_citizenship",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(admission.candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for UCLouvain account creation. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields


class SearchDigitAccountView(FormView):

    urlpatterns = {'search-account': 'search-account/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        admission = BaseAdmission.objects.get(uuid=kwargs['uuid'])

        if self._is_valid_for_search(request, admission):
            return redirect(to=reverse('admission:doctorate:person', kwargs={'uuid': kwargs['uuid']}))

        matches = search_digit_account(
            global_id=admission.candidate.global_id,
            last_name=admission.candidate.last_name,
            first_name=admission.candidate.first_name,
            birth_date=str(admission.candidate.birth_date)
        )

        request.session['search_context'] = {'matches': matches}
        return redirect(reverse('admission:services:search-account-modal', kwargs={'uuid': admission.uuid}))

    @staticmethod
    def _is_valid_for_search(request, admission):
        candidate_required_fields = [
            "last_name", "first_name", "birth_date",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(admission.candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for searching UCLouvain. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields


def request_digit_account_creation(data):
    response = requests.post(
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            "provider": {
                "source": "ETU",
                "sourceId": data["registration_id"],  # noma
                "actif": True,
            },
            "person": {
                "lastName": data['last_name'],
                "firstName": data['first_name'],
                "birthDate": data['birth_date'],
                "gender": data["gender"],
                "nationalRegister": data["national_register"],
                "nationality": data["nationality"],
            },
            "addresses": [
                {
                    "addressType": "RES",
                    "country": data["residence_address"].country.iso_code,
                    "postalCode": data["residence_address"].postal_code,
                    "locality": data["residence_address"].city,
                    "street": data["residence_address"].street,
                    "number": data["residence_address"].street_number,
                    "box": data["residence_address"].postal_box,
                }
            ],
            "physicalPerson": True,
        }),
        url=settings.DIGIT_ACCOUNT_CREATION_URL,
    )
    return response


def search_digit_account(global_id: str, last_name: str, first_name: str, birth_date: str):
    from infrastructure.messages_bus import message_bus_instance

    return message_bus_instance.invoke(
        RechercherCompteExistantQuery(
            matricule=global_id, nom=last_name, prenom=first_name, date_naissance=birth_date
        )
    )
