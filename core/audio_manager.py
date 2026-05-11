import asyncio
import numpy as np
import sounddevice as sd
from google.genai import types
from core.logging import LOG


class AudioManager:
    def __init__(self, send_sample_rate=16000, receive_sample_rate=24000,
                 channels=1, chunk_size=1024):
        self.send_sample_rate = send_sample_rate
        self.receive_sample_rate = receive_sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_in_queue = None
        self.out_queue = None
        self.audio_playback_buffer = bytearray()
        self.audio_playback_lock = asyncio.Lock()
        self._logger = LOG.get_logger("AudioManager")
        self._mic_stream = None
        self._playback_stream = None
        self._amplitude_callback = None
        self._ue_broadcast_callback = None
        self.set_speaking_callback = None
        self._turn_done_event = None
        
        self.noise_floor = None
        self.noise_gate_counter = 0

    def set_amplitude_callback(self, callback):
        self._amplitude_callback = callback

    def set_ue_broadcast_callback(self, callback):
        self._ue_broadcast_callback = callback

    def _safe_queue_put(self, q: asyncio.Queue, data):
        if q is None:
            return
        try:
            if q.full():
                q.get_nowait()
            q.put_nowait(data)
        except Exception:
            pass

    async def audio_stream(self, session, out_queue):
        while True:
            msg = await out_queue.get()
            await session.send_realtime_input(
                audio=types.Blob(data=msg, mime_type='audio/pcm;rate=16000')
            )

    async def listen_audio(self, loop, out_queue):
        self._logger.info("Mic started")
        self.out_queue = out_queue

        def _mic_callback(indata, frames, time_info, status):
            if status:
                self._logger.warning(f"Mic status: {status}")

            volume_norm = np.linalg.norm(indata) * 10

            if self.noise_floor is None:
                self.noise_floor = volume_norm

            if volume_norm < self.noise_floor * 1.2 or volume_norm < 0.03:
                self.noise_floor = 0.98 * self.noise_floor + 0.02 * volume_norm

            dynamic_threshold = max(0.04, self.noise_floor * 1.5)

            self.noise_gate_counter += 1
            if self.noise_gate_counter % 150 == 0:
                self._logger.debug(
                    f"Ambient noise floor: {self.noise_floor:.4f} | "
                    f"Dynamic gate: {dynamic_threshold:.4f}"
                )

            max_val = np.max(np.abs(indata))
            if indata.dtype == np.int16:
                amp = float(max_val) / 32768.0
            else:
                amp = float(max_val)

            if self._amplitude_callback:
                self._amplitude_callback(amp, is_mic=True)

            if volume_norm > dynamic_threshold:
                data = indata.tobytes()
                loop.call_soon_threadsafe(self._safe_queue_put, out_queue, data)

        try:
            with sd.InputStream(
                samplerate=self.send_sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=_mic_callback,
            ) as self._mic_stream:
                self._logger.info("Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            self._logger.error(f"Mic error: {e}")
            raise

    async def play_audio(self, audio_in_queue, turn_done_event):
        self._logger.info("Async playback started")
        self.audio_in_queue = audio_in_queue
        self._turn_done_event = turn_done_event
        buffer = bytearray()
        buffer_lock = asyncio.Lock()

        def playback_callback(outdata, frames, time_info, status):
            bytes_needed = frames * self.channels * 2
            chunk = b""

            if len(buffer) >= bytes_needed:
                chunk = bytes(buffer[:bytes_needed])
                outdata[:bytes_needed] = chunk
                del buffer[:bytes_needed]
            else:
                present = len(buffer)
                if present > 0:
                    chunk = bytes(buffer[:present])
                    outdata[:present] = chunk
                    buffer.clear()
                outdata[present:bytes_needed] = b'\x00' * (bytes_needed - present)

            if chunk and any(chunk):
                if self._ue_broadcast_callback:
                    import base64
                    try:
                        audio_b64 = base64.b64encode(chunk).decode('utf-8')
                        self._ue_broadcast_callback({"event": "audio", "value": audio_b64})
                    except Exception:
                        pass

                try:
                    audio_data = np.frombuffer(chunk, dtype=np.int16)
                    if len(audio_data) > 0:
                        max_val = np.max(np.abs(audio_data))
                        amp = float(max_val) / 32768.0
                        if self._amplitude_callback:
                            self._amplitude_callback(amp, is_mic=False)
                except Exception:
                    pass

        stream = sd.RawOutputStream(
            samplerate=self.receive_sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.chunk_size,
            callback=playback_callback
        )
        self._playback_stream = stream
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        audio_in_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    buffer_empty = (len(buffer) == 0)
                    if (turn_done_event and turn_done_event.is_set()
                            and audio_in_queue.empty() and buffer_empty):
                        if self.set_speaking_callback:
                            self.set_speaking_callback(False)
                        turn_done_event.clear()
                    continue

                if self.set_speaking_callback:
                    self.set_speaking_callback(True)
                buffer.extend(chunk)

        except Exception as e:
            self._logger.error(f"Playback error: {e}")
            raise
        finally:
            if self.set_speaking_callback:
                self.set_speaking_callback(False)
            self._playback_stream = None
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
            self._logger.info("Playback stopped")

    def cleanup(self):
        if self._mic_stream:
            try:
                self._mic_stream.close()
            except Exception:
                pass
        if self._playback_stream:
            try:
                self._playback_stream.stop()
                self._playback_stream.close()
            except Exception:
                pass
