
"""
STT (speech to text) provider
    -connect()
    -send_audio()
    -receive_transcript()
    -close()
"""

from abc import ABC, abstractmethod


# ABC = Abstract Base Class.
# It defines the common contract every STT provider must follow.
#

# We're defining what an STT implementation must be able to do.
class STTProvider(ABC):

    @abstractmethod
    async def connect(self):
        """
        Establish the realtime connection to the STT provider.
        """
        pass

    @abstractmethod
    async def send_audio(self, audio: bytes):
        """
        Send one chunk of PCM16 audio to the STT provider.
        """
        pass

    @abstractmethod
    async def receive_transcript(self) -> str | None:
        """
        Wait for transcript information from the provider.

        str | None means:
        return a transcript string OR no transcript yet.
        """
        pass

    @abstractmethod
    async def close(self):
        """
        Cleanly close the provider connection.
        """
        pass