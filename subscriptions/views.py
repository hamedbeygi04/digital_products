from rest_framework.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Subscription, Package
from .serializers import SubscriptionSerializer, PackageSerializer


class PackageView(APIView):
    def get(self, request):
        packages = Package.objects.filter(is_enabled=True)
        serializer = PackageSerializer(packages, many=True)
        return Response(serializer.data)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user,
            expired_time__gt=timezone.now()
        )
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)