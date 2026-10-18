"""Transfinite interpolation (TFI) for a quadrilateral."""

from __future__ import annotations

from typing import List, Sequence

from meshcad.core.geometry.point import Point2D


def tfi_grid(
    south: Sequence[Point2D],
    east: Sequence[Point2D],
    north: Sequence[Point2D],
    west: Sequence[Point2D],
) -> List[List[Point2D]]:
    """Genera a rejilla estructurada por interpolacion transfinita.

    Convenio de corners y sentidos (siempre segun el recorrido del loop):
        south: c0 -> c1 (N_u puntos). Es el lado 0 del bloque.
        east:  c1 -> c2 (N_v puntos). Es el lado 1 del bloque.
        north: c2 -> c3 (N_u puntos). Es el lado 2 del bloque.
        west:  c3 -> c0 (N_v puntos). Es el lado 3 del bloque.

    Devuelve grid[j][i] with j en [0, N_v), i en [0, N_u).
    grid[0][0] = c0, grid[0][N_u-1] = c1,
    grid[N_v-1][N_u-1] = c2, grid[N_v-1][0] = c3.
    """
    n_u = len(south)
    n_v = len(east)

    if len(north) != n_u:
        raise ValueError(
            "Sides 0 and 2 must have the same node count: {} vs {}".format(
                n_u, len(north)
            )
        )
    if len(west) != n_v:
        raise ValueError(
            "Sides 1 and 3 must have the same node count: {} vs {}".format(
                n_v, len(west)
            )
        )
    if n_u < 2 or n_v < 2:
        raise ValueError("Each side requires at least two nodes")

    # Esquinas
    c0 = south[0]
    c1 = south[-1]
    c2 = north[0]
    c3 = north[-1]

    # Reordenamos los lados 2 y 3 for que vayan en el sentido del grid:
    # north must ir c3 -> c2 (o sea, recorrer el lado 2 in reverse),
    # west must ir c0 -> c3 (recorrer el lado 3 in reverse).
    north_rev = list(reversed(north))
    west_rev = list(reversed(west))

    grid: List[List[Point2D]] = []
    for j in range(n_v):
        v = j / (n_v - 1)
        row: List[Point2D] = []
        for i in range(n_u):
            u = i / (n_u - 1)

            s = south[i]
            n = north_rev[i]  # norte en (u, 1)
            w = west_rev[j]   # oeste en (0, v)
            e = east[j]       # este en (1, v)

            # Correccion bilineal en las corners
            bx = (
                (1.0 - u) * (1.0 - v) * c0.x
                + u * (1.0 - v) * c1.x
                + u * v * c2.x
                + (1.0 - u) * v * c3.x
            )
            by = (
                (1.0 - u) * (1.0 - v) * c0.y
                + u * (1.0 - v) * c1.y
                + u * v * c2.y
                + (1.0 - u) * v * c3.y
            )

            x = (
                (1.0 - v) * s.x
                + v * n.x
                + (1.0 - u) * w.x
                + u * e.x
                - bx
            )
            y = (
                (1.0 - v) * s.y
                + v * n.y
                + (1.0 - u) * w.y
                + u * e.y
                - by
            )
            row.append(Point2D(x, y))
        grid.append(row)
    return grid
