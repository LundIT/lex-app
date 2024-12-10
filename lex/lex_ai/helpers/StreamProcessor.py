import asyncio
from typing import Optional

class StreamProcessor:
    global_message_queue = asyncio.Queue()
    dict_message_queues = asyncio.Queue()
    def __init__(
            self,
            delimiter: Optional[str] = None,
            end_delimiter: Optional[str] = None,
            max_buffer: int = 1024,
            # queue: Optional[asyncio.Queue] = global_message_queue
    ):
        self.delimiter = delimiter
        self.end_delimiter = end_delimiter
        self.max_buffer = max_buffer
        self.queue = StreamProcessor.global_message_queue


    async def process_stream(self, trigger_enabled: bool = False) -> str:

        if not trigger_enabled:
            # Simple pass-through mode
            while True:
                message = await self.queue.get()
                if message == 'DONE':
                    break
                yield message
        else:
            # Delimiter processing mode
            buffer = ""
            in_block = False

            while True:
                message = await self.queue.get()
                if message == 'DONE':
                    break
                if message.startswith("code_file_path") or message.startswith("approval_required"):
                    yield message
                    continue

                buffer += message

                if self.delimiter and self.end_delimiter:
                    # Check for opening delimiter
                    if self.delimiter in buffer and not in_block:
                        buffer = buffer[buffer.find(self.delimiter) + len(self.delimiter):]
                        in_block = True
                        continue

                    # Check for closing delimiter
                    if self.end_delimiter in buffer and in_block:
                        content = buffer[:buffer.find(self.end_delimiter)]
                        if content:
                            yield content
                        buffer = buffer[buffer.find(self.end_delimiter) + len(self.end_delimiter):]
                        in_block = False
                        buffer = ""
                        continue

                    # Yield if buffer gets too large while in a block
                    if in_block and len(buffer) > self.max_buffer:
                        yield buffer
                        buffer = ""
                else:
                    # No delimiters specified, just yield the message
                    yield message