
import argparse
import duckdb
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from retrosynth import (
    Tee,
    run_targets,
)


EVAL_TABLE = "eval_smiles"


def _table_exists(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    rows = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [name],
    ).fetchone()
    return rows[0] > 0


def build_eval_smiles_table(
    con: duckdb.DuckDBPyConnection,
    n_pubchem: int = 100,
    n_reactions: int = 100,
    rebuild: bool = False,
) -> int:

    if _table_exists(con, EVAL_TABLE) and not rebuild:
        n = con.execute(f"SELECT COUNT(*) FROM {EVAL_TABLE}").fetchone()[0]
        print(f"[eval_smiles] Table already exists with {n:,} rows. "
              f"Use --rebuild to regenerate.")
        return n

    print(f"[eval_smiles] Building table "
          f"(pubchem={n_pubchem}, reactions={n_reactions}) …")

    
    max_cid_row = con.execute("SELECT MAX(cid) FROM pubchem_smiles").fetchone()
    if max_cid_row is None or max_cid_row[0] is None:
        raise RuntimeError("pubchem_smiles table is empty or missing.")
    max_cid = int(max_cid_row[0])
    print(f"[eval_smiles]   pubchem_smiles MAX(cid) = {max_cid:,}")
    step = max(1, max_cid // n_pubchem)
    
    cid_targets = [1 + i * step for i in range(n_pubchem)]
    targets_sql = ", ".join(f"({c})" for c in cid_targets)

    pubchem_sql = f"""
        WITH targets(target_cid) AS (VALUES {targets_sql}),
        matched AS (
            SELECT DISTINCT ON (t.target_cid)
                p.cid,
                p.smiles
            FROM targets t
            JOIN pubchem_smiles p ON p.cid >= t.target_cid
            WHERE p.smiles IS NOT NULL
              AND p.smiles != ''
            ORDER BY t.target_cid, p.cid
        )
        SELECT cid, smiles, 'pubchem' AS source
        FROM matched
        LIMIT {n_pubchem}
    """

    reactions_sql = f"""
        SELECT
            NULL::BIGINT        AS cid,
            product_smiles      AS smiles,
            'reactions'         AS source
        FROM (
            SELECT DISTINCT product_smiles
            FROM retro_edges
            WHERE product_smiles IS NOT NULL
              AND product_smiles != ''
            USING SAMPLE {n_reactions} ROWS
        )
    """
    create_sql = f"""
        CREATE OR REPLACE TABLE {EVAL_TABLE} AS
        SELECT * FROM ({pubchem_sql})
        UNION ALL
        SELECT * FROM ({reactions_sql})
    """
    con.execute(create_sql)

    n = con.execute(f"SELECT COUNT(*) FROM {EVAL_TABLE}").fetchone()[0]
    by_source = con.execute(
        f"SELECT source, COUNT(*) FROM {EVAL_TABLE} GROUP BY source"
    ).fetchall()
    print(f"[eval_smiles]   Created {n:,} rows: "
          + ", ".join(f"{s}={c}" for s, c in by_source))
    return n

def fetch_eval_smiles(
    con: duckdb.DuckDBPyConnection,
    n: int,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return up to `n` rows from eval_smiles, optionally filtered by source.
    Uses MAX(cid) ordering for pubchem rows (sequential CID as the guide).
    """
    where = ""
    if source_filter:
        where = f"WHERE source = '{source_filter}'"

    
    rows = con.execute(f"""
        SELECT cid, smiles, source
        FROM {EVAL_TABLE}
        {where}
        ORDER BY
            CASE WHEN source = 'pubchem' THEN cid ELSE NULL END NULLS LAST,
            smiles
        LIMIT {n}
    """).fetchall()

    return [{"cid": r[0], "smiles": r[1], "source": r[2]} for r in rows]


def score_result(entry: Dict[str, Any], cid: Optional[int], source: str) -> Dict[str, Any]:
    """Convert a run_targets() result entry into a flat eval record."""
    routes = entry.get("routes", [])
    has_routes = bool(routes)
    stats = entry.get("stats", {})

    rec: Dict[str, Any] = {
        "name":       entry["name"],
        "smiles":     entry["smiles"],
        "cid":        cid,
        "source":     source,
        "has_routes": has_routes,
        "num_routes": len(routes),
        "eval_score": 1.0 if has_routes else -1.0,
        "error":      None,
        "runtime_s":  stats.get("runtime_seconds"),
        "nodes_explored":    stats.get("nodes_explored"),
        "reactions_queried": stats.get("reactions_queried"),
        "routes_generated":  stats.get("routes_generated"),
    }

    if has_routes:
        best = entry.get("best_route")
        if best:
            m = best.get_metrics()
            rec.update({
                "best_score":      best.score,
                "best_num_steps":  m["num_steps"],
                "best_avg_yield":  m["avg_yield"],
                "best_avg_temp":   m["avg_temp"],
                "best_is_complete": m["complete"],
                "best_has_safety": m["has_safety_concerns"],
                "num_complete_routes": sum(
                    1 for r in routes if len(r.open_molecules) == 0
                ),
            })

    return rec


def print_coverage_report(results: List[Dict[str, Any]], source_label: str = "all"):
    total = len(results)
    errors = [r for r in results if r.get("error")]
    with_routes = [r for r in results if r.get("has_routes")]
    without = [r for r in results if not r.get("has_routes") and not r.get("error")]
    complete = [r for r in with_routes if r.get("best_is_complete")]

    print(f"\n{'=-=-=-=-=-=-=-=-='}")
    print(f"COVERAGE REPORT  [source={source_label}]")
    print(f"{'=-=-=-=-=-=-=-=-='}")
    print(f"  Total SMILES evaluated : {total:>6}")
    print(f"  Errors                 : {len(errors):>6}")
    print(f"  With ≥1 route          : {len(with_routes):>6}  "
          f"({100*len(with_routes)/max(1,total):.1f}%)")
    print(f"  No route found         : {len(without):>6}  "
          f"({100*len(without)/max(1,total):.1f}%)")
    print(f"  Complete routes (best) : {len(complete):>6}  "
          f"({100*len(complete)/max(1,len(with_routes)):.1f}% of routed)")

    if with_routes:
        print(f"\n{'PATH QUALITY  (over SMILES that got routes)':}")
        print(f"  {'Metric':<30}  {'Min':>7}  {'Avg':>7}  {'Max':>7}")
        print(f"  {'-'*54}")

        def _stat(key):
            vals = [r[key] for r in with_routes if r.get(key) is not None]
            if not vals:
                return "N/A", "N/A", "N/A"
            return f"{min(vals):.2f}", f"{sum(vals)/len(vals):.2f}", f"{max(vals):.2f}"

        for label, key in [
            ("Routes per SMILES",    "num_routes"),
            ("Best route score",     "best_score"),
            ("Best route steps",     "best_num_steps"),
            ("Best avg yield (%)",   "best_avg_yield"),
            ("Best avg temp (°C)",   "best_avg_temp"),
            ("Runtime (s)",          "runtime_s"),
            ("Nodes explored",       "nodes_explored"),
        ]:
            lo, avg, hi = _stat(key)
            print(f"  {label:<30}  {lo:>7}  {avg:>7}  {hi:>7}")

        
        yield_vals = [r["best_avg_yield"] for r in with_routes
                      if r.get("best_avg_yield") is not None and r["best_avg_yield"] > 0]
        if yield_vals:
            hi_yield  = sum(1 for y in yield_vals if y >= 70)
            mid_yield = sum(1 for y in yield_vals if 50 <= y < 70)
            lo_yield  = sum(1 for y in yield_vals if y < 50)
            print(f"\n  Yield distribution (best route):")
            print(f"    ≥70%  : {hi_yield:>4}  ({100*hi_yield/len(yield_vals):.1f}%)")
            print(f"    50-70%: {mid_yield:>4}  ({100*mid_yield/len(yield_vals):.1f}%)")
            print(f"    <50%  : {lo_yield:>4}  ({100*lo_yield/len(yield_vals):.1f}%)")

        
        step_vals = [r["best_num_steps"] for r in with_routes if r.get("best_num_steps")]
        if step_vals:
            print(f"\n  Step distribution (best route):")
            for s in sorted(set(step_vals)):
                cnt = step_vals.count(s)
                print(f"    {s} step(s): {cnt:>4}  ({100*cnt/len(step_vals):.1f}%)")

    print(f"{'=-=-=-=-=-=-=-=-='}")

def print_per_source_breakdown(results: List[Dict[str, Any]], rows: List[Dict[str, Any]] = None):
    """Break coverage down by source (pubchem / reactions). source is in each result record."""
    by_source: Dict[str, List] = {}
    for res in results:
        src = res.get("source", "unknown")
        by_source.setdefault(src, []).append(res)

    print(f"\n{'=-=-=-=-=-=-=-=-='}")
    print(f"COVERAGE BY SOURCE")
    print(f"{'=-=-=-=-=-=-=-=-='}")
    for src, src_results in sorted(by_source.items()):
        total = len(src_results)
        routed = sum(1 for r in src_results if r.get("has_routes"))
        avg_sc = sum(r.get("eval_score", 0) for r in src_results) / max(1, total)
        print(f"  {src:<12}  {routed:>4}/{total:<4}  "
              f"({100*routed/max(1,total):.1f}% coverage)  "
              f"avg eval_score={avg_sc:+.2f}")
    print(f"{'=-=-=-=-=-=-=-=-='}")


def print_performance_summary(results: List[Dict[str, Any]]):
    """Overall scoring summary: aggregate eval_score, grade, score distribution."""
    total = len(results)
    scores = [r.get("eval_score", -1.0) for r in results]
    hits   = [r for r in results if r.get("has_routes")]
    misses = [r for r in results if not r.get("has_routes")]
    errors = [r for r in results if r.get("error")]

    total_score = sum(scores)
    n_hits   = len(hits)
    n_misses = len(misses) - len(errors)
    n_errors = len(errors)

    print(f"\n{'=-=-=-=-=-=-=-=-='}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'=-=-=-=-=-=-=-=-='}")
    print(f"  Total SMILES evaluated : {total}")
    print(f"  Routes found   (+1)    : {n_hits:>4}  ({100*n_hits/max(1,total):.1f}%)")
    print(f"  No route found (-1)    : {n_misses:>4}  ({100*n_misses/max(1,total):.1f}%)")
    print(f"  Errors         (-1)    : {n_errors:>4}  ({100*n_errors/max(1,total):.1f}%)")
    print(f"")
    print(f"  Total eval_score       : {total_score:+.0f}")
    print(f"  Coverage               : {100*n_hits/max(1,total):.1f}%")
    print(f"")
    print(f"  Scoring key:")
    print(f"    +1  route with steps found")
    print(f"    -1  no route found or error")
    print(f"{'=-=-=-=-=-=-=-=-='}")






def parse_args():
    p = argparse.ArgumentParser(description="Evaluate OrdRetroSynth coverage & path quality")
    p.add_argument("--db",          default="retrosynthesis.duckdb", help="Path to DuckDB file")
    p.add_argument("--n",           type=int, default=200, help="Total SMILES to evaluate (default 200)")
    p.add_argument("--n-pubchem",   type=int, default=None, help="Pubchem rows in eval_smiles table (default n//2)")
    p.add_argument("--n-reactions", type=int, default=None, help="Reaction product rows in eval_smiles table (default n//2)")
    p.add_argument("--rebuild",     action="store_true", help="Force-rebuild eval_smiles table")
    p.add_argument("--source",      choices=["pubchem", "reactions", "all"], default="all", help="Which source to sample from")
    p.add_argument("--max-depth",   type=int, default=4)
    p.add_argument("--beam",        type=int, default=25)
    p.add_argument("--per-node",    type=int, default=200)
    return p.parse_args()


def main():
    args = parse_args()

    db_path = args.db
    if not os.path.isabs(db_path):
        db_path = os.path.join(_HERE, db_path)

    
    eval_dir = os.path.join(_HERE, "eval_results")
    os.makedirs(eval_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = os.path.join(eval_dir, f"eval_{timestamp}.txt")
    json_path = os.path.join(eval_dir, f"eval_{timestamp}.json")

    log_file = open(log_path, "w")
    sys.stdout = Tee(log_file)

    print(f"{'=-=-=-=-=-=-=-=-='}")
    print(f"OrdRetroSynth  –  Evaluation Run")
    print(f"Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DB      : {db_path}")
    print(f"Config  : n={args.n}, max_depth={args.max_depth}, "
          f"beam={args.beam}, per_node={args.per_node}")
    print(f"{'=-=-=-=-=-=-=-=-='}\n")

    
    con = duckdb.connect(db_path, read_only=False)

    n_pub = args.n_pubchem   if args.n_pubchem   else args.n // 2
    n_rxn = args.n_reactions if args.n_reactions else args.n - n_pub

    build_eval_smiles_table(con, n_pubchem=n_pub, n_reactions=n_rxn, rebuild=args.rebuild)

    source_filter = None if args.source == "all" else args.source
    rows = fetch_eval_smiles(con, n=args.n, source_filter=source_filter)
    con.close()

    print(f"\n[eval] Fetched {len(rows)} SMILES to evaluate "
          f"(source filter: {args.source})\n")

    if not rows:
        print("No SMILES found. Exiting.")
        sys.stdout = sys.stdout.stdout
        log_file.close()
        return

    
    
    targets: Dict[str, str] = {}
    row_meta: Dict[str, Dict] = {}  
    for i, row in enumerate(rows):
        name = f"CID_{row['cid']}" if row["cid"] else f"rxn_{i}"
        targets[name] = row["smiles"]
        row_meta[name] = {"cid": row["cid"], "source": row["source"]}

    print(f"[eval] Running run_targets() on {len(targets)} SMILES …\n")

    
    t_total_start = time.time()
    rt_results = run_targets(
        targets=targets,
        duckdb_path=db_path,
        max_depth=args.max_depth,
        beam_width=args.beam,
        per_node_limit=args.per_node,
    )
    total_elapsed = time.time() - t_total_start

    
    results: List[Dict[str, Any]] = []
    for entry in rt_results:
        meta = row_meta[entry["name"]]
        rec  = score_result(entry, cid=meta["cid"], source=meta["source"])
        results.append(rec)

        cid_str = str(meta["cid"]) if meta["cid"] else "—"
        src = meta["source"]
        if rec["has_routes"]:
            print(f"cid={cid_str:<12}  source={src:<10}  "
                  f"eval_score={rec['eval_score']:+.0f}  "
                  f"routes={rec['num_routes']}  "
                  f"steps={rec.get('best_num_steps', '?')}  "
                  f"yield={rec.get('best_avg_yield', 0.0):.1f}%")
        else:
            print(f"cid={cid_str:<12}  source={src:<10}  "
                  f"eval_score={rec['eval_score']:+.0f}  no routes")

    
    print_coverage_report(results, source_label=args.source)
    print_per_source_breakdown(results, rows)  
    print_performance_summary(results)

    print(f"\n{'=-=-=-=-=-=-=-=-='}")
    print(f"TIMING")
    print(f"{'=-=-=-=-=-=-=-=-='}")
    print(f"  Total wall time : {total_elapsed:.1f}s")
    print(f"  Avg per SMILES  : {total_elapsed/max(1,len(results)):.2f}s")
    print(f"{'=-=-=-=-=-=-=-=-='}\n")

    
    with open(json_path, "w") as fh:
        json.dump(results, fh, indent=2, default=str)

    sys.stdout = sys.stdout.stdout
    log_file.close()
    print(f"Summary : {log_path}")
    print(f"JSON    : {json_path}")


if __name__ == "__main__":
    main()
