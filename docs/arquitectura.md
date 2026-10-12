# Arquitectura de MeshCAD

## Vision general

    +-----------------+     +-----------------+     +------------------+
    |   core (puro)   |<----|      gui        |<----|      io          |
    |  geometry /     |     |  canvas, tools, |     |  JSON, VTK       |
    |  topology /     |     |  panels, doc    |     |  (puro dict)     |
    |  mesh           |     |  (PyQt5)        |     |                  |
    +-----------------+     +-----------------+     +------------------+
            ^                       ^                        ^
            |                       |                        |
            +---------- no depende de Qt ---------+-----------+

Reglas de dependencia:

- `core` **no** importa PyQt5 ni `gui` ni `io`.
- `gui` puede importar `core` e `io`. Es la unica capa que conoce Qt.
- `io` puede importar `core`. **No** importa `gui`. Trabaja con `dict`.

## Paquetes

- `meshcad.core.geometry`
  - `Point2D`, `Vector2D`
  - `GeometryEntity` (interfaz)
  - `Line`, `Arc`, `Spline`
  - `evaluate(t) -> Point2D` normaliza el parametro a [0, 1].

- `meshcad.core.topology`
  - `Vertex`, `Edge`, `OrientedEdge`: IDs unicos dentro de una `Topology`.
  - `Topology`: contenedor con asignacion monotona de IDs.
  - `Loop`: contorno cerrado. Guarda referencias por id, no copias.
  - `BlockSide`: lado de un bloque (una o varias aristas).
  - `Block`: bloque estructurado de 4 lados.
  - `loop_detector`: deteccion automatica de loops simples.

- `meshcad.core.mesh`
  - `NodeDistribution`, `UniformDistribution`, `BiasedDistribution`.
  - `EdgeMeshSpec`: (edge_id, n_nodes, distribution).
  - `MeshModel`: mapa edge_id -> spec. Una spec por arista.
  - `tfi_grid`: interpolacion transfinita para un cuadrilatero.
  - `mesh_block`: Block + MeshModel + Topology -> BlockMesh.

- `meshcad.gui`
  - `Document`: estado del proyecto + undo stack + to_dict/from_dict.
  - `CadCanvas`: QGraphicsView con preview, snapping, highlights.
  - `tools/`: LineTool, ArcTool, SplineTool, CornerPickerTool.
  - `panels`: LoopsPanel, EdgesPanel, BlocksPanel.

- `meshcad.io`
  - `json_io`: serializacion pura de entidades de `core`.
  - `project_io`: guardar/cargar dict en disco (sin Qt).
  - `vtk_io`: exportacion a PVD + VTS para ParaView.

## Flujo de datos

    CAD (Line/Arc/Spline)
            |
            v
    Topology (Vertex, Edge) ---- Loop (referencias a Edge)
            |                         |
            |                         v
            |                    Block (4 BlockSide)
            |                         |
            v                         v
        MeshModel  ----------->  mesh_block
        (specs por arista)            |
                                      v
                                 BlockMesh (grid)
                                      |
                                      v
                           Canvas / VTK export

## Decisiones de diseno clave

1. **Aristas compartidas por ID**: dos loops que usen la misma arista
   comparten automaticamente su distribucion de nodos. Esto garantiza
   conformidad entre bloques adyacentes sin promediar ni interpolar.

2. **OrientedEdge**: la arista tiene una direccion natural. Si un loop
   la recorre al reves, se marca `reversed=True`. Nunca se duplica.

3. **evaluate(t)**: todas las geometrias exponen un parametro
   normalizado. Las distribuciones producen valores de t, no puntos.

4. **TFI con verificacion de fronteras**: los lados 0/2 y 1/3 se
   muestrean del MeshModel. El interior se calcula por interpolacion
   transfinita. Las fronteras coinciden exactas (verificado por tests).

5. **Document.load_from(other)**: se reemplaza el contenido, no el
   objeto Document, para no romper las conexiones signal/slot.
