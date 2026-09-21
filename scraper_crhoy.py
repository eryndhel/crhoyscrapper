import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin

URL_OBJETIVO = "https://crhoy.com/nacionales/"
BASE_URL = "https://crhoy.com"

# 1. Configuración de headers para evitar bloqueos por bot
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CR,es;q=0.9",
}

print(f"Descargando noticias desde {URL_OBJETIVO}...")
response = requests.get(URL_OBJETIVO, headers=headers, timeout=15)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# 2. Configurar el feed RSS
fg = FeedGenerator()
fg.title("CRHoy - Nacionales")
fg.link(href=URL_OBJETIVO, rel="alternate")
fg.description("Feed RSS generado automáticamente para la sección Nacionales de CRHoy.")
fg.language("es")

# 3. Localizar los contenedores de noticias
# Se buscan contenedores de artículos habituales en CRHoy
articulos = soup.find_all("article")
if not articulos:
    # Selector de respaldo si no usan etiquetas semánticas <article>
    articulos = soup.select(".noticia, .post, .item-noticia, .c-article")

items_procesados = 0
enlaces_vistos = set()

for art in articulos:
    # A. Buscar el título y enlace (suele residir en un h2/h3 con etiqueta <a>)
    encabezado = art.find(["h2", "h3", "h1"])
    link_tag = art.find("a", href=True)

    if not encabezado and not link_tag:
        continue

    # Si hay encabezado con enlace adentro, se prioriza
    if encabezado and encabezado.find("a", href=True):
        link_tag = encabezado.find("a", href=True)
        titulo = link_tag.get_text(strip=True)
    elif encabezado:
        titulo = encabezado.get_text(strip=True)
    else:
        titulo = link_tag.get_text(strip=True)

    if not titulo:
        continue

    url_noticia = urljoin(BASE_URL, link_tag["href"])

    # Evitar duplicados y enlaces irrelevantes (categorías, autores)
    if url_noticia in enlaces_vistos or "/nacionales/" not in url_noticia or url_noticia == URL_OBJETIVO:
        continue

    # B. Buscar la bajada de texto o resumen
    bajada_tag = art.find("p") or art.select_one(".resumen, .bajada, .excerpt, .entry-content")
    bajada = bajada_tag.get_text(strip=True) if bajada_tag else ""

    # C. Si la portada no muestra la bajada completa, usar el título o descripción genérica
    descripcion_final = bajada if bajada else titulo

    # D. Agregar el ítem al canal RSS
    fe = fg.add_entry()
    fe.id(url_noticia)
    fe.title(titulo)
    fe.link(href=url_noticia)
    fe.description(descripcion_final)

    enlaces_vistos.add(url_noticia)
    items_procesados += 1

    # Limitar a las 20 noticias más recientes
    if items_procesados >= 20:
        break

# 4. Guardar archivo XML
archivo_salida = "feed_crhoy_nacionales.xml"
fg.rss_file(archivo_salida, pretty=True)

print(f"Listo. Se agregaron {items_procesados} noticias a '{archivo_salida}'.")