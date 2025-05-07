#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
contains all the views related to Mechanic
"""
import bcrypt
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from crapi_site import settings
from utils.jwt import jwt_auth_required
from utils import messages
from crapi.user.models import User, Vehicle, UserDetails
from utils.logging import log_error
from .models import Mechanic, ServiceRequest, ServiceComment
from .serializers import (
    MechanicSerializer,
    MechanicServiceRequestSerializer,
    ReceiveReportSerializer,
    SignUpSerializer,
    ServiceRequestStatusUpdateSerializer,
    ServiceCommentCreateSerializer,
    ServiceCommentViewSerializer,
)
from rest_framework.pagination import LimitOffsetPagination


class SignUpView(APIView):
    """
    Used to add a new mechanic
    """

    @csrf_exempt
    def post(self, request):
        """
        creates a new Mechanic in the db
        :param request: http request for the view
            method allowed: POST
            mandatory fields: ['name', 'email', 'number', 'password', 'mechanic_code']
        :returns Response object with
            mechanics list and 200 status if no error
            message and corresponding status if error
        """
        serializer = SignUpSerializer(data=request.data)
        if not serializer.is_valid():
            log_error(
                request.path,
                request.data,
                status.HTTP_400_BAD_REQUEST,
                serializer.errors,
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        mechanic_details = serializer.data

        if User.objects.filter(email=mechanic_details["email"]).exists():
            return Response(
                {"message": messages.EMAIL_ALREADY_EXISTS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Mechanic.objects.filter(
            mechanic_code=mechanic_details["mechanic_code"]
        ).exists():
            return Response(
                {"message": messages.MEC_CODE_ALREADY_EXISTS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user_id = User.objects.aggregate(models.Max("id"))["id__max"] + 1
        except TypeError:
            user_id = 1

        user = User.objects.create(
            id=user_id,
            email=mechanic_details["email"],
            number=mechanic_details["number"],
            password=bcrypt.hashpw(
                mechanic_details["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode(),
            role=User.ROLE_CHOICES.MECH,
            created_on=timezone.now(),
        )
        Mechanic.objects.create(
            mechanic_code=mechanic_details["mechanic_code"], user=user
        )
        try:
            user_details_id = (
                UserDetails.objects.aggregate(models.Max("id"))["id__max"] + 1
            )
        except TypeError:
            user_details_id = 1
        UserDetails.objects.create(
            id=user_details_id,
            available_credit=0,
            name=mechanic_details["name"],
            status="ACTIVE",
            user=user,
        )
        return Response(
            {"message": messages.MEC_CREATED.format(user.email)},
            status=status.HTTP_200_OK,
        )
