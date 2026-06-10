"""Convert a complete HTML string to an A4 PDF using Playwright."""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def _html_to_pdf(html: str, output_path: Path) -> Path:
    """Render *html* in headless Chromium and save an A4 PDF to *output_path*.

    Returns the resolved absolute path of the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()

        await page.set_content(html, wait_until="networkidle")

        # Emulate print media so page-break rules, margins, and A4 print layout are applied correctly.
        await page.emulate_media(media="print")

        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )

        await browser.close()

    return output_path.resolve()


def html_to_pdf(html: str, output_path: Path) -> Path:
    """Sync wrapper around :func:`_html_to_pdf`.

    Safe to call from both sync and async contexts — it creates a new
    event-loop if one is not already running.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an existing async context (e.g. FastMCP).
        # Schedule the coroutine and wait via run_until_complete on a new loop
        # running in a thread so we don't block.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(asyncio.run, _html_to_pdf(html, output_path)).result()
        return result
    else:
        return asyncio.run(_html_to_pdf(html, output_path))
