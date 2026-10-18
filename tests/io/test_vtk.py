from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.gui.document import Document
from meshcad.io.vtk_io import export_mesh_vtk


def build_meshed_document(n_nodes=4):
    doc = Document()
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))
    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    doc.add_block(Block(doc.next_block_id(), sides))
    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))
    doc.generate_mesh()
    return doc


def test_export_creates_pvd_and_blocks_dir(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "mesh.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    assert pvd.exists()
    blocks_dir = tmp_path / "mesh_blocks"
    assert blocks_dir.is_dir()
    assert (blocks_dir / "block_0000.vts").exists()


def test_pvd_contains_reference(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "mesh.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    content = pvd.read_text(encoding="utf-8")
    assert "block_0000.vts" in content
    assert "Collection" in content


def test_vts_contains_structured_grid(tmp_path):
    doc = build_meshed_document(n_nodes=4)
    pvd = tmp_path / "mesh.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    vts = (tmp_path / "mesh_blocks" / "block_0000.vts").read_text(encoding="utf-8")
    assert "StructuredGrid" in vts
    assert 'WholeExtent="0 3 0 3 0 0"' in vts
    assert "Float64" in vts


def test_export_multiple_blocks(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "mesh.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    blocks_dir = tmp_path / "mesh_blocks"
    vts_files = sorted(blocks_dir.glob("*.vts"))
    assert len(vts_files) == len(doc.block_meshes)
