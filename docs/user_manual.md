# Manual de usuario

## Arranque

    python -m meshcad

## Interfaz

- Barra de herramientas: Select, Line, Arc, Spline,
  Generate Mesh, Clear Mesh.
- Menu File: New, Abrir, Save, Save As, Exportar mesh (VTK).
- Panel izquierdo Loops.
- Paneles derechos Distributions y Blocks.

## Flujo tipico

### 1. Dibujar geometry

Click Line (2 clics), Arc (3 clics: centro, inicio, fin) o
Spline (varios clics + clic derecho for terminar). Mientras mueves
el raton se ve la forma en tiempo real (linea discontinua).

Los vertices existentes se muestran como circulos rojos. Al pasar
cerca with el cursor, la geometry hace snapping.

Escape cancela la herramienta activa.

### 2. Crear un loop

En el panel Loops, pulsa Detect Loops. Se listan los contornos
cerrados. Al seleccionar uno se ilumina en verde sobre el lienzo.

### 3. Crear un bloque

Con un loop seleccionado, pulsa Create Block from Loop. Click en
4 vertices del loop (en cualquier orden). Se creara un bloque.

### 4. Ajustar distribuciones

En el panel Distributions, pulsa Refresh Edges y edita cada
edge:

- Nodes: number total incluyendo los extremos.
- Distribution: uniform o biased with un parametro bias.

Click Aplicar. Si dos blocks comparten a edge, ambos
comparten esta configuracion automaticamente.

### 5. Validar blocks

El panel Blocks muestra si cada bloque tiene los lados opuestos
with el same number de nodes:

- `OK (nodes N x M)`
- `MISMATCH lados 0/2: A vs B`

### 6. Generate Mesh

Click Generate Mesh. La rejilla aparece sobre los blocks. La barra
de estado indica blocks y cells.

### 7. Save y exportar

- File > Save: guarda topology, distribuciones y blocks en JSON.
- File > Exportar mesh (VTK): genera un .pvd y a carpeta
  <nombre>_blocks/ with un .vts por bloque. Abre el .pvd en ParaView.
