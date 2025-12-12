from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
import logging

from app.scraper import scrape_seace_playwright
from app.cubso_extractor import extraer_cubso_batch

# Configuración
app = FastAPI(
    title="SEACE Scraper API",
    description="API para extraer licitaciones públicas del SEACE (Perú)",
    version="1.0.0"
)

# Logging básico
logging.basicConfig(level=logging.INFO)

@app.get("/scrape", response_model=List[dict])
async def scrape_endpoint(
        fecha_inicio: str = Query(..., pattern=r"^\d{2}/\d{2}/\d{4}$", description="dd/mm/yyyy"),
        fecha_fin: str = Query(..., pattern=r"^\d{2}/\d{2}/\d{4}$", description="dd/mm/yyyy"),
        max_licitaciones: int = Query(100, ge=10, le=500),
        incluir_cubso: bool = Query(False, description="Si True, extrae CUBSO (más lento)")
):
    """
    Extrae licitaciones del SEACE en un rango de fechas.
    """
    try:
        # Paso 1: Scrape inicial
        resultados = await scrape_seace_playwright(fecha_inicio, fecha_fin, max_licitaciones)
        if not resultados:
            return JSONResponse(content=[], status_code=200)

        # Paso 2: Extraer CUBSO si se pide
        if incluir_cubso:
            urls = [(r["Código"], r["Enlace"]) for r in resultados if r["Enlace"] != "No disponible"]
            if urls:
                cubso_data = await extraer_cubso_batch(urls)
                cubso_map = {item["Código"]: item["CUBSO"] for item in cubso_data}
                for r in resultados:
                    r["CUBSO"] = cubso_map.get(r["Código"], "No extraído")
            else:
                for r in resultados:
                    r["CUBSO"] = "No disponible"

        return resultados

    except Exception as e:
        logging.error(f"Error en scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")