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
    url = BASE_URL + slug + ext
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text, url


SKIP_IMAGE_PATTERNS = {
    "spacer", "beacon", "pixel", "track", "blank",
    "virtumundo", "doubleclick", "googlesyndication",
}


def should_skip_image(url: str, filename: str) -> bool:
    """Skip tracking pixels, spacers, and external junk images."""
    lower = url.lower() + filename.lower()
    return any(p in lower for p in SKIP_IMAGE_PATTERNS)


def extract_images(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Extract meaningful image URLs from the page."""
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        abs_url = urljoin(page_url, src)
        filename = Path(src).name
        if should_skip_image(abs_url, filename):
            img.decompose()  # remove junk images from DOM
            continue
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


def fix_br_tags(html: str) -> str:
    """Fix PG's malformed <br><br/> sequences before parsing.

    PG's HTML uses patterns like <br><br/> which causes html.parser to
    nest all subsequent content inside the first <br> tag. We normalize
    them all to <br/> so BeautifulSoup treats them as self-closing.
    """
    html = re.sub(r"<br\s*>", "<br/>", html)
    return html


def find_essay_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Extract the main essay content from PG's table-based layout.

    PG's site uses nested <table> elements for layout. The essay text is
    typically inside the largest <font> tag or the <td> with the most text.
    """
    # Strategy 1: find the <font> tag with the most text (works for most essays)
    fonts = soup.find_all("font")
    if fonts:
        best = max(fonts, key=lambda f: len(f.get_text()))
        if len(best.get_text()) > 100:
            return best

    # Strategy 2: find the <td> with the most text
    tds = soup.find_all("td")
    if tds:
        best = max(tds, key=lambda t: len(t.get_text()))
        if len(best.get_text()) > 100:
            return best

    # Fallback: use body
    return soup.find("body") or soup


def html_to_markdown(html: str, page_url: str, client: httpx.Client) -> str:
    """Convert essay HTML to clean markdown, downloading images."""
    html = fix_br_tags(html)
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style tags first
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Extract the actual essay content (not the layout tables)
    content_el = find_essay_content(soup)

    # Download images and rewrite src to local paths
    images = extract_images(content_el, page_url)
    for img_info in images:
        local_path = download_image(client, img_info["url"], img_info["filename"])
        if local_path:
            for img_tag in content_el.find_all("img", src=True):
                if img_info["filename"] in img_tag["src"]:
                    img_tag["src"] = f"../../{local_path}"

    # Unwrap layout tables inside the content to avoid markdown table noise
    for table in content_el.find_all("table"):
        table.unwrap()
    for tag in content_el.find_all(["tr", "td", "tbody"]):
        tag.unwrap()

    # Convert to markdown
    content = md(
        str(content_el),
        heading_style="ATX",
        strip=["font"],
    )

    # Clean up
    content = re.sub(r"\n{3,}", "\n\n", content)           # excess blank lines
    content = re.sub(r"[ \t]+\n", "\n", content)            # trailing whitespace
    content = re.sub(r"\|\s*\|[\s|]*", "", content)         # leftover table pipes
    content = re.sub(r"---+\s*\n\s*---+", "---", content)  # duplicate hr
    content = content.strip()

    return content


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

            # Skip entries marked as skip
            if essay.get("skip"):
                stats["skipped"] += 1
                progress.update(task, advance=1, description=f"[dim]Skip: {title}[/dim]")
                continue

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


MIN_CONTENT_LENGTH = 200  # essays shorter than this are likely broken


def validate():
    """Validate scraped essays for quality issues."""
    data = load_essays()
    essays = data["essays"]
    issues = []

    for essay in essays:
        if essay.get("skip"):
            continue
        title = essay["title"]
        slug = essay["slug"]
        topic = essay.get("topic")

        if topic:
            path = TOPICS_DIR / topic / f"{slug}.md"
        else:
            path = BACKLOGS_DIR / f"{slug}.md"

        if not path.exists():
            issues.append(f"[red]MISSING[/red]  {title} ({path})")
            continue

        content = path.read_text(encoding="utf-8")
        # Strip the header (title + source + hr) to measure actual content
        parts = content.split("---\n\n", 1)
        body = parts[1] if len(parts) > 1 else content
        body_len = len(body.strip())

        if body_len < MIN_CONTENT_LENGTH:
            issues.append(f"[yellow]SHORT[/yellow]   {title}: {body_len} chars ({path})")

        if "| --- |" in body or body.count("| |") > 3:
            issues.append(f"[yellow]TABLES[/yellow]  {title}: leftover table markup ({path})")

        # Check for broken image refs
        for match in re.finditer(r"!\[.*?\]\((.*?)\)", body):
            img_path = ROOT / match.group(1).lstrip("../../")
            if not img_path.exists() and not match.group(1).startswith("http"):
                issues.append(f"[yellow]IMG[/yellow]     {title}: missing {match.group(1)}")

    if issues:
        console.print(f"\n[bold]Found {len(issues)} issues:[/bold]")
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("[green]All essays passed validation![/green]")

    # Stats
    total = sum(1 for e in essays if not e.get("skip"))
    existing = sum(1 for e in essays if not e.get("skip") and (
        (TOPICS_DIR / e.get("topic", "") / f"{e['slug']}.md").exists() if e.get("topic")
        else (BACKLOGS_DIR / f"{e['slug']}.md").exists()
    ))
    console.print(f"\nScraped: {existing}/{total} essays")

    return len(issues) == 0


def main():
    import sys
    if "--validate" in sys.argv:
        console.print("[bold]Validating scraped essays...[/bold]")
        ok = validate()
        sys.exit(0 if ok else 1)
    else:
        console.print("[bold]Paul Graham Essay Scraper[/bold]")
        console.print(f"Output: {ROOT}")
        console.print()
        scrape_all()


if __name__ == "__main__":
    main()
