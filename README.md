# Script de Monitoreo de Archivos con watchdog
Este script monitorea una carpeta en busca de eventos de creación, eliminación y modificación de archivos .jar. Cada vez que se detecta un cambio, el archivo afectado se copia a una carpeta específica y se registra el evento.

## Requisitos
Para ejecutar el script, necesitas tener instalados los siguientes paquetes:

Python 3.x: El script está escrito en Python, por lo que necesitas una instalación de Python 3.x.
Watchdog: Es la librería utilizada para monitorear los cambios en el sistema de archivos.
Puedes instalar watchdog ejecutando el siguiente comando en tu terminal:

bash
Copiar código
pip install watchdog

## Estructura de Carpetas

### Carpetas Principales:
Origen: Carpeta que se monitorea para cambios de archivos (creación, eliminación, modificación).
Destino: Carpeta donde se crean subcarpetas para registrar los eventos.

### Carpetas de Registro:
Dentro de Destino, el script creará una carpeta llamada RegistroJar con el formato RegistroJar_DD-MM-YYYY-HH, que contendrá subcarpetas para cada tipo de evento:
creados-HH: Archivos recién creados.
eliminados-HH: Archivos eliminados, con un archivo .txt que documenta el evento.
modificados-HH: Archivos que han sido modificados.
Si ya existe una carpeta RegistroJar con una diferencia de tiempo menor a 6 horas, el script creará nuevas subcarpetas de eventos basadas en la hora actual.

## Funcionalidades
Detección de eventos: Monitorea cambios en los archivos .jar dentro de una carpeta específica.
Copia de archivos: Copia archivos creados o modificados a carpetas específicas dentro de Destino.
Registro de eventos: Crea un archivo registro_eventos.txt que documenta los eventos (creación, modificación y eliminación) con la hora correspondiente.
Comparación de nombres: Si los archivos difieren solo en la versión, se detectan como archivos relacionados (por ejemplo, al eliminar una versión anterior y crear una nueva).

## Uso
1. Configuración Inicial
En el script, configura las rutas de origen y destino modificando las siguientes variables:

python
Copiar código
origen = "Carpeta\\Origen"
ruta_destino = "Carpeta\\Destino"
2. Ejecutar el Script
Una vez configurado, puedes ejecutar el script en tu terminal o entorno de desarrollo de Python:

bash
Copiar código
python watch.py
3. Eventos Registrados
Cada vez que se detecta un evento (creación, eliminación o modificación), el archivo afectado será copiado a la carpeta correspondiente dentro de Destino, y un registro del evento será añadido a registro_eventos.txt.

4. Manejo de Errores
El script tiene reintentos para copiar archivos que están en uso (por ejemplo, si otro proceso está accediendo al archivo). Si tras varios intentos no se puede copiar el archivo, se registra un error en el archivo de registro.

## Funciones Clave
intentar_copiar_archivo()
Esta función copia un archivo desde la carpeta de origen a la carpeta de destino. En caso de un error de permisos, reintenta varias veces con una pausa entre cada intento.

comparar_nombres()
Compara dos archivos quitando versiones del nombre (por ejemplo, quitando "build.XXXX") para determinar si los archivos están relacionados.

procesar_modificacion()
Copia un archivo modificado a la carpeta de modificados y registra el evento.

## Lógica de Fechas y Horas
El script maneja las carpetas de destino basadas en la fecha y la hora:

Si existe una carpeta con la fecha actual y la hora dentro de un margen de 6 horas, el script crea nuevas subcarpetas dentro de esa carpeta.
Si no existe una carpeta con esas condiciones, se crea una nueva carpeta RegistroJar con la fecha y hora actuales.

## Contribuciones
Si deseas contribuir a este proyecto, puedes hacer un fork del repositorio, hacer tus cambios y luego abrir un pull request.

