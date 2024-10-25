import asyncio
# Global asyncio Queue to hold messages from all requests
global_message_queue = asyncio.Queue()

async def global_message_stream():
    while True:
        # Wait for a message from the queue
        message = await global_message_queue.get()

        # When a message is received, yield it to the response
        yield message

        # Optionally check for stop signal
        if message == "DONE":
            break