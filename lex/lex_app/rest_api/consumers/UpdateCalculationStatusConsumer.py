import json

from channels.generic.websocket import AsyncWebsocketConsumer


class UpdateCalculationStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer to handle updates on calculation status.

    This consumer manages WebSocket connections and broadcasts messages
    about the completion of calculations to all connected clients.

    Attributes
    ----------
    active_consumers : set
        A set of currently active consumers.
    """
    active_consumers = set()
    async def connect(self):
        """
        Handle a new WebSocket connection.

        Adds the consumer to the group and accepts the connection.
        """
        await self.channel_layer.group_add(f'update_calculation_status', self.channel_name)
        await self.accept()
        self.active_consumers.add(self)

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Removes the consumer from the group and calls the parent class's
        disconnect method.

        Parameters
        ----------
        close_code : int
            The close code for the WebSocket connection.
        """
        await self.channel_layer.group_discard(f'update_calculation_status', self.channel_name)
        await super().disconnect(close_code)

    async def calculation_is_completed(self, event):
        """
        Send a message to the WebSocket client indicating that a calculation is completed.

        Parameters
        ----------
        event : dict
            The event data containing the payload.
        """
        payload = event['payload']
        await self.send(text_data=json.dumps({
            'type': 'calculation_is_completed',
            'payload': payload
        }))
    @classmethod
    async def disconnect_all(cls):
        """
        Disconnect all active consumers.

        Iterates over all active consumers and disconnects them.
        """
        for consumer in cls.active_consumers.copy():
            await consumer.disconnect(None)
