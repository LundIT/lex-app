
import json

from channels.generic.websocket import AsyncWebsocketConsumer
# from lex_app.LexLogger.LexLogger import LexLogger


class LogConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling log messages.

    Attributes
    ----------
    socket : AsyncWebsocketConsumer or None
        The current WebSocket connection.
    """
    # logger = LexLogger()
    socket = None

    async def connect(self):
        """
        Handle a new WebSocket connection.

        If there is an existing connection, it will be disconnected.
        Adds the connection to the 'log_group' and accepts the WebSocket connection.
        """
        if self.socket is not None:
            await self.socket.disconnect(None)
        self.socket = self
        await self.channel_layer.group_add("log_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Removes the connection from the 'log_group' and calls the parent class's disconnect method.

        Parameters
        ----------
        close_code : int
            The WebSocket close code.
        """
        await self.channel_layer.group_discard("log_group", self.channel_name)
        await super().disconnect(close_code)


    async def log_message(self, event):
        """
        Send a log message to the WebSocket client.

        Parameters
        ----------
        event : dict
            The event data containing log information.
        """
        await self.send(text_data=json.dumps({
            'id': event.get('id', 'N/A'),
            'logId': event.get('logId', 'N/A'),
            'level': event['level'],
            'message': event['message'],
            'timestamp': event['timestamp'],
            'logName': event.get('logName', 'N/A'),
            'triggerName': event.get('triggerName', 'N/A'),
            'method': event.get('method', 'N/A'),
            'logDetails': event.get('logDetails', 'N/A'),
        }))
    async def receive(self, text_data):
        """
        Handle incoming messages from the WebSocket client.

        Sends a status message back to the client.

        Parameters
        ----------
        text_data : str
            The incoming message data.
        """
        await self.send(text_data=json.dumps({
            'STATUS': "LexLogger v1.0.0 Created By Hazem Sahbani"
        }))


    # async def log_message(self, event):
    #     await self.send(text_data=json.dumps({
    #         'message': message,
    #     }))
