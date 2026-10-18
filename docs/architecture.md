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

Dependency Rules:

- `core` **no** importa PyQt5 ni `gui` ni `io`.
- `gui` can importar `core` e `io`. Es la single capa que conoce Qt.
- `io` can importar `core`. **No** importa `gui`. Trabaja with `dict`.

## Paquetes

- `meshcad.core.geometry`
  - `Point2D`, `Vector2D`
  - `GeometryEntity` (interfaz)
  - `Line`, `Arc`, `Spline`
  - `evaluate(t) -> Point2D` normaliza el parametro a [0, 1].

- `meshcad.core.topology`
  - `Vertex`, `Edge`, `OrientedEdge`: IDs unicos inside de a `Topology`.
  - `Topology`: contenedor with asignacion monotona de IDs.
  - `Loop`: contorno cerrado. Guarda referencias por id, no copias.
  - `BlockSide`: lado de un bloque (a o varias edges).
  - `Block`: bloque estructurado de 4 lados.
  - `loop_detector`: deteccion automatica de loops simples.

- `meshcad.core.mesh`
  - `NodeDistribution`, `UniformDistribution`, `BiasedDistribution`.
  - `EdgeMeshSpec`: (edge_id, n_nodes, distribution).
  - `MeshModel`: mapa edge_id -> spec. Una spec por edge.
  - `tfi_grid`: interpolacion transfinita for un cuadrilatero.
  - `mesh_block`: Block + MeshModel + Topology -> BlockMesh.

- `meshcad.gui`
  - `Document`: estado del proyecto + undo stack + to_dict/from_dict.
  - `CadCanvas`: QGraphicsView with preview, snapping, highlights.
  - `tools/`: LineTool, ArcTool, SplineTool, CornerPickerTool.
  - `panels`: LoopsPanel, EdgesPanel, BlocksPanel.

- `meshcad.io`
  - `json_io`: serializacion pura de entidades de `core`.
  - `project_io`: save/load dict en disco (without Qt).
  - `vtk_io`: exportacion a PVD + VTS for ParaView.

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
        (specs por edge)            |
                                      v
                                 BlockMesh (grid)
                                      |
                                      v
                           Canvas / VTK export

## Decisiones de diseno clave

1. **Aristas compartidas por ID**: dos loops que usen la misma edge
   comparten automaticamente su distribucion de nodes. Esto garantiza
   conformidad entre blocks adyacentes without promediar ni interpolar.

2. **OrientedEdge**: la edge tiene a direccion natural. Si un loop
   la recorre in reverse, se marca `reversed=True`. Nunca se duplica.

3. **evaluate(t)**: all las geometrias exponen un parametro
   normalizado. Las distribuciones producen valores de t, no puntos.

4. **TFI with verificacion de fronteras**: los lados 0/2 y 1/3 se
   muestrean del MeshModel. El interior se calcula por interpolacion
   transfinita. Las fronteras coinciden exactas (verificado por tests).

5. **Document.load_from(other)**: se reemplaza el contenido, no el
   objeto Document, for no romper las conexiones signal/slot.
