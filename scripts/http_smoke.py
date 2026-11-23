"""Exercise the actual ASGI server over a loopback TCP connection."""
import json
import os
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import httpx
import uvicorn

from workforce_knowledge.api import app as APP


def prepare(folder: Path) -> dict:
    return {"ANSWER_MODE": "extractive"}


def verify(client: httpx.Client) -> None:
    ok = client.post("/v1/answer", json={"question": "What happens to offline clock entries?"})
    refused = client.post("/v1/answer", json={"question": "Insure a bicycle"})
    invalid = client.post("/v1/answer", json={"question": "a"})
    assert ok.status_code == 200 and ok.json()["citation"] == "clock.offline"
    assert refused.json()["status"] == "abstained" and invalid.status_code == 422
    print(json.dumps(dict(answer=ok.json(), out_of_scope=refused.json()
          ["status"], invalid=invalid.status_code)))


def main() -> None:
    with TemporaryDirectory() as folder, socket.socket() as listener:
        settings = prepare(Path(folder))
        listener.bind(("127.0.0.1", 0))
        listener.listen(16)
        port = listener.getsockname()[1]
        with patch.dict(os.environ, settings):
            server = uvicorn.Server(uvicorn.Config(APP, log_level="error"))
            thread = threading.Thread(target=server.run, kwargs={
                                      "sockets": [listener]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic()+10
                while not server.started and thread.is_alive() and time.monotonic() < deadline:
                    time.sleep(0.02)
                if not server.started:
                    raise RuntimeError("Server failed to start")
                with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=5) as client:
                    verify(client)
            finally:
                server.should_exit = True
                thread.join(timeout=10)
                if thread.is_alive():
                    raise RuntimeError("Server failed to stop")


if __name__ == "__main__":
    main()
