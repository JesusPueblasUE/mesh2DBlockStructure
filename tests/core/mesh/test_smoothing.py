import math
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.smoothing import SmoothingOptions, enforce_boundary_orthogonality, elliptic_smooth, improve_grid

def grid(n=7):
    return [[Point2D(i/(n-1)+.12*math.sin(math.pi*j/(n-1))*math.sin(math.pi*i/(n-1)),j/(n-1)) for i in range(n)] for j in range(n)]
def boundary(g): return g[0]+g[-1]+[r[0] for r in g]+[r[-1] for r in g]
def test_boundary_fixed():
    g=grid(); o=improve_grid(g,SmoothingOptions(True,2,20,.4,1.0)); assert boundary(o)==boundary(g)
def test_orthogonal():
    g=grid(); o=enforce_boundary_orthogonality(g,1,1.0); assert abs(o[1][3].x-o[0][3].x)<1e-12
def test_smoothing_reduces_defect():
    g=grid(); c=3
    def d(a):
        p=a[c][c]; n=(a[c][c-1],a[c][c+1],a[c-1][c],a[c+1][c]); return math.hypot(p.x-sum(q.x for q in n)/4,p.y-sum(q.y for q in n)/4)
    assert d(elliptic_smooth(g,20,.45)) < d(g)
