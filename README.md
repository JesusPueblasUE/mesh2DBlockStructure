# MeshCAD

Mallador 2D estructurado por bloques con un pequeno CAD integrado.

- Version: 0.0.1
- Python: >= 3.9
- GUI: PyQt5

## Estado

Fase 0 completada: estructura del proyecto, entorno y ventana minima.

## Estructura

    src/meshcad/
      core/
        geometry/
        topology/
        mesh/
      gui/
        main_window.py
        canvas.py
        tools/
      io/
    tests/

## Ejecutar

    python -m meshcad

## Tests

    pytest

## Roadmap

- [x] Fase 0: preparacion del proyecto
- [ ] Fase 1: nucleo geometrico 2D
- [ ] Fase 2: topologia CAD
- [ ] Fase 3: GUI CAD basica
- [ ] Fase 4: bloques estructurados de 4 lados
- [ ] Fase 5: distribuciones de nodos
- [ ] Fase 6: generacion de malla estructurada
- [ ] Fase 7: persistencia y exportacion
- [ ] Fase 8: refactor, docs y empaquetado
