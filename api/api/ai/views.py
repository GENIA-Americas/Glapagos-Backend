# Rest framework
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import status

# Models
from api.ai.serializers import ChatSerializer
from api.ai.models import Chat 
from api.datasets.models import Table

# Permissions
from api.ai.services import ChatAssistant 
from api.users.permissions import IsAdminPermission, CanCrudPermission


class AiViewset(viewsets.ModelViewSet):
    serializer_class = ChatSerializer 
    model = Chat 
    queryset = Chat.objects.all()
    permission_classes = [IsAdminPermission | CanCrudPermission]

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def chat(self, request, *args, **kwargs):
        serializer = ChatSerializer(
            data=request.data, context=dict(request=request)
        )
        serializer.is_valid()
        msg = serializer.validated_data.get("msg", ""),

        tables = Table.objects.filter(file__owner=request.user)
        context = "" 
        for i in tables:
            context += f"table_id = {i.path} \n"

        res = ChatAssistant.chat(msg[0], context)
        return Response({"message": res}, status=status.HTTP_200_OK)

