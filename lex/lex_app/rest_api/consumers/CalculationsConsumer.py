import json

from channels.generic.websocket import AsyncWebsocketConsumer


class CalculationsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling calculation-related messages.

    This consumer manages WebSocket connections, handles incoming messages,
    and sends notifications to connected clients. It also maintains a set of
    active consumers and provides a method to disconnect all consumers.

    Attributes
    ----------
    active_consumers : set
        A set of currently active consumers.
    """
    active_consumers = set()
    async def connect(self):
        """
        Handle a new WebSocket connection.

        This method accepts the WebSocket connection, adds the consumer to
        the 'calculations' group, and registers the consumer as active.
        """
        await self.accept()
        await self.channel_layer.group_add(
            "calculations",
            self.channel_name
        )
        self.active_consumers.add(self)
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        This method removes the consumer from the 'calculations' group and
        unregisters the consumer as active.

        Parameters
        ----------
        close_code : int
            The WebSocket close code.
        """
        await self.channel_layer.group_discard(
            "calculations",
            self.channel_name
        )
        await super().disconnect(close_code)

    async def calculation_id(self, event):
        """
        Handle a calculation ID event.

        This method sends the event data to the WebSocket client.

        Parameters
        ----------
        event : dict
            The event data to be sent to the client.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    async def calculation_notification(self, event):
        """
        Handle a calculation notification event.

        This method sends a notification payload to the WebSocket client.

        Parameters
        ----------
        event : dict
            The event data containing the notification payload.
        """
        payload = event['payload']
        await self.send(text_data=json.dumps({
            'type': 'calculation_notification',
            'payload': payload
        }))

    @classmethod
    async def disconnect_all(cls):
        """
        Disconnect all active consumers.

        This method iterates over all active consumers and disconnects them.
        """
        for consumer in cls.active_consumers.copy():
            await consumer.disconnect(None)