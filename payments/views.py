import uuid

import requests
from rest_framework.utils import timezone
# from django.shortcuts import redirect, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from subscriptions.models import Package, Subscription
from .models import Gateway, Payment
from .serializers import GatewaySerializer


class GatewayView(APIView):
    def get(self, request):
        gateways = Gateway.objects.filter(is_enabled=True)
        serializer = GatewaySerializer(gateways, many=True)
        return Response(serializer.data)


class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        gateways_id = request.query_params.get('gateways')
        package_id = request.query_params.get('package')

        try:
            package = Package.objects.get(pk=package_id, is_enabled=True)
            gateway = Gateway.objects.get(pk=gateways_id, is_enabled=True)
        except (Package.DoesNotExist, Gateway.DoesNotExist):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            user=request.user,
            package=package,
            gateway=gateway,
            phone_number=request.user.phone_number,
            token=str(uuid.uuid4()),
        )

        # return redirect()
        return Response({'token': payment.token, 'callback_url': 'https://my-site.com/payments/pay/'})

    def post(self, request):
        token = request.data.get('token')
        st = request.data.get('status')

        try:
            payment = Payment.objects.get(token=token)
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if st != 10:
            payment.status = Payment.STATUS_FAILED
            payment.save()
            # render(request, 'payments/result.html', context={'status': payment})
            return Response({'detail': 'Paymet canceled by user.'},
                status=status.HTTP_400_BAD_REQUEST)

        r = requests.post('bank_verify_url', data={})
        if r.status_code // 100 != 2:
            payment.status = Payment.STATUS_ERROR
            payment.save()
            # render(request, 'payments/result.html', context={'status': payment})
            return Response({'detail': 'Payment verification failed.'},
                status=status.HTTP_400_BAD_REQUEST)

        payment.status = Payment.STATUS_PAID
        payment.save()

        Subscription.objects.create(
            user=payment.user,
            package=payment.package,
            expired_time=timezone.now() + timezone.timedelta(days=payment.package.duration.days),
        )

        return Response({'detail': 'Payment is successful.'},)