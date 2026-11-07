import sounddevice as sd
import numpy as np
import threading
import queue

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self._current_volume = 0.0
        self._lock = threading.Lock()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        if self.is_recording:
            chunk = indata[:, 0].copy()
            self.audio_queue.put(chunk)
            rms = np.sqrt(np.mean(chunk**2))
            with self._lock:
                self._current_volume = float(rms)

    def start(self):
        with self._lock:
            self.is_recording = True
            self._current_volume = 0.0
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
            blocksize=1024
        )
        self.stream.start()

    def stop(self) -> np.ndarray:
        with self._lock:
            self.is_recording = False
            self._current_volume = 0.0

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        chunks = []
        while not self.audio_queue.empty():
            try:
                chunks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        if not chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(chunks, axis=0)

    def get_volume(self) -> float:
        with self._lock:
            return self._current_volume
