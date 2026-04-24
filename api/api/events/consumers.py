import logging
from http.cookies import SimpleCookie

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from api.events.serializers import WSSerializer

logger = logging.getLogger(__name__)

CLOSE_CODE_AUTH_FAILURE = 4000
CLOSE_CODE_SERVER_ERROR = 4500


class Consumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket connection attempt from %s", self.scope.get("client"))
        await self.accept()

    async def notify(self, event):
        """
        Handles channel layer group_send calls with type='notify'.
        Routes the content payload to the connected WebSocket client.
        """
        await self.send_json(event["content"])

    async def receive_json(self, content, **kwargs):
        """
        Handles incoming JSON from the WebSocket client.
        Validates auth via cookie-based JWT, then subscribes the socket to the
        appropriate channel groups.
        """
        cookie = self._extract_cookies()
        combined = {**content, **cookie}

        serializer = WSSerializer(data=combined)

        try:
            await sync_to_async(serializer.is_valid)(raise_exception=True)
        except Exception as exc:
            logger.warning("WebSocket authentication failed: %s", exc)
            await self.close(code=CLOSE_CODE_AUTH_FAILURE)
            return

        try:
            group_names = await sync_to_async(serializer.get_group_names)()
            for group_name in group_names:
                self.groups.append(group_name)
                await self.channel_layer.group_add(group_name, self.channel_name)
            logger.info("WebSocket subscribed to groups: %s", group_names)
        except Exception as exc:
            logger.error("Error subscribing to channel groups: %s", exc, exc_info=True)
            await self.close(code=CLOSE_CODE_SERVER_ERROR)

    def _extract_cookies(self) -> dict:
        """Parses the Cookie header from the ASGI scope into a plain dict."""
        for key, value in self.scope.get("headers", []):
            if key.decode() == "cookie":
                cookie_str = value.decode()
                parsed = SimpleCookie(cookie_str)
                return {k: morsel.value for k, morsel in parsed.items()}
        return {}
