import pytest
from src.junction.phase_builder import JunctionTopology

def test_phase_builder_n3_t_junction():
    app_ids = ["north", "south", "east"]
    movements = {
        "north": ["through", "left"],
        "south": ["through", "right"],
        "east": ["left", "right"]
    }
    topo = JunctionTopology(app_ids, movements)
    phases = topo.build_phases()
    assert len(phases) >= 2
    # Verify opposing N-S through movements are grouped together
    p1_movements = phases[0].movements
    assert any("north" in m for m in p1_movements)

def test_phase_builder_n4_crossroads():
    app_ids = ["north", "south", "east", "west"]
    movements = {
        "north": ["through", "left", "right"],
        "south": ["through", "left", "right"],
        "east": ["through", "left", "right"],
        "west": ["through", "left", "right"]
    }
    topo = JunctionTopology(app_ids, movements)
    phases = topo.build_phases()
    assert len(phases) >= 2
    # Verify North through and South through can run in the same phase
    assert topo.are_movements_compatible(("north", "through"), ("south", "through"))
    # Verify North through and East through conflict
    assert not topo.are_movements_compatible(("north", "through"), ("east", "through"))
