from typing import Optional

import asyncio


class StreamProcessor:
    global_message_queue = asyncio.Queue()
    dict_message_queues = asyncio.Queue()

    START_BLOCK_FLAG = "_start_code_bloc:\n"
    END_BLOCK_FLAG = "_end_code_bloc:\n"

    def __init__(
            self,
            delimiter: Optional[str] = None,
            end_delimiter: Optional[str] = None,
            max_buffer: int = 1024
    ):
        self.delimiter = delimiter
        self.end_delimiter = end_delimiter
        self.max_buffer = max_buffer
        self.queue = StreamProcessor.global_message_queue

    async def process_stream(self) -> str:
        buffer = ""
        in_block = False
        processing_mode = False

        while True:
            message = await self.queue.get()

            if message == 'DONE':
                break

            # Handle special control messages
            if message == self.START_BLOCK_FLAG:
                processing_mode = True
                continue
            elif message == self.END_BLOCK_FLAG:
                processing_mode = False
                if buffer:
                    yield buffer
                buffer = ""
                continue

            # Handle direct pass-through messages
            if message.startswith("code_file_path") or message.startswith("approval_required"):
                yield message
                continue

            # Process messages based on current mode
            if not processing_mode:
                yield message
                continue

            # Delimiter processing mode
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
                # No delimiters specified, yield accumulated buffer
                yield buffer
                buffer = ""
