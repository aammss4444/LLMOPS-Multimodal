"""
Video processing service:
- Download video (YouTube)
- Extract audio with ffmpeg (for speech pipeline)
- Transcribe speech with Whisper
- Extract frames with ffmpeg (for OCR)
- Run OCR over extracted frames
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import yt_dlp
from paddleocr import PaddleOCR
import whisper

logger = logging.getLogger("video-processor")


class VideoProcessingService:
    def __init__(self):
        self.local_storage_dir = os.getenv("LOCAL_VIDEO_STORAGE_DIR", "backend/data/videos")
        self.audio_dir = os.getenv("LOCAL_AUDIO_STORAGE_DIR", "backend/data/audio")
        self.frames_dir = os.getenv("LOCAL_FRAMES_STORAGE_DIR", "backend/data/frames")
        self.frame_interval_seconds = int(os.getenv("FRAME_INTERVAL_SECONDS", "2"))
        self.whisper_model_name = os.getenv("WHISPER_MODEL", "base")
        self.whisper_language = os.getenv("WHISPER_LANGUAGE", "en")
        self._whisper_model = None

    def download_youtube_video(self, url: str, output_path: str = "temp_video.mp4") -> str:
        """Downloads a YouTube video to a local file."""
        logger.info(f"Downloading YouTube video: {url}")
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        ydl_opts = {
            "format": "best",
            "outtmpl": output_path,
            "quiet": False,
            "no_warnings": False,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info("Download complete.")
            return output_path
        except Exception as e:
            raise Exception(f"YouTube Download Failed: {str(e)}")

    def _run_ffmpeg(self, args: list[str]) -> None:
        command = ["ffmpeg", "-y", *args]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except FileNotFoundError:
            raise Exception("ffmpeg is not installed or not available in PATH.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"ffmpeg failed: {e.stderr}")

    def extract_audio(self, video_path: str, output_path: str) -> str:
        """Extract mono 16k WAV audio for speech processing."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        self._run_ffmpeg([
            "-i", video_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            output_path,
        ])
        return output_path

    def extract_frames(self, video_path: str, output_dir: str, interval_seconds: int | None = None) -> list[str]:
        """Extract frames at a fixed interval for OCR."""
        interval = interval_seconds or self.frame_interval_seconds
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        pattern = str(Path(output_dir) / "frame_%06d.jpg")

        # fps=1/N extracts one frame every N seconds.
        self._run_ffmpeg([
            "-i", video_path,
            "-vf", f"fps=1/{max(1, interval)}",
            pattern,
        ])

        frames = sorted(str(p) for p in Path(output_dir).glob("frame_*.jpg"))
        return frames

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe extracted audio using Whisper."""
        try:
            if self._whisper_model is None:
                self._whisper_model = whisper.load_model(self.whisper_model_name)
            result = self._whisper_model.transcribe(audio_path, language=self.whisper_language)
            transcript = (result or {}).get("text", "")
            return transcript.strip()
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    def extract_ocr_text(self, frame_paths: list[str]) -> list[str]:
        """Run OCR on all frames and return de-duplicated text lines."""
        if not frame_paths:
            return []

        ocr = PaddleOCR(use_textline_orientation=True, lang="en")
        lines: list[str] = []
        seen = set()

        for frame in frame_paths:
            try:
                result = ocr.predict(frame)
            except Exception:
                continue

            for page in result or []:
                rec_texts = page.get("rec_texts", []) if isinstance(page, dict) else []
                for text in rec_texts:
                    cleaned = (text or "").strip()
                    if cleaned and cleaned.lower() not in seen:
                        seen.add(cleaned.lower())
                        lines.append(cleaned)

        return lines

    def process_video(self, video_path: str, video_id: str) -> dict[str, Any]:
        safe_id = "".join(c if c.isalnum() or c in "._-" else "_" for c in video_id)

        audio_path = str(Path(self.audio_dir) / f"{safe_id}.wav")
        frames_output_dir = str(Path(self.frames_dir) / safe_id)

        extracted_audio = self.extract_audio(video_path, audio_path)
        transcript = self.transcribe_audio(extracted_audio)
        frame_paths = self.extract_frames(video_path, frames_output_dir)
        ocr_text = self.extract_ocr_text(frame_paths)

        return {
            "local_file_path": video_path,
            "audio_file_path": extracted_audio,
            "frame_paths": frame_paths,
            "transcript": transcript,
            "ocr_text": ocr_text,
            "video_metadata": {
                "platform": "youtube",
                "extraction": "ffmpeg+whisper",
                "frame_count": len(frame_paths),
            },
        }
