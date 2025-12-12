import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .utils import fecha_en_rango, extraer_tipo, extraer_departamento

SEACE_URL = "https://prod6.seace.gob.pe/buscador-publico/contrataciones"

async def scrape_seace_playwright(fecha_inicio: str, fecha_fin: str, max_cards: int):
    todas_licitaciones = []
    page_count = 1
    max_paginas = 10  # reducido para evitar timeouts en Render

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
            await page.goto(SEACE_URL, timeout=60000)
            await page.wait_for_selector("div.bg-fondo-section.rounded-md.p-5.ng-star-inserted", timeout=20000)

            # Intentar 100 por página
            try:
                select = await page.query_selector("mat-select[aria-labelledby*='mat-paginator-page-size-label']")
                if select:
                    await select.click()
                    opt = await page.query_selector("mat-option:has-text('100')")
                    if opt:
                        await opt.click()
                    await page.wait_for_timeout(3000)
            except Exception:
                pass

            while page_count <= max_paginas and len(todas_licitaciones) < max_cards:
                cards = await page.query_selector_all("div.bg-fondo-section.rounded-md.p-5.ng-star-inserted")
                if not cards:
                    break

                for card in cards:
                    if len(todas_licitaciones) >= max_cards:
                        break
                    try:
                        html = await card.inner_html()
                        soup = BeautifulSoup(html, "html.parser")
                        p_tags = soup.select("p")

                        codigo = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else "No disponible"
                        entidad = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else "No disponible"
                        desc = p_tags[2].get_text(strip=True) if len(p_tags) > 2 else "No disponible"

                        fecha_pub = "No disponible"
                        for p in p_tags:
                            txt = p.get_text(strip=True)
                            if txt.startswith("Fecha de publicación:"):
                                fecha_pub = txt
                                break

                        if fecha_pub == "No disponible" or not fecha_en_rango(fecha_pub, fecha_inicio, fecha_fin):
                            continue

                        enlace = "No disponible"
                        link = soup.select_one("a[href*='/buscador-publico/contrataciones/']")
                        if link and link.get("href"):
                            enlace = urljoin(SEACE_URL, link["href"])

                        lic = {
                            "Código": codigo,
                            "Entidad": entidad,
                            "Servicio": desc,
                            "Tipo": extraer_tipo(desc),
                            "Departamento": extraer_departamento(entidad),
                            "Fecha Publicación": fecha_pub.replace("Fecha de publicación:", "").strip(),
                            "Enlace": enlace
                        }
                        todas_licitaciones.append(lic)
                    except Exception:
                        continue

                if len(todas_licitaciones) >= max_cards:
                    break

                next_btn = await page.query_selector("button.mat-mdc-paginator-navigation-next")
                if not next_btn or await next_btn.is_disabled():
                    break
                await next_btn.click()
                await page.wait_for_timeout(4000)
                page_count += 1

            return todas_licitaciones
        finally:
            await context.close()
            await browser.close()