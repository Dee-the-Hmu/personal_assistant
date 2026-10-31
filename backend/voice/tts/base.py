from abc import ABC, abstractmethod


# Abstract interface/contract for every TTS provider.
#
# The rest of our voice system should depend on TTSProvider,
# not directly on Deepgram, ElevenLabs, etc.
class TTSProvider(ABC):

    @abstractmethod
    async def connect(self):
        """
        Establish the realtime connection to the TTS provider.
        """
        pass

    @abstractmethod
    async def send_text(self, text: str):
        """
        Send a speakable piece of text to the TTS provider.
        """
        pass

    @abstractmethod
    async def receive_audio(self) -> bytes | None:
        """
        Wait for the next generated audio chunk.

        bytes = generated audio is available
        None  = provider event contains no audio
        """
        pass

    @abstractmethod
    async def flush(self):
        """
        Tell the provider that the current buffered text should
        be synthesized without waiting for more text.
        """
        pass

    @abstractmethod
    async def close(self):
        """
        Cleanly close the TTS connection.
        """
        pass