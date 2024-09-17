import os
import shutil
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración 
origen = "C:\\Users\\angel\\Desktop\\watch\\ejemplo"
ruta_creados = "C:\\Users\\angel\\Desktop\\watch\\copiaJa\\nuevos"
ruta_eliminados = "C:\\Users\\angel\\Desktop\\watch\\copiaJa\\eliminados"
ruta_modificados = "C:\\Users\\angel\\Desktop\\watch\\copiaJa\\modificados"

# Crear directorios si no existen
for ruta in [ruta_creados, ruta_eliminados, ruta_modificados]:
    os.makedirs(ruta, exist_ok=True)

extensiones_a_monitorear = ['.jar']
archivos_eliminados = {}  # Diccionario para rastrear archivos eliminados recientes
archivos_creados_recientes = {}  # Diccionario para rastrear archivos creados recientemente

# Expresión regular para eliminar las versiones de los nombres de archivos
regex_version = r"[-_]\d+\.\d+(\.\d+)?"

# Tiempo de gracia para detectar la creación/eliminación como un par relacionado (en segundos)
tiempo_gracia = 3

# Handler para eventos del sistema de archivos
class ModificacionHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return
        if self.es_extension_jar(event.src_path):
            print(f"Archivo creado: {event.src_path}")
            nombre_archivo_creado = os.path.basename(event.src_path)

            # Verificar si coincide con un archivo eliminado recientemente
            archivo_eliminado_encontrado = None
            for archivo_eliminado, tiempo_eliminacion in list(archivos_eliminados.items()):
                if self.comparar_nombres(nombre_archivo_creado, archivo_eliminado) and time.time() - tiempo_eliminacion < tiempo_gracia:
                    archivo_eliminado_encontrado = archivo_eliminado
                    break

            if archivo_eliminado_encontrado:
                # Coincidencia encontrada con una eliminación reciente, proceder a reemplazar el archivo eliminado
                nombre_carpeta = f"remplazo y actualizacion de archivo {archivo_eliminado_encontrado}"
                ruta_carpeta = os.path.join(ruta_creados, nombre_carpeta)
                os.makedirs(ruta_carpeta, exist_ok=True)
                shutil.copy2(event.src_path, ruta_carpeta)
                nombre_txt = os.path.join(ruta_carpeta, f"{archivo_eliminado_encontrado}_eliminado_.txt")
                with open(nombre_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {archivo_eliminado_encontrado}")
                print(f"Carpeta creada: {ruta_carpeta}, archivo nuevo copiado y registro de eliminación guardado.")
                del archivos_eliminados[archivo_eliminado_encontrado]
            else:
                # Registrar el archivo como creado recientemente para manejar posibles eliminaciones posteriores
                archivos_creados_recientes[nombre_archivo_creado] = time.time()
                # Copiar el archivo como nuevo si no se encuentra una eliminación
                shutil.copy2(event.src_path, ruta_creados)
                print(f"Archivo copiado a {ruta_creados}: {event.src_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        if self.es_extension_jar(event.src_path):
            print(f"Archivo eliminado: {event.src_path}")
            nombre_archivo_eliminado = os.path.basename(event.src_path)

            # Verificar si coincide con un archivo creado recientemente
            archivo_creado_encontrado = None
            for archivo_creado, tiempo_creacion in list(archivos_creados_recientes.items()):
                if self.comparar_nombres(nombre_archivo_eliminado, archivo_creado) and time.time() - tiempo_creacion < tiempo_gracia:
                    archivo_creado_encontrado = archivo_creado
                    break

            if archivo_creado_encontrado:
                # Coincidencia encontrada con una creación reciente, proceder a reemplazar el archivo eliminado
                nombre_carpeta = f"remplazo y actualizacion de archivo {nombre_archivo_eliminado}"
                ruta_carpeta = os.path.join(ruta_creados, nombre_carpeta)
                os.makedirs(ruta_carpeta, exist_ok=True)
                # El archivo ya ha sido copiado cuando fue creado, solo se necesita registrar la eliminación
                nombre_txt = os.path.join(ruta_carpeta, f"{nombre_archivo_eliminado}_eliminado_.txt")
                with open(nombre_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {nombre_archivo_eliminado}")
                print(f"Carpeta creada: {ruta_carpeta}, archivo nuevo ya copiado y registro de eliminación guardado.")
                del archivos_creados_recientes[archivo_creado_encontrado]
            else:
                # Registrar el archivo como eliminado recientemente para manejar posibles creaciones posteriores
                archivos_eliminados[nombre_archivo_eliminado] = time.time()
                # Crear un registro de eliminación como respaldo si no hay creación
                ruta_txt = os.path.join(ruta_eliminados, f"{nombre_archivo_eliminado}-eliminado-.txt")
                with open(ruta_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {nombre_archivo_eliminado}")
                print(f"Registro de eliminación creado: {ruta_txt}")

    def on_modified(self, event):
        if event.is_directory:
            return
        if self.es_extension_jar(event.src_path):
            # Ignorar modificaciones que ocurran justo después de la creación del archivo
            tiempo_creacion = archivos_creados_recientes.get(os.path.basename(event.src_path))
            if tiempo_creacion and time.time() - tiempo_creacion < tiempo_gracia:
                print(f"Modificación ignorada para {event.src_path}, ocurrió justo después de la creación.")
                return
            print(f"Archivo modificado: {event.src_path}")
            self.procesar_modificacion(event.src_path)

    def es_extension_jar(self, archivo):
        _, extension = os.path.splitext(archivo)
        return extension in extensiones_a_monitorear

    def procesar_modificacion(self, archivo_modificado):
        nombre_archivo_modificado = os.path.basename(archivo_modificado)
        shutil.copy2(archivo_modificado, ruta_modificados)
        nombre_txt = os.path.join(ruta_modificados, f"{nombre_archivo_modificado}_modificado_.txt")
        with open(nombre_txt, 'w') as f:
            f.write(f"Archivo modificado: {nombre_archivo_modificado}")
        print(f"Archivo modificado copiado a {ruta_modificados} y registro creado.")

    def comparar_nombres(self, nombre1, nombre2):
        # Quitar las versiones de los nombres
        nombre1_sin_version = re.sub(regex_version, '', nombre1)
        nombre2_sin_version = re.sub(regex_version, '', nombre2)
        return nombre1_sin_version == nombre2_sin_version

# Configurar watchdog
event_handler = ModificacionHandler()
observer = Observer()
observer.schedule(event_handler, origen, recursive=True)

# Iniciar la observación
observer.start()
print(f"Monitoreando la carpeta '{origen}' para archivos {extensiones_a_monitorear}...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
