from playwright_stealth import Stealth
from playwright.async_api import async_playwright
import time
import base64
import random
import json
import os
from datetime import datetime

async def guardar_cookies(context, filename='cookies.json'):
    """Guarda las cookies de la sesión en un archivo"""
    cookies = await context.cookies()
    
    # Añadir timestamp para saber cuándo se guardaron
    data = {
        'timestamp': datetime.now().isoformat(),
        'cookies': cookies
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Cookies guardadas en {filename}")

async def cargar_cookies(context, filename='cookies.json'):
    """Carga las cookies desde un archivo si existe"""
    if not os.path.exists(filename):
        print(f"No se encontró archivo de cookies: {filename}")
        return False
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Verificar si las cookies son recientes (menos de 3 horas)
        timestamp = datetime.fromisoformat(data['timestamp'])
        ahora = datetime.now()
        diff = (ahora - timestamp).total_seconds() / 3600  # horas
        
        if diff > 3:
            print(f"Cookies expiradas (guardadas hace {diff:.1f} horas)")
            return False
        
        await context.add_cookies(data['cookies'])
        print(f"Cookies cargadas desde {filename} (guardadas hace {diff:.1f} horas)")
        return True
    except Exception as e:
        print(f"Error cargando cookies: {str(e)}")
        return False

async def get_antecedentes(cedula, headless=True, usar_cookies=True):
    print("Iniciando scraper con Playwright...")
    
    async with Stealth().use_async(async_playwright()) as p:
        # Iniciar navegador Firefox
        browser = await p.firefox.launch(headless=headless)
        # Configuración del contexto
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            locale='es-ES',
            timezone_id='America/Guayaquil'
        )
        
        # Intentar cargar cookies si usar_cookies=True
        cookies_cargadas = False
        if usar_cookies:
            cookies_cargadas = await cargar_cookies(context)
        
        page = await context.new_page()
        
        # Configuraciones adicionales para parecer más humano
        await page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        }
        """)

        try:
            url = 'https://certificados.ministeriodelinterior.gob.ec/gestorcertificados/antecedentes/'
            print(f"Navegando a: {url}")
            
            # Navegar a la página
            await page.goto(url, wait_until='load', timeout=30000)
            
            # Esperar a que cargue completamente
            await page.wait_for_timeout(3000)
            
            # Verificar si llegamos a la página correcta
            page_content = await page.content()
            
            # Tomar screenshot para debug
            await page.screenshot(path="pagina_inicial.png")
            print("Screenshot guardado como pagina_inicial.png")
            
            # Guardar HTML para depuración
            with open('pagina_recibida.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("HTML guardado en pagina_recibida.html")
            
            # Buscar indicadores de captcha con mejor detección
            captcha_indicators = ['hcaptcha', 'captcha', 'checkbox', 'challenge', 'security check',
                                  'verificación', 'verificacion', 'robot', 'humano', 'iframe']
                                  
            found_captcha = False
            for indicator in captcha_indicators:
                if indicator in page_content.lower():
                    found_captcha = True
                    print(f"Indicador de captcha encontrado: '{indicator}'")
            
            # Verificar captchas directamente
            print("Buscando iframes o elementos de captcha...")
            iframes = page.locator('iframe')
            iframe_count = await iframes.count()
            print(f"Total de iframes encontrados: {iframe_count}")
            
            # Intentar forzar la detección del captcha independientemente
            try:
                # Buscar botones interactivos en la página principal
                checkboxes = page.locator('input[type="checkbox"], div[role="checkbox"]')
                checkbox_count = await checkboxes.count()
                print(f"Checkboxes encontrados en página principal: {checkbox_count}")
                
                if checkbox_count > 0:
                    found_captcha = True
                    print("Checkbox detectado en la página principal")
            except Exception as e:
                print(f"Error buscando checkboxes: {str(e)}")
                
            # SIEMPRE intentar resolver captcha al principio
            found_captcha = True
            
            if found_captcha:
                print("Detectado hCaptcha - intentando resolver...")
                try:
                    # obtain the iFrame containing the CAPTCHA box
                    captcha_frame = await page.wait_for_selector("iframe[src*='recaptcha']")

                    print("iframe encontrado")

                    # switch to the content of the CAPTCHA iframe
                    captcha_frame_content = await captcha_frame.content_frame()
                    
                    print("iframe contenido encontrado")

                    # extract site key for the CAPTCHA
                    site_key = captcha_frame.get_attribute("src").split("k=")[-1].split("&")[0]

                    print(f"Site key: {site_key}")

                    # get the CAPTCHA checkbox element
                    captcha_checkbox = await captcha_frame_content.wait_for_selector("#recaptcha-anchor")

                    # click the CAPTCHA checkbox
                    await captcha_checkbox.click()

                    # solve CAPTCHA after this
                    # captcha_response = solver.recaptcha(sitekey=site_key, url=url)
                    # # extract the Turnstile token from the response
                    # captcha_token = captcha_response["code"]
                except Exception as e:
                    print(f"Error al intentar resolver captcha: {str(e)}")
                    
            # Actualizar el contenido de la página después de la posible resolución del captcha
            await page.wait_for_timeout(3000)  # Esperar que cargue cualquier redireccionamiento
            page_content = await page.content()
            
            # Guardar una nueva copia del HTML
            with open('pagina_despues_captcha.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("HTML actualizado guardado en pagina_despues_captcha.html")
            
            # Tomar otro screenshot
            await page.screenshot(path="pagina_despues_captcha.png")
            print("Screenshot actualizado guardado como pagina_despues_captcha.png")
            
            # Verificaciones en el contenido de la página
            content_indicators = [
                {'text': 'CERTIFICADO DE ANTECEDENTES PENALES', 'weight': 10},
                {'text': 'cedula', 'weight': 5},
                {'text': 'cédula', 'weight': 5},
                {'text': 'ministerio', 'weight': 3},
                {'text': 'ecuador', 'weight': 3},
                {'text': 'identidad', 'weight': 2},
                {'text': 'formulario', 'weight': 2},
                {'text': 'consulta', 'weight': 2}
            ]
            
            # Calcular score para determinar si estamos en la página correcta
            content_score = 0
            found_indicators = []
            
            for indicator in content_indicators:
                if indicator['text'] in page_content.lower():
                    content_score += indicator['weight']
                    found_indicators.append(indicator['text'])
            
            print(f"Score de contenido: {content_score}, indicadores encontrados: {found_indicators}")
            
            # Verificar si hay elementos UI específicos
            ui_elements_found = []
            try:
                cedula_input = page.locator('#txtCi')
                if await cedula_input.is_visible(timeout=1000):
                    print("Campo de cédula encontrado")
                    ui_elements_found.append('campo_cedula')
                    content_score += 10
            except Exception:
                pass
                
            # Si el score es demasiado bajo, probablemente no estamos en la página correcta
            if content_score < 5 and not ui_elements_found:
                return {'status': 'error', 'message': 'No se pudo acceder a la página - posible bloqueo'}
            
            print(f"Página cargada con score {content_score} y elementos UI: {ui_elements_found}")
            
            # Ya se imprime un mensaje más detallado arriba
            
            # Aceptar el diálogo de términos y condiciones si aparece
            try:
                accept_button = page.locator('button:has-text("Aceptar")')
                if await accept_button.is_visible(timeout=5000):
                    print("Aceptando términos y condiciones...")
                    await accept_button.click()
                    await page.wait_for_timeout(1000)
            except:
                print("No se encontró diálogo de términos")
            
            # Llenar el formulario
            print(f"Ingresando cédula: {cedula}")
            
            # Seleccionar "SI" para ecuatoriano (por defecto)
            ecuatoriano_select = page.locator('#cmbEcuatoriano')
            await ecuatoriano_select.select_option('SI')
            
            # Seleccionar cédula (por defecto ya está seleccionado)
            cedula_radio = page.locator('#rbtType1')
            await cedula_radio.check()
            
            # Ingresar la cédula
            cedula_input = page.locator('#txtCi')
            await cedula_input.fill(cedula)
            
            # Hacer clic en el botón "Siguiente"
            next_button = page.locator('#btnSig1')
            print("Haciendo clic en Siguiente...")
            await next_button.click()
            
            # Esperar respuesta del servidor
            await page.wait_for_timeout(5000)
            
            # Verificar si hay errores
            try:
                error_dialog = page.locator('#dvSimpleDialog')
                if await error_dialog.is_visible():
                    error_text = await error_dialog.inner_text()
                    return {'status': 'error', 'message': f'Error del sitio: {error_text}'}
            except:
                pass
            
            # Verificar si aparece el segundo tab (motivo)
            try:
                tab2 = page.locator('#tab2')
                if await tab2.is_visible(timeout=10000):
                    print("Apareció el segundo paso - ingresando motivo...")
                    
                    # Ingresar motivo de consulta
                    motivo_input = page.locator('#txtMotivo')
                    await motivo_input.fill('Consulta de antecedentes penales para trámites personales')
                    
                    # Hacer clic en siguiente
                    next_button2 = page.locator('#btnSig2')
                    await next_button2.click()
                    
                    # Esperar a que aparezca el certificado
                    await page.wait_for_timeout(10000)
                    
                    # Buscar el botón de abrir certificado
                    try:
                        open_button = page.locator('#btnOpen')
                        if await open_button.is_visible(timeout=10000):
                            print("Certificado disponible!")
                            
                            # Extraer información de la página
                            page_content = await page.content()
                            
                            return {
                                'status': 'success', 
                                'message': 'Certificado generado exitosamente',
                                'data': {
                                    'cedula': cedula,
                                    'certificado_disponible': True,
                                    'contenido_parcial': page_content[:1000] + '...'
                                }
                            }
                        else:
                            return {'status': 'error', 'message': 'No se pudo generar el certificado'}
                    except Exception as e:
                        return {'status': 'error', 'message': f'Error procesando certificado: {str(e)}'}
                        
            except Exception as e:
                return {'status': 'error', 'message': f'Error en segundo paso: {str(e)}'}
            
            return {'status': 'error', 'message': 'No se pudo completar el proceso'}
            
        except Exception as e:
            print(f"Error general: {str(e)}")
            return {'status': 'error', 'message': f'Error del navegador: {str(e)}'}
        
        finally:
            # Guardar cookies si tuvimos éxito
            try:
                await guardar_cookies(context)
            except Exception as e:
                print(f"Error al guardar cookies: {str(e)}")
                
            await browser.close()
