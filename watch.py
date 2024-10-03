from datetime import datetime, timedelta
import os
import shutil
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración de directorios
origen = "C:\\Users\\angel\\OneDrive\\Escritorio\\watch\\ejemplo"
ruta_destino = "C:\\Users\\angel\\OneDrive\\Escritorio\\watch\\copiaJa"

# Obtener fecha y hora actuales
fecha_actual = datetime.now().strftime("%dD-%mM-%YY")
hora_actual = datetime.now().strftime("%H")  # Solo la hora

# Buscar carpeta "RegistroJar" con la fecha actual y una hora con diferencia menor a 6 horas
def buscar_carpeta_registro():
    for carpeta in os.listdir(ruta_destino):
        if "RegistroJar" in carpeta:
            fecha_hora_carpeta = re.search(r"(\d{2}D-\d{2}M-\d{4}Y)-(\d{2}H)", carpeta)
            if fecha_hora_carpeta:
                fecha_carpeta, hora_carpeta = fecha_hora_carpeta.groups()
                if fecha_carpeta == fecha_actual:
                    diferencia_horas = abs(int(hora_actual) - int(hora_carpeta[:-1]))
                    if diferencia_horas <= 6:
                        return os.path.join(ruta_destino, carpeta)
    return None

# Crear carpeta "RegistroJar" con la fecha y hora actuales
def crear_carpeta_registro():
    nombre_carpeta_registro = f"RegistroJar_{fecha_actual}-{hora_actual}H"
    ruta_carpeta_registro = os.path.join(ruta_destino, nombre_carpeta_registro)
    os.makedirs(ruta_carpeta_registro, exist_ok=True)
    return ruta_carpeta_registro

# Crear carpeta de eventos (creados, eliminados, modificados) con la hora actual
def crear_carpeta_eventos(ruta_registro):
    carpeta_creados = os.path.join(ruta_registro, f"creados-{hora_actual}H")
    carpeta_eliminados = os.path.join(ruta_registro, f"eliminados-{hora_actual}H")
    carpeta_modificados = os.path.join(ruta_registro, f"modificados-{hora_actual}H")
    for carpeta in [carpeta_creados, carpeta_eliminados, carpeta_modificados]:
        os.makedirs(carpeta, exist_ok=True)
    return carpeta_creados, carpeta_eliminados, carpeta_modificados

# Actualizar archivo de registro de eventos
def registrar_evento(ruta_registro, evento):
    archivo_registro = os.path.join(ruta_registro, "registro_eventos.txt")
    with open(archivo_registro, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {evento}\n")

# Configuración inicial
ruta_registro = buscar_carpeta_registro()
if not ruta_registro:
    ruta_registro = crear_carpeta_registro()
carpeta_creados, carpeta_eliminados, carpeta_modificados = crear_carpeta_eventos(ruta_registro)

# Extensiones a monitorear
extensiones_a_monitorear = ['.jar']
archivos_eliminados = {}
archivos_creados_recientes = {}

# Expresión regular para eliminar versiones de nombres de archivos
regex_version = r"[-_](\d+\.\d+(\.\d+)?|build\.\d+)"
tiempo_gracia = 2
max_reintentos = 5

def intentar_copiar_archivo(origen, destino, intentos=0):
    try:
        shutil.copy2(origen, destino)
        registrar_evento(ruta_registro, f"Archivo copiado a {destino}: {origen}")
    except PermissionError as e:
        if intentos < max_reintentos:
            print(f"Error: {e}. Reintentando en 1 segundo... (Intento {intentos + 1})")
            time.sleep(1)
            intentar_copiar_archivo(origen, destino, intentos + 1)
        else:
            registrar_evento(ruta_registro, f"Error al copiar {origen}: {e}")
            print(f"Error al copiar {origen}: {e}")

# Handler para eventos del sistema de archivos
class ModificacionHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory: 
            return
        if self.es_extension_jar(event.src_path):
            registrar_evento(ruta_registro, f"Archivo creado: {event.src_path}")
            nombre_archivo_creado = os.path.basename(event.src_path)

            # Verificar si coincide con un archivo eliminado recientemente
            archivo_eliminado_encontrado = None
            for archivo_eliminado, tiempo_eliminacion in list(archivos_eliminados.items()):
                if self.comparar_nombres(nombre_archivo_creado, archivo_eliminado) and time.time() - tiempo_eliminacion < tiempo_gracia:
                    archivo_eliminado_encontrado = archivo_eliminado
                    break

            if archivo_eliminado_encontrado:
                # Coincidencia encontrada con una eliminación reciente, nombrar la carpeta con el archivo creado
                nombre_carpeta = f"remplazo y actualizacion de archivo {archivo_eliminado_encontrado}"
                ruta_carpeta = os.path.join(carpeta_creados, nombre_carpeta)
                os.makedirs(ruta_carpeta, exist_ok=True)
                intentar_copiar_archivo(event.src_path, ruta_carpeta)  # Copiar el archivo nuevo a la carpeta
                nombre_txt = os.path.join(ruta_carpeta, f"{archivo_eliminado_encontrado}_eliminado_.txt")
                with open(nombre_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {nombre_archivo_creado}")
                registrar_evento(ruta_registro, f"Carpeta creada: {ruta_carpeta}, archivo nuevo copiado y registro de eliminación guardado.")
                print(f"Carpeta creada: {ruta_carpeta}, archivo nuevo copiado y registro de eliminación guardado.")
                del archivos_eliminados[archivo_eliminado_encontrado]
            else:
                # Registrar el archivo como creado recientemente para manejar posibles eliminaciones posteriores
                archivos_creados_recientes[nombre_archivo_creado] = time.time()
                # Copiar el archivo como nuevo si no se encuentra una eliminación
                intentar_copiar_archivo(event.src_path, carpeta_creados)

    def on_deleted(self, event):
        if event.is_directory:
            return
        if self.es_extension_jar(event.src_path):
            registrar_evento(ruta_registro, f"Archivo eliminado: {event.src_path}")
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
                ruta_carpeta = os.path.join(carpeta_creados, nombre_carpeta)
                os.makedirs(ruta_carpeta, exist_ok=True)

                # Verificar si el archivo ya está en ruta_creados
                archivo_en_ruta_creados = os.path.join(carpeta_creados, archivo_creado_encontrado)
                if os.path.exists(archivo_en_ruta_creados):
                    # Mover el archivo creado a la nueva carpeta
                    shutil.move(archivo_en_ruta_creados, ruta_carpeta)
                    registrar_evento(ruta_registro, f"Archivo {archivo_creado_encontrado} movido a {ruta_carpeta}")

                # El archivo ya ha sido copiado cuando fue creado, solo se necesita registrar la eliminación
                nombre_txt = os.path.join(ruta_carpeta, f"{nombre_archivo_eliminado}_eliminado_.txt")
                with open(nombre_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {nombre_archivo_eliminado}")
                registrar_evento(ruta_registro, f"Carpeta creada: {ruta_carpeta}, archivo nuevo ya copiado y registro de eliminación guardado.")
                print(f"Carpeta creada: {ruta_carpeta}, archivo nuevo ya copiado y registro de eliminación guardado.")
                del archivos_creados_recientes[archivo_creado_encontrado]
            else:
                # Registrar el archivo como eliminado recientemente para manejar posibles creaciones posteriores
                archivos_eliminados[nombre_archivo_eliminado] = time.time()
                # Crear un registro de eliminación como respaldo si no hay creación
                ruta_txt = os.path.join(carpeta_eliminados, f"{nombre_archivo_eliminado}-eliminado-.txt")
                with open(ruta_txt, 'w') as f:
                    f.write(f"Archivo eliminado: {nombre_archivo_eliminado}")
                registrar_evento(ruta_registro, f"Registro de eliminación creado: {ruta_txt}")
                print(f"Registro de eliminación creado: {ruta_txt}")

    def on_modified(self, event):
        if event.is_directory:
            return
        if self.es_extension_jar(event.src_path):
            # Ignorar modificaciones que ocurran justo después de la creación del archivo
            tiempo_creacion = archivos_creados_recientes.get(os.path.basename(event.src_path))
            if tiempo_creacion and time.time() - tiempo_creacion < tiempo_gracia:
                registrar_evento(ruta_registro, f"Archivo modificado: {event.src_path}")
                return
            registrar_evento(ruta_registro, f"Archivo modificado: {event.src_path}")
            print(f"Archivo modificado: {event.src_path}")
            self.procesar_modificacion(event.src_path)

    def es_extension_jar(self, archivo):
        _, extension = os.path.splitext(archivo)
        return extension in extensiones_a_monitorear

    def procesar_modificacion(self, archivo_modificado):
        nombre_archivo_modificado = os.path.basename(archivo_modificado)
        intentar_copiar_archivo(archivo_modificado, carpeta_modificados)
        nombre_txt = os.path.join(carpeta_modificados, f"{nombre_archivo_modificado}_modificado_.txt")
        with open(nombre_txt, 'w') as f:
            f.write(f"Archivo modificado: {nombre_archivo_modificado}")
        registrar_evento(ruta_registro, f"Archivo modificado copiado a {carpeta_modificados} y registro creado.")
        print(f"Archivo modificado copiado a {carpeta_modificados} y registro creado.")
    def comparar_nombres(self, nombre1, nombre2):
        # Quitar las versiones de los nombres, incluyendo las versiones con "build"
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
