import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def extraer_cubso_batch(urls_codigos):
    resultados = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            for codigo, url in urls_codigos:
                cubso = "No disponible"
                if url != "No disponible":
                    try:
                        await page.goto(url, timeout=20000)
                        await page.wait_for_timeout(1500)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")

                        # Buscar en celdas con clase que contenga "codCubso"
                        for cell in soup.find_all("td", class_=re.compile(r".*codCubso.*", re.I)):
                            txt = cell.get_text(strip=True)
                            if txt.isdigit() and 13 <= len(txt) <= 16:
                                cubso = txt
                                break
                        else:
                            # Buscar en todo el texto como fallback
                            match = re.search(r"\b\d{13,16}\b", soup.get_text())
                            cubso = match.group() if match else "No encontrado"
                    except Exception:
                        cubso = "Error"
                resultados.append({"Código": codigo, "CUBSO": cubso})
                await asyncio.sleep(0.5)  # reducido para Render
            return resultados
        finally:
            await context.close()
            await browser.close()