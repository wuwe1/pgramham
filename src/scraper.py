"""Scrape Paul Graham's essays and organize them by topic as markdown files."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

BASE_URL = "https://paulgraham.com/"
ROOT = Path(__file__).resolve().parent.parent
ESSAYS_JSON = ROOT / "essays.json"
IMAGES_DIR = ROOT / "images"
BACKLOGS_DIR = ROOT / "backlogs"
TOPICS_DIR = ROOT / "topics"

console = Console()


def load_essays() -> dict:
    with open(ESSAYS_JSON) as f:
        return json.load(f)


def get_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PGEssayScraper/1.0)"
        },
        timeout=30,
        follow_redirects=True,
    )


def fetch_essay(client: httpx.Client, slug: str) -> tuple[str, list[dict]]:
    """Fetch an essay and return (html_content, images_info)."""
    ext = ".txt" if slug in ("acl1", "acl2") else ".html"
    url = urljoin(BASE_URL, slug + ext)
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text, url


def extract_images(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Extract image URLs from the page."""
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        abs_url = urljoin(page_url, src)
        filename = Path(src).name
        images.append({"url": abs_url, "filename": filename})
    return images


def download_image(client: httpx.Client, url: str, filename: str) -> str | None:
    """Download an image and save to images/ directory. Returns local path."""
    dest = IMAGES_DIR / filename
    if dest.exists():
        return f"images/{filename}"
    try:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return f"images/{filename}"
    except Exception as e:
        console.print(f"  [yellow]Warning: failed to download {url}: {e}[/yellow]")
        return None


def html_to_markdown(html: str, page_url: str, client: httpx.Client) -> str:
    """Convert essay HTML to clean markdown, downloading images."""
    soup = BeautifulSoup(html, "html.parser")

    # PG's essays are usually in a <table> layout, find the main text
    # Try to find the essay content - usually in the largest <font> or <td> block
    body = soup.find("body")
    if not body:
        body = soup

    # Download images and rewrite src to local paths
    images = extract_images(soup, page_url)
    for img_info in images:
        local_path = download_image(client, img_info["url"], img_info["filename"])
        if local_path:
            for img_tag in body.find_all("img", src=True):
                if img_info["filename"] in img_tag["src"]:
                    img_tag["src"] = f"../../{local_path}"

    # Convert to markdown
    content = md(str(body), heading_style="ATX", strip=["script", "style"])

    # Clean up excessive whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    return content


def txt_to_markdown(text: str) -> str:
    """Convert plain text essay to markdown."""
    return text.strip()


def save_essay(title: str, slug: str, topic: str, content: str) -> Path:
    """Save essay markdown to the appropriate topic directory."""
    topic_dir = TOPICS_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slug}.md"
    filepath = topic_dir / filename

    header = f"# {title}\n\n"
    header += f"> Source: [{BASE_URL}{slug}.html]({BASE_URL}{slug}.html)\n\n---\n\n"

    filepath.write_text(header + content, encoding="utf-8")
    return filepath


def save_to_backlog(title: str, slug: str, content: str) -> Path:
    """Save unclassified essay to backlogs."""
    BACKLOGS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}.md"
    filepath = BACKLOGS_DIR / filename

    header = f"# {title}\n\n"
    header += f"> Source: [{BASE_URL}{slug}.html]({BASE_URL}{slug}.html)\n\n---\n\n"

    filepath.write_text(header + content, encoding="utf-8")
    return filepath


def scrape_all():
    """Scrape all essays and organize by topic."""
    data = load_essays()
    essays = data["essays"]
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    client = get_client()
    stats = {"success": 0, "failed": 0, "skipped": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping essays...", total=len(essays))

        for essay in essays:
            title = essay["title"]
            slug = essay["slug"]
            topic = essay.get("topic")

            # Check if already scraped
            if topic:
                dest = TOPICS_DIR / topic / f"{slug}.md"
            else:
                dest = BACKLOGS_DIR / f"{slug}.md"
            if dest.exists():
                stats["skipped"] += 1
                progress.update(task, advance=1, description=f"[dim]Skip: {title}[/dim]")
                continue

            progress.update(task, advance=0, description=f"Fetching: {title}")

            try:
                html, page_url = fetch_essay(client, slug)

                if slug in ("acl1", "acl2"):
                    content = txt_to_markdown(html)
                else:
                    content = html_to_markdown(html, page_url, client)

                if topic:
                    save_essay(title, slug, topic, content)
                else:
                    save_to_backlog(title, slug, content)

                stats["success"] += 1

                # Be polite - small delay between requests
                time.sleep(0.5)

            except Exception as e:
                console.print(f"[red]Failed: {title} - {e}[/red]")
                stats["failed"] += 1

            progress.update(task, advance=1)

    console.print()
    console.print(f"[green]Done![/green] "
                  f"Success: {stats['success']}, "
                  f"Skipped: {stats['skipped']}, "
                  f"Failed: {stats['failed']}")


def main():
    console.print("[bold]Paul Graham Essay Scraper[/bold]")
    console.print(f"Output: {ROOT}")
    console.print()
    scrape_all()


if __name__ == "__main__":
    main()
