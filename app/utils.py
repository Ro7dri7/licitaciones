from datetime import datetime

DEPARTAMENTOS_PERU = [
    "Amazonas", "Áncash", "Apurímac", "Arequipa", "Ayacucho", "Cajamarca",
    "Cusco", "Huancavelica", "Huánuco", "Ica", "Junín", "La Libertad",
    "Lambayeque", "Lima", "Loreto", "Madre de Dios", "Moquegua", "Pasco",
    "Piura", "Puno", "San Martín", "Tacna", "Tumbes", "Ucayali"
]

def parse_fecha_seace(fecha_str: str) -> datetime:
    try:
        fecha_str = fecha_str.replace("Fecha de publicación:", "").strip()
        return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
    except Exception:
        return None

def fecha_en_rango(fecha_str: str, fecha_inicio: str, fecha_fin: str) -> bool:
    fecha = parse_fecha_seace(fecha_str)
    if not fecha:
        return False
    inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
    fin = datetime.strptime(fecha_fin, "%d/%m/%Y")
    return inicio.date() <= fecha.date() <= fin.date()

def extraer_tipo(desc: str) -> str:
    if not isinstance(desc, str):
        return "Otro"
    d = desc.lower()
    if d.startswith("bien:"): return "Bien"
    elif d.startswith("servicio:"): return "Servicio"
    elif d.startswith("obra:"): return "Obra"
    elif "consultor" in d: return "Consultoría"
    else: return "Otro"

def extraer_departamento(entidad: str) -> str:
    if not isinstance(entidad, str):
        return "No identificado"
    u = entidad.upper()
    for d in DEPARTAMENTOS_PERU:
        if d.upper() in u:
            return d
    return "No identificado"