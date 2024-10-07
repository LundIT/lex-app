import json

from channels.generic.websocket import AsyncWebsocketConsumer


class CalculationLogConsumer(AsyncWebsocketConsumer):
    """
    Consumer for handling WebSocket connections related to calculation logs.

    Attributes
    ----------
    active_consumers : set
        A set to keep track of active consumers.
    calculation_id : str
        The ID of the calculation.
    calculation_record : str
        The record of the calculation.
    """
    active_consumers = set()

    async def connect(self):
        """
        Handles the WebSocket connection event.

        Extracts the calculation ID from the URL route, adds the consumer to the
        appropriate group, and accepts the WebSocket connection.
        """
        self.calculation_id = self.scope['url_route']['kwargs']['calculationId']
        self.calculation_record = self.calculation_id.split("-")[0]

        await self.channel_layer.group_add(f'{self.calculation_record}', self.channel_name)
        await self.accept()
        self.active_consumers.add(self)

    async def disconnect(self, close_code):
        """
        Handles the WebSocket disconnection event.

        Removes the consumer from the appropriate group and calls the parent
        class's disconnect method.

        Parameters
        ----------
        close_code : int
            The WebSocket close code.
        """
        await self.channel_layer.group_discard(f'{self.calculation_record}', self.channel_name)
        await super().disconnect(close_code)

    async def calculation_log_real_time(self, event):
        """
        Sends real-time calculation logs to the WebSocket client.

        Parameters
        ----------
        event : dict
            The event data containing the payload with logs.
        """
        payload = event['payload']
        await self.send(text_data=json.dumps({
            'type': 'calculation_log_real_time',
            "logs": payload
        }))

    @classmethod
    async def disconnect_all(cls):
        """
        Disconnects all active consumers.

        Iterates over the set of active consumers and disconnects each one.
        """
        for consumer in cls.active_consumers.copy():
            await consumer.disconnect(None)