# Manual de usuario

## Arranque

    python -m meshcad

## Interfaz

- Barra de herramientas: Seleccionar, Linea, Arco, Spline,
  Generar malla, Borrar malla.
- Menu Archivo: Nuevo, Abrir, Guardar, Guardar como, Exportar malla (VTK).
- Panel izquierdo Loops.
- Paneles derechos Distribuciones y Bloques.

## Flujo tipico

### 1. Dibujar geometria

Pulsa Linea (2 clics), Arco (3 clics: centro, inicio, fin) o
Spline (varios clics + clic derecho para terminar). Mientras mueves
el raton se ve la forma en tiempo real (linea discontinua).

Los vertices existentes se muestran como circulos rojos. Al pasar
cerca con el cursor, la geometria hace snapping.

Escape cancela la herramienta activa.

### 2. Crear un loop

En el panel Loops, pulsa Detectar loops. Se listan los contornos
cerrados. Al seleccionar uno se ilumina en verde sobre el lienzo.

### 3. Crear un bloque

Con un loop seleccionado, pulsa Crear bloque del loop. Haz clic en
4 vertices del loop (en cualquier orden). Se creara un bloque.

### 4. Ajustar distribuciones

En el panel Distribuciones, pulsa Refrescar aristas y edita cada
arista:

- Nodos: numero total incluyendo los extremos.
- Distribucion: uniforme o sesgada con un parametro bias.

Pulsa Aplicar. Si dos bloques comparten una arista, ambos
comparten esta configuracion automaticamente.

### 5. Validar bloques

El panel Bloques muestra si cada bloque tiene los lados opuestos
con el mismo numero de nodos:

- `OK (nodos N x M)`
- `DESAJUSTE lados 0/2: A vs B`

### 6. Generar malla

Pulsa Generar malla. La rejilla aparece sobre los bloques. La barra
de estado indica bloques y celdas.

### 7. Guardar y exportar

- Archivo > Guardar: guarda topologia, distribuciones y bloques en JSON.
- Archivo > Exportar malla (VTK): genera un .pvd y una carpeta
  <nombre>_blocks/ con un .vts por bloque. Abre el .pvd en ParaView.
