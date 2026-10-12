# MeshCAD

Mallador 2D estructurado por bloques con un pequeno CAD integrado.

- Version: 1.0.0
- Python: >= 3.9
- GUI: PyQt5

## Instalacion

    pip install -e .

## Uso

    python -m meshcad

Consulta `docs/manual_usuario.md` para el flujo completo.
Consulta `docs/arquitectura.md` para el diseno interno.

## Tests

    python -m pytest

## Estructura

    src/meshcad/
      core/      # geometria, topologia y malla (sin Qt)
        geometry/
        topology/
        mesh/
      gui/       # PyQt5
        tools/
      io/        # JSON y VTK (sin Qt)
    docs/
    tests/

## Reglas de dependencia

- `core` no depende de PyQt5 ni de `gui` ni de `io`.
- `gui` puede importar `core` e `io`.
- `io` puede importar `core` y trabaja con `dict` (sin Qt).

## Roadmap

- [x] Fase 0: estructura del proyecto
- [x] Fase 1: nucleo geometrico 2D
- [x] Fase 2: topologia CAD
- [x] Fase 3: GUI CAD con vista previa en tiempo real
- [x] Fase 4: bloques estructurados de 4 lados
- [x] Fase 5: distribuciones de nodos
- [x] Fase 6: generacion de malla estructurada (TFI)
- [x] Fase 7: persistencia JSON y exportacion VTK
- [x] Fase 8: consolidacion, docs, CI y empaquetado

## Licencia

MIT
