from typing import List, Dict, Set, Tuple, Any
from pydantic import BaseModel, Field

class Movement(BaseModel):
    approach_id: str
    direction: str  # "through", "left", "right"

    @property
    def key(self) -> str:
        return f"{self.approach_id}_{self.direction}"

class PhaseGroup(BaseModel):
    phase_id: int
    name: str
    movements: List[str]  # e.g. ["north_through", "south_through"]

class JunctionTopology:
    """
    Computes movement compatibility and phase conflict matrices for 2-way through 8-way junctions.
    """
    def __init__(self, approach_ids: List[str], movements_per_approach: Dict[str, List[str]]):
        self.approach_ids = approach_ids
        self.movements_per_approach = movements_per_approach
        self.num_approaches = len(approach_ids)

    def are_movements_compatible(self, m1: Tuple[str, str], m2: Tuple[str, str]) -> bool:
        """
        Determines if two movements (app_id, dir) are non-conflicting (compatible).
        Rules:
        - Same approach movements: compatible if different directions or right-turn filter.
        - Opposing approach 'through' movements: compatible.
        - Adjacent approach 'through' movements: CONFLICTING.
        - Left turns: generally compatible with non-crossing through traffic.
        """
        app1, dir1 = m1
        app2, dir2 = m2

        if app1 == app2:
            return True  # Same approach can serve multiple lanes together

        idx1 = self.approach_ids.index(app1) if app1 in self.approach_ids else -1
        idx2 = self.approach_ids.index(app2) if app2 in self.approach_ids else -1

        if idx1 == -1 or idx2 == -1:
            return False

        opposing_pairs = {
            ("north", "south"), ("south", "north"),
            ("east", "west"), ("west", "east"),
            ("northeast", "southwest"), ("southwest", "northeast"),
            ("northwest", "southeast"), ("southeast", "northwest")
        }
        name1, name2 = app1.lower(), app2.lower()
        directional_names = {"north", "south", "east", "west", "northeast", "southwest", "northwest", "southeast"}
        if name1 in directional_names and name2 in directional_names:
            is_opposing = (name1, name2) in opposing_pairs
        else:
            is_opposing = (abs(idx1 - idx2) == (self.num_approaches // 2))

        if is_opposing:
            # Opposing through movements are compatible
            if dir1 == "through" and dir2 == "through":
                return True
            # Opposing left turns are compatible
            if dir1 == "left" and dir2 == "left":
                return True
            # Left turn + opposing through (if right-side traffic standard rules)
            if (dir1 == "through" and dir2 == "right") or (dir1 == "right" and dir2 == "through"):
                return True

        # Right turns typically conflict with through traffic unless separate protected phase
        if (dir1 == "through" and dir2 == "through") and not is_opposing:
            return False

        # Default compatibility for same phase group if non-crossing
        return is_opposing or dir1 == "left" or dir2 == "left"

    def build_phases(self) -> List[PhaseGroup]:
        """
        Auto-derives maximal non-conflicting phase groups.
        """
        all_movements: List[Tuple[str, str]] = []
        for app in self.approach_ids:
            for d in self.movements_per_approach.get(app, ["through"]):
                all_movements.append((app, d))

        phase_groups: List[PhaseGroup] = []
        visited_movements: Set[str] = set()
        phase_idx = 1

        # Strategy 1: Pair opposing 'through' movements into main arterial phases
        for i, m1 in enumerate(all_movements):
            m1_key = f"{m1[0]}_{m1[1]}"
            if m1_key in visited_movements:
                continue

            current_group = [m1_key]
            visited_movements.add(m1_key)

            for j, m2 in enumerate(all_movements):
                if i == j:
                    continue
                m2_key = f"{m2[0]}_{m2[1]}"
                if m2_key in visited_movements:
                    continue

                if self.are_movements_compatible(m1, m2):
                    current_group.append(m2_key)
                    visited_movements.add(m2_key)

            phase_groups.append(
                PhaseGroup(
                    phase_id=phase_idx,
                    name=f"Phase {phase_idx} ({' + '.join(current_group)})",
                    movements=current_group
                )
            )
            phase_idx += 1

        # Ensure every movement is assigned to at least one phase
        for m in all_movements:
            m_key = f"{m[0]}_{m[1]}"
            if not any(m_key in pg.movements for pg in phase_groups):
                phase_groups.append(
                    PhaseGroup(
                        phase_id=phase_idx,
                        name=f"Phase {phase_idx} ({m_key})",
                        movements=[m_key]
                    )
                )
                phase_idx += 1

        return phase_groups
