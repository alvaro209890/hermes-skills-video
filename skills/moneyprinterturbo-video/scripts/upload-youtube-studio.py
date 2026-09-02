#!/usr/bin/env python3
"""Seleciona um MP4 no diálogo de upload do YouTube Studio via CDP.

Pré-condições:
- Chrome espelho `alvaro` ativo em localhost:9222;
- YouTube Studio aberto no canal correto;
- diálogo "Enviar vídeos" já aberto, com input[type=file].

Este script SOMENTE seleciona o arquivo. Título, descrição, público infantil,
visibilidade e publicação devem ser definidos e verificados depois no Studio.
"""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

import websockets


def targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10) as response:
        return json.load(response)


async def main():
    if len(sys.argv) != 2:
        raise SystemExit("uso: upload-youtube-studio.py /caminho/video.mp4")
    video = Path(sys.argv[1]).expanduser().resolve()
    if not video.is_file() or video.suffix.lower() != ".mp4":
        raise SystemExit(f"MP4 não encontrado: {video}")

    target = next((item for item in targets() if "studio.youtube.com" in item.get("url", "")), None)
    if not target:
        raise SystemExit("Nenhuma aba do YouTube Studio encontrada")

    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=None) as websocket:
        sequence = 0

        async def call(method, params=None):
            nonlocal sequence
            sequence += 1
            request_id = sequence
            await websocket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(await websocket.recv())
                if message.get("id") == request_id:
                    if "error" in message:
                        raise RuntimeError(f"{method}: {message['error']}")
                    return message.get("result", {})

        await call("DOM.enable")
        document = await call("DOM.getDocument", {"depth": -1, "pierce": True})
        query = await call(
            "DOM.querySelector",
            {"nodeId": document["root"]["nodeId"], "selector": "input[type=file]"},
        )
        if not query.get("nodeId"):
            raise SystemExit("Input de arquivo não encontrado; abra Criar → Enviar vídeos")
        await call("DOM.setFileInputFiles", {"nodeId": query["nodeId"], "files": [str(video)]})
        print(json.dumps({"ok": True, "target": target["id"], "video": str(video)}, ensure_ascii=False))


asyncio.run(main())
