import heapq
import requests
import duckdb
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
import json
import time
import sys
import os
from datetime import datetime


class Tee:
    def __init__(self, file):
        self.file = file
        self.stdout = sys.stdout

    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)

    def flush(self):
        self.stdout.flush()
        self.file.flush()


 

def split_smiles_set(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(".") if x.strip()]

def default_step_score(row: Dict[str, Any], reactants: List[str]) -> float:
    score = 0.0

    y = row.get("yield_pct")
    t = row.get("temperature_c")
    safety = row.get("notes_safety")

    score -= 0.6 * max(0, len(reactants) - 2)

    if y is not None:
        try:
            score += 0.03 * float(y)
        except Exception:
            pass

    if t is not None:
        try:
            score -= 0.01 * max(0.0, float(t) - 25.0)
        except Exception:
            pass

    if safety and str(safety).strip():
        score -= 0.5

    return score

@dataclass
class Step:
    reaction_id: str
    product_smiles: str
    reactants: List[str]
    source: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    yield_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    pressure_atm: Optional[float] = None
    stirring_rpm: Optional[float] = None
    reagent_smiles: Optional[str] = None
    solvent_smiles: Optional[str] = None
    catalyst_smiles: Optional[str] = None
    doi: Optional[str] = None
    publication_year: Optional[int] = None
    notes_safety: Optional[str] = None
    notes_procedure: Optional[str] = None
    step_score: float = 0.0

@dataclass
class Route:
    target_smiles: str
    steps: List[Step] = field(default_factory=list)
    open_molecules: List[str] = field(default_factory=list)
    score: float = 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        if not self.steps:
            return {
                "num_steps": 0,
                "avg_yield": 0.0,
                "avg_temp": 0.0,
                "has_safety_concerns": False,
                "num_reactants": 0,
                "complete": len(self.open_molecules) == 0
            }
        
        yields = [s.yield_pct for s in self.steps if s.yield_pct is not None]
        temps = [s.temperature_c for s in self.steps if s.temperature_c is not None]
        safety_issues = any(s.notes_safety and str(s.notes_safety).strip() for s in self.steps)
        total_reactants = sum(len(s.reactants) for s in self.steps)
        
        return {
            "num_steps": len(self.steps),
            "avg_yield": sum(yields) / len(yields) if yields else 0.0,
            "avg_temp": sum(temps) / len(temps) if temps else 0.0,
            "has_safety_concerns": safety_issues,
            "num_reactants": total_reactants,
            "complete": len(self.open_molecules) == 0,
            "yields_available": len(yields),
            "temps_available": len(temps)
        }

@dataclass
class SearchStats:
    target_smiles: str
    max_depth: int
    beam_width: int
    per_node_limit: int
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    nodes_explored: int = 0
    reactions_queried: int = 0
    routes_generated: int = 0
    
    def finish(self):
        self.end_time = time.time()
    
    def runtime_seconds(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_smiles": self.target_smiles,
            "max_depth": self.max_depth,
            "beam_width": self.beam_width,
            "per_node_limit": self.per_node_limit,
            "runtime_seconds": self.runtime_seconds(),
            "nodes_explored": self.nodes_explored,
            "reactions_queried": self.reactions_queried,
            "routes_generated": self.routes_generated,
            "avg_reactions_per_node": self.reactions_queried / max(1, self.nodes_explored)
        }

@dataclass
class AStarSearchStats:
    target_smiles: str
    max_depth: int
    max_nodes: int
    per_node_limit: int
    heuristic_weight: float
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    nodes_explored: int = 0
    reactions_queried: int = 0
    routes_generated: int = 0
    states_pruned: int = 0

    def finish(self):
        self.end_time = time.time()

    def runtime_seconds(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_smiles": self.target_smiles,
            "max_depth": self.max_depth,
            "max_nodes": self.max_nodes,
            "per_node_limit": self.per_node_limit,
            "heuristic_weight": self.heuristic_weight,
            "runtime_seconds": self.runtime_seconds(),
            "nodes_explored": self.nodes_explored,
            "reactions_queried": self.reactions_queried,
            "routes_generated": self.routes_generated,
            "states_pruned": self.states_pruned,
            "avg_reactions_per_node": self.reactions_queried / max(1, self.nodes_explored),
        }


class OrdRetroSynth:
    def __init__(self, duckdb_path: str = "retrosynthesis.duckdb"):
        self.con = duckdb.connect(duckdb_path, read_only=True)
        self.stats: Optional[SearchStats] = None

    def candidates_for_product(self, product_smiles: str, limit: int = 200) -> List[Dict[str, Any]]:
        q = """
        SELECT
          reaction_id,
          source,
          dataset_id,
          dataset_name,
          product_smiles,
          reactants,
          reagent_smiles,
          solvent_smiles,
          catalyst_smiles,
          yield_pct,
          temperature_c,
          pressure_atm,
          stirring_rpm,
          doi,
          publication_year,
          notes_safety,
          notes_procedure
        FROM retro_edges
        WHERE product_smiles = ?
          AND reactants IS NOT NULL
          AND len(reactants) > 0
        LIMIT ?;
        """
        if self.stats:
            self.stats.reactions_queried += 1
        return self.con.execute(q, [product_smiles, limit]).fetchdf().to_dict("records")

    def build_routes(
        self,
        target_smiles: str,
        max_depth: int = 4,
        beam_width: int = 25,
        per_node_limit: int = 200,
        require_exactly_2_reactants: bool = False,
        stop_if_in_stock: Optional[set] = None,
        scorer=default_step_score,
    ) -> List[Route]:
        beam: List[Route] = [
            Route(target_smiles=target_smiles, steps=[], open_molecules=[target_smiles], score=0.0)
        ]

        for _depth in range(max_depth):
            new_candidates: List[Route] = []

            for route in beam:
                if not route.open_molecules:
                    new_candidates.append(route)
                    continue

                
                if stop_if_in_stock is not None and all(m in stop_if_in_stock for m in route.open_molecules):
                    new_candidates.append(route)
                    continue

                product = route.open_molecules[0]
                remaining = route.open_molecules[1:]

                rows = self.candidates_for_product(product, limit=per_node_limit)
                if self.stats:
                    self.stats.nodes_explored += 1
                
                if not rows:
                    new_candidates.append(route)
                    continue

                for row in rows:
                    reactants = row.get("reactants", [])
                    if isinstance(reactants, str):
                        reactants = split_smiles_set(reactants)
                    elif not isinstance(reactants, list):
                        reactants = list(reactants) if hasattr(reactants, '__iter__') else []

                    if not reactants:
                        continue
                    if require_exactly_2_reactants and len(reactants) != 2:
                        continue

                    step_sc = scorer(row, reactants)

                    step = Step(
                        reaction_id=row["reaction_id"],
                        product_smiles=product,
                        reactants=reactants,
                        source=row.get("source"),
                        dataset_id=row.get("dataset_id"),
                        dataset_name=row.get("dataset_name"),
                        yield_pct=row.get("yield_pct"),
                        temperature_c=row.get("temperature_c"),
                        pressure_atm=row.get("pressure_atm"),
                        stirring_rpm=row.get("stirring_rpm"),
                        reagent_smiles=row.get("reagent_smiles"),
                        solvent_smiles=row.get("solvent_smiles"),
                        catalyst_smiles=row.get("catalyst_smiles"),
                        doi=row.get("doi"),
                        publication_year=row.get("publication_year"),
                        notes_safety=row.get("notes_safety"),
                        notes_procedure=row.get("notes_procedure"),
                        step_score=step_sc,
                    )
                    
                    if self.stats:
                        self.stats.routes_generated += 1

                    new_route = Route(
                        target_smiles=route.target_smiles,
                        steps=route.steps + [step],
                        open_molecules=remaining + reactants,
                        score=route.score + step_sc,
                    )
                    new_candidates.append(new_route)

            new_candidates.sort(key=lambda r: r.score, reverse=True)
            beam = new_candidates[:beam_width]

        if self.stats:
            self.stats.finish()
        
        return beam
    
    def select_best_route(self, routes: List[Route]) -> Tuple[Route, Dict[str, Any]]:
        """Select the best route based on multiple criteria and return selection reasoning"""
        if not routes:
            return None, {"error": "No routes available"}
        
        criteria_scores = []
        
        for route in routes:
            metrics = route.get_metrics()
            
            criteria = {
                "route_index": len(criteria_scores),
                "base_score": route.score,
                "num_steps": metrics["num_steps"],
                "avg_yield": metrics["avg_yield"],
                "avg_temp": metrics["avg_temp"],
                "has_safety_concerns": metrics["has_safety_concerns"],
                "num_reactants": metrics["num_reactants"],
                "is_complete": metrics["complete"],
                "yields_available": metrics.get("yields_available", 0),
                "temps_available": metrics.get("temps_available", 0)
            }
            
            final_score = route.score
            
            if metrics["complete"]:
                final_score += 5.0
            
            if metrics["avg_yield"] > 70:
                final_score += 2.0
            elif metrics["avg_yield"] > 50:
                final_score += 1.0
            
            if metrics["num_steps"] <= 3:
                final_score += 1.5
            elif metrics["num_steps"] <= 5:
                final_score += 0.5
            
            if not metrics["has_safety_concerns"]:
                final_score += 1.0
            
            criteria["final_score"] = final_score
            criteria_scores.append(criteria)
        
        best_idx = max(range(len(criteria_scores)), key=lambda i: criteria_scores[i]["final_score"])
        best_route = routes[best_idx]
        
        selection_reasoning = {
            "best_route_index": best_idx,
            "total_routes_evaluated": len(routes),
            "best_route_criteria": criteria_scores[best_idx],
            "all_route_scores": criteria_scores,
            "selection_factors": [
                "Base score from step-level scoring",
                "Route completion bonus (+5.0 if complete)",
                "High yield bonus (+2.0 if avg >70%, +1.0 if >50%)",
                "Step efficiency bonus (+1.5 if ≤3 steps, +0.5 if ≤5 steps)",
                "Safety bonus (+1.0 if no safety concerns)"
            ]
        }
        
        return best_route, selection_reasoning

class AStarRetroSynth(OrdRetroSynth):
    """A* retrosynthesis search """

    def __init__(self, duckdb_path: str = "retrosynthesis.duckdb"):
        super().__init__(duckdb_path)
        self.astar_stats: Optional[AStarSearchStats] = None

    def build_routes_astar(
        self,
        target_smiles: str,
        max_depth: int = 4,
        max_nodes: int = 500,
        per_node_limit: int = 200,
        top_k: int = 5,
        heuristic_weight: float = 0.5,
        require_exactly_2_reactants: bool = False,
        stop_if_in_stock: Optional[set] = None,
        scorer=default_step_score,
    ) -> List[Route]:
        self.astar_stats = AStarSearchStats(
            target_smiles=target_smiles,
            max_depth=max_depth,
            max_nodes=max_nodes,
            per_node_limit=per_node_limit,
            heuristic_weight=heuristic_weight,
        )
        # Route candidates_for_product (inherited) through self.stats so reactions_queried is tracked
        self.stats = self.astar_stats

        def _priority(route: Route) -> float:
            # min-heap: negate because we want to maximise (score - penalty for open mols)
            return -(route.score - heuristic_weight * len(route.open_molecules))

        initial = Route(
            target_smiles=target_smiles,
            steps=[],
            open_molecules=[target_smiles],
            score=0.0,
        )

        counter = 0
        heap: List[Tuple] = [(_priority(initial), counter, initial)]

        visited: Dict[frozenset, float] = {}

        complete_routes: List[Route] = []
        partial_routes: List[Route] = []

        while heap and self.astar_stats.nodes_explored < max_nodes:
            _, _, current = heapq.heappop(heap)

            if not current.open_molecules:
                complete_routes.append(current)
                if len(complete_routes) >= top_k:
                    break
                continue

            if len(current.steps) >= max_depth:
                if current.steps:
                    partial_routes.append(current)
                continue

            state_key = frozenset(current.open_molecules)
            if state_key in visited and visited[state_key] >= current.score:
                self.astar_stats.states_pruned += 1
                continue
            visited[state_key] = current.score

            self.astar_stats.nodes_explored += 1

            if stop_if_in_stock is not None and all(
                m in stop_if_in_stock for m in current.open_molecules
            ):
                complete_routes.append(current)
                continue

            product = current.open_molecules[0]
            remaining = current.open_molecules[1:]

            rows = self.candidates_for_product(product, limit=per_node_limit)
            if not rows:
                if current.steps:
                    partial_routes.append(current)
                continue

            for row in rows:
                reactants = row.get("reactants", [])
                if isinstance(reactants, str):
                    reactants = split_smiles_set(reactants)
                elif not isinstance(reactants, list):
                    reactants = list(reactants) if hasattr(reactants, "__iter__") else []

                if not reactants:
                    continue
                if require_exactly_2_reactants and len(reactants) != 2:
                    continue

                step_sc = scorer(row, reactants)

                step = Step(
                    reaction_id=row["reaction_id"],
                    product_smiles=product,
                    reactants=reactants,
                    source=row.get("source"),
                    dataset_id=row.get("dataset_id"),
                    dataset_name=row.get("dataset_name"),
                    yield_pct=row.get("yield_pct"),
                    temperature_c=row.get("temperature_c"),
                    pressure_atm=row.get("pressure_atm"),
                    stirring_rpm=row.get("stirring_rpm"),
                    reagent_smiles=row.get("reagent_smiles"),
                    solvent_smiles=row.get("solvent_smiles"),
                    catalyst_smiles=row.get("catalyst_smiles"),
                    doi=row.get("doi"),
                    publication_year=row.get("publication_year"),
                    notes_safety=row.get("notes_safety"),
                    notes_procedure=row.get("notes_procedure"),
                    step_score=step_sc,
                )

                new_route = Route(
                    target_smiles=current.target_smiles,
                    steps=current.steps + [step],
                    open_molecules=remaining + reactants,
                    score=current.score + step_sc,
                )
                counter += 1
                heapq.heappush(heap, (_priority(new_route), counter, new_route))
                self.astar_stats.routes_generated += 1

        self.astar_stats.finish()

        result = list(complete_routes)
        if len(result) < top_k:
            partial_routes.sort(key=lambda r: r.score, reverse=True)
            result += partial_routes[: top_k - len(result)]
        if len(result) < top_k:
            heap_routes = sorted(
                [item[2] for item in heap if item[2].steps],
                key=lambda r: r.score,
                reverse=True,
            )
            result += heap_routes[: top_k - len(result)]

        return result[:top_k]


def routes_to_pretty_json(routes: List[Route], top_k: int = 5) -> str:
    def r_to_dict(r: Route) -> Dict[str, Any]:
        metrics = r.get_metrics()
        return {
            "target_smiles": r.target_smiles,
            "score": r.score,
            "metrics": metrics,
            "open_molecules": r.open_molecules,
            "steps": [asdict(s) for s in r.steps],
        }
    return json.dumps([r_to_dict(r) for r in routes[:top_k]], indent=2)

def print_route_summary(route: Route, route_num: int = 1):
    metrics = route.get_metrics()
    print(f"{'==========='}")
    print(f"Route #{route_num} Summary")
    print(f"{'==========='}")
    print(f"Target: {route.target_smiles}")
    print(f"Score: {route.score:.2f}")
    print(f"Number of steps: {metrics['num_steps']}")
    print(f"Complete route: {'Yes' if metrics['complete'] else 'No'}")
    print(f"Remaining molecules: {len(route.open_molecules)}")
    
    # if metrics['avg_yield'] > 0:
    #     print(f"Average yield: {metrics['avg_yield']:.1f}% ({metrics['yields_available']}/{metrics['num_steps']} steps with yield data)")
    # else:
    #     print(f"Average yield: N/A")
    
    # if metrics['avg_temp'] > 0:
    #     print(f"Average temperature: {metrics['avg_temp']:.1f}°C ({metrics['temps_available']}/{metrics['num_steps']} steps with temp data)")
    # else:
    #     print(f"Average temperature: N/A")
    
    # print(f"Safety concerns: {'Yes' if metrics['has_safety_concerns'] else 'No'}")
    # print(f"Total reactants: {metrics['num_reactants']}")
    
    print(f"Steps:")
    for i, step in enumerate(route.steps, 1):
        print(f"  Step {i}: {step.product_smiles}")
        print(f"Reaction ID: {step.reaction_id}")
        print(f"Source: {step.source or 'N/A'}")
        print(f"Reactants ({len(step.reactants)}): {', '.join(step.reactants[:3])}{'...' if len(step.reactants) > 3 else ''}")
        if step.yield_pct:
            print(f"Yield: {step.yield_pct:.1f}%")
        if step.temperature_c:
            print(f"Temperature: {step.temperature_c:.1f}°C")
        if step.solvent_smiles:
            print(f"Solvent: {step.solvent_smiles}")
        if step.catalyst_smiles:
            print(f"Catalyst: {step.catalyst_smiles}")
        if step.notes_safety:
            print(f"Safety: {step.notes_safety[:100]}...")
        print(f"Step score: {step.step_score:.2f}")
    
    if route.open_molecules:
        print(f"Open molecules (need synthesis): {', '.join(route.open_molecules[:5])}{'...' if len(route.open_molecules) > 5 else ''}")
    print(f"{'==========='}")

def get_smiles(name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/CanonicalSMILES/JSON"
    r = requests.get(url)
    data = r.json()
    return data["PropertyTable"]["Properties"][0]["CanonicalSMILES"]

def run_targets(
    targets: Dict[str, str],
    duckdb_path: str = "retrosynthesis.duckdb",
    max_depth: int = 4,
    beam_width: int = 25,
    per_node_limit: int = 200,
) -> List[Dict[str, Any]]:
    retro = OrdRetroSynth(duckdb_path=duckdb_path)
    results = []

    for name, smi in targets.items():
        print(f"{'###########'}")
        print(f"    Target: {name}")
        print(f"    SMILES: {smi}")
        print(f"{'###########'}\n")

        retro.stats = SearchStats(
            target_smiles=smi,
            max_depth=max_depth,
            beam_width=beam_width,
            per_node_limit=per_node_limit,
        )

        try:
            routes = retro.build_routes(
                target_smiles=smi,
                max_depth=max_depth,
                beam_width=beam_width,
                per_node_limit=per_node_limit,
                require_exactly_2_reactants=False,
            )
        except RuntimeError as e:
            if "Query interrupted" in str(e):
                raise KeyboardInterrupt() from e
            raise

        routes = [r for r in routes if r.steps]

        print(f"Found {len(routes)} routes for {name}\n")

        best_route, reasoning = None, {}
        if routes:
            best_route, reasoning = retro.select_best_route(routes)

            print(f"{'***********'}")
            print(f"BEST ROUTE SELECTION")
            print(f"{'***********'}")
            print(f"Selected route: #{reasoning['best_route_index'] + 1} out of {reasoning['total_routes_evaluated']}")
            print(f"Selection criteria used:")
            for factor in reasoning['selection_factors']:
                print(f"  - {factor}")

            print(f"Best route metrics:")
            for key, value in reasoning['best_route_criteria'].items():
                if key != 'route_index':
                    print(f"  {key}: {value}")

            print_route_summary(best_route, route_num=reasoning['best_route_index'] + 1)

            print(f"{'==========='}")
            print(f"ALL ROUTES COMPARISON")
            print(f"{'==========='}")
            for i, route_criteria in enumerate(reasoning['all_route_scores'][:5], 1):
                print(f"Route #{i}:")
                print(f"  Final score: {route_criteria['final_score']:.2f}")
                print(f"  Base score: {route_criteria['base_score']:.2f}")
                print(f"  Steps: {route_criteria['num_steps']}")
                print(f"  Avg yield: {route_criteria['avg_yield']:.1f}%")
                print(f"  Complete: {route_criteria['is_complete']}")
                print(f"  Safety concerns: {route_criteria['has_safety_concerns']}")

            print(f"{'==========='}")
            print(f"TOP 3 ROUTES (JSON)")
            print(f"{'==========='}")
            print(routes_to_pretty_json(routes, top_k=3))
        else:
            print(f"No routes found for {name}")

        results.append({
            "name": name,
            "smiles": smi,
            "routes": routes,
            "best_route": best_route,
            "reasoning": reasoning,
            "stats": retro.stats.to_dict(),
        })

    return results


if __name__ == "__main__":
    eval_dir = os.path.join(os.path.dirname(__file__), "eval_results")
    os.makedirs(eval_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(eval_dir, f"retrosynth_{timestamp}.txt")

    log_file = open(log_path, "w")
    sys.stdout = Tee(log_file)

    print(f"{'==========='}")
    print(f"Retrosynthesis Analysis")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output file: {log_path}")

    # curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Orforglipron/property/CanonicalSMILES/JSON"
    # curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Etoricoxib/property/CanonicalSMILES/JSON"
    # curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Camlipixant/property/CanonicalSMILES/JSON"
    # Molecule with verified 2-step pathway in the ORD database
    TARGETS = {
        "Fluorinated_Imidazole": "N#CC1=C(C2=CC=CC=C2F)N(C)C=N1",
        "Methoxy_Diphenylamine": "COc1ccc(Nc2ccc(C)cc2)cc1",
        "Tolyl_Pyridine": "Cc1ccc(Nc2cccnc2)cc1",
    }

    MAX_DEPTH = 4
    BEAM_WIDTH = 25
    PER_NODE_LIMIT = 200

    results = run_targets(
        targets=TARGETS,
        duckdb_path="retrosynthesis.duckdb",
        max_depth=MAX_DEPTH,
        beam_width=BEAM_WIDTH,
        per_node_limit=PER_NODE_LIMIT,
    )

    all_stats = [r["stats"] for r in results]
    for r in results:
        all_stats[results.index(r)]["target_name"] = r["name"]

    print(f"\n{'==========='}")
    print(f"RUN STATISTICS SUMMARY")
    print(f"{'==========='}")
    print(f"Configuration:")
    print(f"  Max depth: {MAX_DEPTH}")
    print(f"  Beam width: {BEAM_WIDTH}")
    print(f"  Per-node limit: {PER_NODE_LIMIT}")
    print(f"Per-target statistics:")

    for stat in all_stats:
        print(f"  {stat['target_name']}:")
        print(f"    Runtime: {stat['runtime_seconds']:.2f} seconds")
        print(f"    Nodes explored: {stat['nodes_explored']}")
        print(f"    Reactions queried: {stat['reactions_queried']}")
        print(f"    Routes generated: {stat['routes_generated']}")
        print(f"    Avg reactions/node: {stat['avg_reactions_per_node']:.1f}")

    total_runtime = sum(s['runtime_seconds'] for s in all_stats)
    total_nodes = sum(s['nodes_explored'] for s in all_stats)
    total_routes = sum(s['routes_generated'] for s in all_stats)

    print(f"Overall totals:")
    print(f"  Total runtime: {total_runtime:.2f} seconds")
    print(f"  Total nodes explored: {total_nodes}")
    print(f"  Total routes generated: {total_routes}")
    print(f"  Avg runtime per target: {total_runtime/len(all_stats):.2f} seconds")

    print(f"{'==========='}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Total runtime: {total_runtime:.2f}s)")
    print(f"{'==========='}\n")

    print(f"TIP: Adjust MAX_DEPTH to explore deeper/shallower routes")
    print(f" Current depth: {MAX_DEPTH}")

    sys.stdout = sys.stdout.stdout
    log_file.close()
    print(f"Results saved to: {log_path}")