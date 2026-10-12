import math

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import BiasedDistribution, UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology
from meshcad.gui.document import Document
from meshcad.io.project_io import load_project, save_project


def build_document():
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

    doc.set_edge_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e1.id, 5, BiasedDistribution(bias=1.5)))
    doc.set_edge_spec(EdgeMeshSpec(e2.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e3.id, 5, BiasedDistribution(bias=1.5)))
    return doc


def test_save_creates_file(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    assert path.exists()
    assert "meshcad-project" in path.read_text(encoding="utf-8")


def test_round_trip_topology(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert len(back.topology.vertices()) == 4
    assert len(back.topology.edges()) == 4
    for e in doc.topology.edges():
        be = back.topology.get_edge(e.id)
        assert be.start_vertex_id == e.start_vertex_id
        assert be.end_vertex_id == e.end_vertex_id


def test_round_trip_edge_specs(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert set(back.mesh.edge_specs.keys()) == set(doc.mesh.edge_specs.keys())
    for eid, spec in doc.mesh.edge_specs.items():
        bspec = back.mesh.get_spec(eid)
        assert bspec.n_nodes == spec.n_nodes
        assert type(bspec.distribution) is type(spec.distribution)
        if isinstance(spec.distribution, BiasedDistribution):
            assert math.isclose(
                bspec.distribution.bias, spec.distribution.bias
            )


def test_round_trip_blocks(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert len(back.blocks) == 1
    assert back.blocks[0].id == 0
    assert back.blocks[0].sides[0].edge_ids() == [0]
    back.blocks[0].validate_opposite_sides()


def test_generate_mesh_after_load(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    meshes, errors = back.generate_mesh()
    assert errors == []
    assert len(meshes) == 1
    assert meshes[0].n_u == 4
    assert meshes[0].n_v == 5


def test_next_block_id_survives(tmp_path):
    doc = build_document()
    # consumimos algunos IDs
    doc.next_block_id()
    doc.next_block_id()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert back.next_block_id() >= 3


def test_load_from_replaces_state(qtbot):
    doc_a = Document()
    doc_b = build_document()
    assert len(doc_a.topology.vertices()) == 0
    with qtbot.waitSignal(doc_a.project_replaced, timeout=1000):
        doc_a.load_from(doc_b)
    assert len(doc_a.topology.vertices()) == 4
    assert len(doc_a.blocks) == 1
