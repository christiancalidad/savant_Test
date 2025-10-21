from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)


def test_voice_with_fixture_file_mp3():
    """Ensure the voice endpoint accepts the fixture MP3 file, skipping if absent, and returns the expected transcription, 
    response text, audio MIME type, and base64-encoded audio."""
    
    project_root = Path(__file__).resolve().parents[1]
    audio_path = project_root / "test_recordings" / "test1.mp3"

    if not audio_path.exists():
        pytest.skip(f"Missing test audio: {audio_path}")

    with audio_path.open("rb") as fh:
        files = {"file": (audio_path.name, fh, "audio/mpeg")}
        r = client.post("/v1/voice", files=files)

    assert r.status_code == 200, r.text
    data = r.json()
    assert "transcription" in data
    assert "response_text" in data
    assert data["audio_mime_type"].startswith("audio/")
    assert isinstance(data.get("audio_b64", ""), str)
