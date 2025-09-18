# Proyecto de Scraping Antecedentes Penales

Este proyecto permite consultar certificados de antecedentes penales del Ministerio del Interior de Ecuador, usando Playwright para simular un navegador real y superar las protecciones anti-bot.

## Instalación

1. Crear entorno virtual: `python -m venv .venv`
2. Activar: `.venv\Scripts\Activate.ps1`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Instalar navegador: `playwright install firefox`

## Características

- **Stealth Mode**: Implementación avanzada para evitar detección como bot
- **Gestión de Cookies**: Guarda/carga cookies para mantener sesiones
- **Resolución de Captcha**: Intenta resolver captchas automáticamente
- **Logging detallado**: Guarda screenshots para depuración

## Uso

### Ejecutar el scraper directamente

```python
from scraper import get_antecedentes
import asyncio

# Parámetros:
# - headless: False para ver el navegador, True para modo invisible
# - usar_cookies: True para cargar cookies guardadas (reduce captchas)
result = asyncio.run(get_antecedentes(
    cedula='1718997784',  # Usar una cédula real
    headless=False,  
    usar_cookies=True
))
print(result)
```

### Ejecutar el endpoint

```bash
python app.py
```

Luego, hacer GET a `http://localhost:5000/antecedentes/<cedula>`

## Archivos Generados

- **cookies.json**: Almacena cookies de sesión (válidas por 3 horas)
- **pagina_inicial.png**: Screenshot de la página inicial
- **captcha_frame.png**: Screenshot del iframe de captcha si se detecta

## Notas

- El sitio usa protección Incapsula y hCaptcha que puede requerir intervención manual
- Las cookies guardadas ayudan a reducir la frecuencia de captchas
- Para producción, considerar un servicio de resolución de captchas
