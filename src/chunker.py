"""Split long essays into chunks for parallel translation, then reassemble."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STARTUPS_DIR = ROOT / "topics" / "startups"
CHUNKS_DIR = ROOT / ".chunks"
MAX_CHUNK_SIZE = 8000  # chars per chunk


def get_untranslated() -> list[str]:
    """Get slugs of essays that don't have _zh.md yet."""
    slugs = []
    for f in sorted(STARTUPS_DIR.glob("*.md")):
        if f.name.endswith("_zh.md") or f.name == "README.md":
            continue
        slug = f.stem
        zh_file = STARTUPS_DIR / f"{slug}_zh.md"
        if not zh_file.exists():
            slugs.append(slug)
    return slugs


def split_essay(slug: str) -> list[Path]:
    """Split an essay into chunks at paragraph boundaries."""
    src = STARTUPS_DIR / f"{slug}.md"
    content = src.read_text(encoding="utf-8")

    # Separate header (# title + > Source + ---) from body
    parts = content.split("---\n\n", 1)
    if len(parts) == 2:
        header = parts[0] + "---\n\n"
        body = parts[1]
    else:
        header = ""
        body = content

    # Split body into paragraphs (double newline separated)
    paragraphs = re.split(r"\n\n", body)

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        if current_size + len(para) > MAX_CHUNK_SIZE and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(para)
        current_size += len(para)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    # Save chunks
    chunk_dir = CHUNKS_DIR / slug
    chunk_dir.mkdir(parents=True, exist_ok=True)

    # Save header separately
    (chunk_dir / "header.txt").write_text(header, encoding="utf-8")

    paths = []
    for i, chunk in enumerate(chunks):
        p = chunk_dir / f"chunk_{i:02d}.txt"
        p.write_text(chunk, encoding="utf-8")
        paths.append(p)

    return paths


def reassemble(slug: str) -> bool:
    """Reassemble translated chunks into a single _zh.md file."""
    chunk_dir = CHUNKS_DIR / slug
    if not chunk_dir.exists():
        return False

    header = (chunk_dir / "header.txt").read_text(encoding="utf-8")

    # Collect translated chunks in order
    translated = []
    for p in sorted(chunk_dir.glob("chunk_*_zh.txt")):
        translated.append(p.read_text(encoding="utf-8"))

    if not translated:
        return False

    # Check all chunks are translated
    total_chunks = len(list(chunk_dir.glob("chunk_*.txt")))
    translated_chunks = len(list(chunk_dir.glob("chunk_*_zh.txt")))
    if translated_chunks < total_chunks:
        print(f"  {slug}: {translated_chunks}/{total_chunks} chunks translated")
        return False

    out = STARTUPS_DIR / f"{slug}_zh.md"
    out.write_text(header + "\n\n".join(translated), encoding="utf-8")
    print(f"  {slug}: assembled {translated_chunks} chunks -> {out.name}")
    return True


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "split"

    if cmd == "split":
        slugs = get_untranslated()
        print(f"Splitting {len(slugs)} untranslated essays...")
        for slug in slugs:
            paths = split_essay(slug)
            src_size = (STARTUPS_DIR / f"{slug}.md").stat().st_size
            print(f"  {slug}: {src_size} bytes -> {len(paths)} chunks")

    elif cmd == "assemble":
        print("Reassembling translated chunks...")
        ok = 0
        for d in sorted(CHUNKS_DIR.iterdir()):
            if d.is_dir() and reassemble(d.name):
                ok += 1
        print(f"Assembled {ok} essays")

    elif cmd == "status":
        for d in sorted(CHUNKS_DIR.iterdir()):
            if not d.is_dir():
                continue
            total = len(list(d.glob("chunk_*.txt")))
            done = len(list(d.glob("chunk_*_zh.txt")))
            status = "done" if done == total else f"{done}/{total}"
            print(f"  {d.name}: {status}")


if __name__ == "__main__":
    main()
