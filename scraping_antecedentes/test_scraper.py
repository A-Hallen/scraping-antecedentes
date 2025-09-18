from scraper import get_antecedentes
import asyncio

if __name__ == '__main__':
    # Cédula para prueba (debe ser una cédula válida de Ecuador)
    cedula = '1718997784'  # Reemplazar con una cédula real para pruebas
    
    # Parámetros:
    # headless=False - Mostrar el navegador para depurar
    # usar_cookies=True - Intentar usar cookies guardadas (reduce captchas)
    result = asyncio.run(get_antecedentes(
        cedula=cedula, 
        headless=False,  # False para ver el navegador, True para modo invisible
        usar_cookies=True  # Intentar cargar cookies guardadas
    ))
    
    print(result)
