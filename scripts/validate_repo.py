#!/usr/bin/env python3
"""Valida o acervo público de skills sem criar cache ou abrir mídia."""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML ausente: {exc}")

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
BANNED_SUFFIXES = {
    ".mp4", ".mov", ".webm", ".mkv", ".mp3", ".wav", ".m4a", ".aac",
    ".flac", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".7z", ".tar",
    ".gz", ".pyc", ".bak",
}
BANNED_PARTS = {"__pycache__", "cache", "caches", "backup", "backups", ".env"}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|senha)\s*[:=]\s*[^<\s`\"']{8,}"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def frontmatter(text: str, path: Path) -> dict:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: frontmatter não começa no byte 0")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path}: frontmatter sem fechamento")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter não é mapping YAML")
    if not data.get("name") or not data.get("description"):
        raise ValueError(f"{path}: name/description obrigatórios")
    if len(str(data["name"])) > 64 or not re.fullmatch(r"[a-z0-9_-]+", str(data["name"])):
        raise ValueError(f"{path}: name inválido")
    if len(str(data["description"])) > 1024:
        raise ValueError(f"{path}: description > 1024 caracteres")
    if not text[end + 5 :].strip():
        raise ValueError(f"{path}: corpo vazio")
    return data


def main() -> int:
    errors: list[str] = []
    skill_files = sorted(SKILLS.glob("*/SKILL.md"))
    names: dict[str, Path] = {}
    if not skill_files:
        errors.append("nenhuma skill encontrada")

    for path in skill_files:
        try:
            text = path.read_text(encoding="utf-8")
            data = frontmatter(text, path)
            name = str(data["name"])
            if name in names:
                errors.append(f"nome duplicado {name}: {names[name]} e {path}")
            names[name] = path
        except Exception as exc:
            errors.append(str(exc))

    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts):
        rel = path.relative_to(ROOT)
        if path.suffix.lower() in BANNED_SUFFIXES or any(part.lower() in BANNED_PARTS for part in rel.parts):
            errors.append(f"artefato proibido: {rel}")
            continue
        if path.stat().st_size > 1_000_000:
            errors.append(f"arquivo >1 MB: {rel}")
        if path.is_symlink():
            errors.append(f"symlink proibido: {rel}")
        if path.suffix.lower() not in {".md", ".py", ".sh", ".ass", ".txt", ".json", "", ".gitignore"}:
            errors.append(f"extensão não permitida: {rel}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"arquivo não textual: {rel}")
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possível segredo: {rel} ({pattern.pattern[:30]}…)")
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(rel))
            except SyntaxError as exc:
                errors.append(f"Python inválido {rel}: {exc}")
        if path.suffix == ".sh":
            check = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if check.returncode:
                errors.append(f"Shell inválido {rel}: {check.stderr.strip()}")
        if path.suffix == ".md":
            for target in LINK_RE.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                clean = target.split("#", 1)[0]
                if clean and not (path.parent / clean).resolve().exists():
                    errors.append(f"link quebrado {rel}: {target}")

    print(f"skills={len(skill_files)} arquivos={sum(1 for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts)}")
    if errors:
        print(f"ERROS={len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDACAO_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
