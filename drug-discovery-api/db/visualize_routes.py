import sys
import os
import json
import argparse
import math
import textwrap
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc


DATA_DIR   = Path(__file__).parent
NDJSON     = DATA_DIR / "eval_results" / "filtered_has_routes.ndjson"
DB_PATH    = str(DATA_DIR / "retrosynthesis.duckdb")
OUT_DIR    = DATA_DIR / "eval_results" / "route_graphs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE   = OUT_DIR / "retrosynthesis_dashboard.html"

sys.path.insert(0, str(DATA_DIR))
from retrosynth import OrdRetroSynth, SearchStats, Route  

DEPTH_COLORS = [
    "#1f77b4",  
    "#ff7f0e",  
    "#2ca02c",  
    "#d62728",  
    "#9467bd",  
    "#8c564b",  
]

def depth_color(d: int) -> str:
    return DEPTH_COLORS[min(d, len(DEPTH_COLORS) - 1)]


def short_smiles(smi: str, max_len: int = 30) -> str:
    return smi if len(smi) <= max_len else smi[:max_len - 1] + "…"

def wrap_smiles(smi: str, width: int = 40) -> str:
    return "<br>".join(textwrap.wrap(smi, width=width))


def route_to_dag(route: Route, cid: int) -> nx.DiGraph:
    G = nx.DiGraph()
    target = route.target_smiles
    depth: Dict[str, int] = {target: 0}
    
    G.add_node(target,
               node_type="target",
               depth=0,
               label=short_smiles(target),
               full_smiles=target,
               cid=cid)

    for step_idx, step in enumerate(route.steps):
        product = step.product_smiles
        prod_depth = depth.get(product, 0)

        
        rxn_id = f"rxn_{step_idx}_{step.reaction_id}"
        rxn_depth = prod_depth + 1

        yield_str  = f"{step.yield_pct:.1f}%" if step.yield_pct else "N/A"
        temp_str   = f"{step.temperature_c:.0f}°C" if step.temperature_c else "N/A"
        source_str = step.source or "N/A"

        G.add_node(rxn_id,
                   node_type="reaction",
                   depth=rxn_depth,
                   label=f"Step {step_idx + 1}",
                   reaction_id=step.reaction_id,
                   source=source_str,
                   yield_pct=yield_str,
                   temperature=temp_str,
                   reagents=step.reagent_smiles or "",
                   solvent=step.solvent_smiles or "",
                   catalyst=step.catalyst_smiles or "",
                   doi=step.doi or "",
                   step_score=f"{step.step_score:.2f}")

        
        G.add_edge(product, rxn_id)

        for reactant in step.reactants:
            r_depth = rxn_depth + 1
            if reactant not in depth:
                depth[reactant] = r_depth
            if reactant not in G:
                G.add_node(reactant,
                           node_type="reactant",
                           depth=r_depth,
                           label=short_smiles(reactant),
                           full_smiles=reactant)
            G.add_edge(rxn_id, reactant)

    return G


def hierarchical_layout(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    layers: Dict[int, List[str]] = {}
    for node, data in G.nodes(data=True):
        d = data.get("depth", 0)
        layers.setdefault(d, []).append(node)

    pos = {}
    for depth_val, nodes in layers.items():
        n = len(nodes)
        for i, node in enumerate(nodes):
            y = (i - (n - 1) / 2.0) * 1.5
            pos[node] = (float(depth_val) * 3.0, y)
    return pos


def dag_to_figure_json(G: nx.DiGraph, cid: int, smiles: str,
                       meta: Dict[str, Any]) -> str:
    """Return the Plotly figure as a JSON string (for embedding inline)."""
    return dag_to_plotly(G, cid, smiles, meta).to_json()


def dag_to_plotly(G: nx.DiGraph, cid: int, smiles: str,
                  meta: Dict[str, Any]) -> go.Figure:

    pos = hierarchical_layout(G)

    
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1.5, color="#888"),
        hoverinfo="none",
        showlegend=False,
    )

    
    node_types = {"target": [], "reaction": [], "reactant": []}
    for node, data in G.nodes(data=True):
        node_types[data["node_type"]].append(node)

    traces = [edge_trace]

    style_map = {
        "target":   dict(size=28, symbol="circle",       line_width=3, line_color="#333"),
        "reaction": dict(size=20, symbol="diamond",      line_width=2, line_color="#555"),
        "reactant": dict(size=18, symbol="circle-open",  line_width=2, line_color=None),
    }

    for ntype, nodes in node_types.items():
        if not nodes:
            continue
        xs, ys, texts, hovers, colors = [], [], [], [], []
        for node in nodes:
            data = G.nodes[node]
            x, y = pos[node]
            xs.append(x)
            ys.append(y)
            texts.append(data.get("label", ""))
            colors.append(depth_color(data.get("depth", 0)))

            if ntype == "target":
                hover = (
                    f"<b>TARGET</b><br>"
                    f"CID: {cid}<br>"
                    f"SMILES: {wrap_smiles(smiles)}<br>"
                    f"Routes found: {meta.get('num_routes', '?')}<br>"
                    f"Best depth: {meta.get('best_num_steps', '?')} step(s)<br>"
                    f"Score: {meta.get('best_score', 'N/A')}"
                )
            elif ntype == "reaction":
                hover = (
                    f"<b>REACTION STEP</b><br>"
                    f"Reaction ID: {data.get('reaction_id','?')}<br>"
                    f"Source: {data.get('source','?')}<br>"
                    f"Yield: {data.get('yield_pct','N/A')}<br>"
                    f"Temp: {data.get('temperature','N/A')}<br>"
                    f"Reagents: {wrap_smiles(data.get('reagents','')) or 'N/A'}<br>"
                    f"Solvent: {wrap_smiles(data.get('solvent','')) or 'N/A'}<br>"
                    f"Catalyst: {wrap_smiles(data.get('catalyst','')) or 'N/A'}<br>"
                    f"Step score: {data.get('step_score','?')}<br>"
                    f"DOI: {data.get('doi','N/A')}"
                )
            else:  
                full = data.get("full_smiles", node)
                hover = (
                    f"<b>REACTANT</b><br>"
                    f"SMILES: {wrap_smiles(full)}<br>"
                    f"Depth: {data.get('depth', '?')}"
                )

            hovers.append(hover)

        st = style_map[ntype]
        lc = st["line_color"] if st["line_color"] else colors
        traces.append(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            text=texts,
            textposition="top center",
            textfont=dict(size=9),
            hovertext=hovers,
            hoverinfo="text",
            marker=dict(
                size=st["size"],
                symbol=st["symbol"],
                color=colors,
                line=dict(width=st["line_width"], color=lc),
            ),
            name=ntype.capitalize(),
        ))

    
    max_depth = max((d.get("depth", 0) for _, d in G.nodes(data=True)), default=0)
    annotations = []
    for d in range(max_depth + 1):
        label = {0: "Target", 1: "Step 1 reactions", 2: "Depth-2 reactants"}.get(
            d, f"Depth {d}"
        )
        annotations.append(dict(
            x=float(d) * 3.0,
            y=-max(2.5, (max(len([n for n, dd in G.nodes(data=True)
                                  if dd.get("depth") == d]), 1) * 1.5) / 2 + 0.8),
            xref="x", yref="y",
            text=f"<b>Depth {d}</b><br>{label}",
            showarrow=False,
            font=dict(size=10, color=depth_color(d)),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor=depth_color(d),
            borderwidth=1,
        ))

    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            title=dict(
                text=(
                    f"<b>Retrosynthesis Graph — CID {cid}</b><br>"
                    f"<span style='font-size:11px'>{smiles}</span>"
                ),
                font=dict(size=14),
            ),
            showlegend=True,
            hovermode="closest",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=620,
            margin=dict(l=20, r=20, t=90, b=60),
            annotations=annotations,
        )
    )
    return fig


def build_dashboard_html(records: List[Dict[str, Any]]) -> str:
    n = len(records)
    avg_routes = sum(r["num_routes"] for r in records) / n if n else 0
    avg_depth  = sum((r.get("max_depth_reached") or r.get("best_num_steps") or 0)
                     for r in records) / n if n else 0
    with_yield = sum(1 for r in records
                     if r.get("best_avg_yield") and not math.isnan(float(r["best_avg_yield"])))

    
    scatter_x, scatter_y, scatter_color, scatter_hover, scatter_link = [], [], [], [], []
    for r in records:
        depth = r.get("max_depth_reached") or r.get("best_num_steps") or 0
        scatter_x.append(depth)
        scatter_y.append(r["num_routes"])
        scatter_color.append(depth_color(min(depth, 5)))
        score_str = (f"{r['best_score']:.2f}"
                     if r.get("best_score") and not math.isnan(float(r["best_score"]))
                     else "N/A")
        yield_str = (f"{r['best_avg_yield']:.1f}%"
                     if r.get("best_avg_yield") and not math.isnan(float(r["best_avg_yield"]))
                     else "N/A")
        scatter_hover.append(
            f"<b>CID {r['cid']}</b><br>"
            f"SMILES: {r['smiles'][:55]}{'…' if len(r['smiles'])>55 else ''}<br>"
            f"Routes: {r['num_routes']}<br>"
            f"Best depth: {depth}<br>"
            f"Best score: {score_str}<br>"
            f"Avg yield: {yield_str}"
        )
        scatter_link.append(str(r['cid']))

    scatter_fig = go.Figure(go.Scatter(
        x=scatter_x, y=scatter_y,
        mode="markers",
        marker=dict(size=12, color=scatter_color,
                    line=dict(width=1, color="#333")),
        hovertext=scatter_hover,
        hoverinfo="text",
        customdata=scatter_link,
    ))
    scatter_fig.update_layout(
        xaxis=dict(title="Best route depth (steps)", dtick=1,
                   gridcolor="#eee", zeroline=False),
        yaxis=dict(title="Number of routes found",
                   gridcolor="#eee", zeroline=False),
        plot_bgcolor="white", paper_bgcolor="white",
        height=340, margin=dict(l=50, r=20, t=30, b=50),
        clickmode="event",
    )
    scatter_json = scatter_fig.to_json()

    
    depth_counts: Dict[int, int] = {}
    for r in records:
        d = r.get("max_depth_reached") or r.get("best_num_steps") or 0
        depth_counts[d] = depth_counts.get(d, 0) + 1
    donut_labels = [f"Depth {d}" for d in sorted(depth_counts)]
    donut_values = [depth_counts[d] for d in sorted(depth_counts)]
    donut_colors = [depth_color(d) for d in sorted(depth_counts)]

    donut_fig = go.Figure(go.Pie(
        labels=donut_labels, values=donut_values,
        hole=0.55,
        marker=dict(colors=donut_colors,
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        hovertemplate="%{label}<br>%{value} molecules (%{percent})<extra></extra>",
    ))
    donut_fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="white",
        showlegend=False,
    )
    donut_json = donut_fig.to_json()

    
    table_rows = []
    for r in records:
        depth = r.get("max_depth_reached") or r.get("best_num_steps") or 0
        score_str = (f"{r['best_score']:.3f}"
                     if r.get("best_score") and not math.isnan(float(r["best_score"]))
                     else "—")
        yield_str = (f"{r['best_avg_yield']:.1f}%"
                     if r.get("best_avg_yield") and not math.isnan(float(r["best_avg_yield"]))
                     else "—")
        dot = f'<span class="dot" style="background:{depth_color(min(depth,5))}"></span>'
        table_rows.append(
            f'<tr onclick="showGraph({r["cid"]}, this)" '
            f'data-cid="{r["cid"]}" data-smiles="{r["smiles"]}" '
            f'data-routes="{r["num_routes"]}" data-depth="{depth}">'
            f'<td><b>{r["cid"]}</b></td>'
            f'<td class="smiles-cell" title="{r["smiles"]}">{r["smiles"][:60]}{"…" if len(r["smiles"])>60 else ""}</td>'
            f'<td>{dot} {depth}</td>'
            f'<td>{r["num_routes"]}</td>'
            f'<td>{score_str}</td>'
            f'<td>{yield_str}</td>'
            f'<td>{r.get("nodes_explored","—")}</td>'
            f'</tr>'
        )
    table_rows_html = "\n".join(table_rows)

    graphs_json = json.dumps({r["cid"]: r["graph_json"] for r in records})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Retrosynthesis Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; overflow: hidden; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f0f2f5; color: #222;
    display: flex; flex-direction: column;
  }}
  header {{
    background: linear-gradient(135deg, #1a3a5c 0%, #1f77b4 100%);
    color: white; padding: 14px 28px; flex-shrink: 0;
    display: flex; align-items: center; gap: 32px;
  }}
  header h1 {{ font-size: 18px; font-weight: 700; white-space: nowrap; }}
  .hcards {{ display: flex; gap: 20px; }}
  .hcard {{ background: rgba(255,255,255,.15); border-radius: 8px; padding: 8px 16px; text-align:center; }}
  .hcard .val {{ font-size: 22px; font-weight: 700; }}
  .hcard .lbl {{ font-size: 10px; opacity: .8; }}

  /* main split */
  .body {{ display: flex; flex: 1; overflow: hidden; }}

  /* LEFT PANEL */
  .left {{
    width: 520px; min-width: 380px; display: flex; flex-direction: column;
    border-right: 1px solid #dde; background: white; flex-shrink: 0;
  }}
  .charts-row {{
    display: grid; grid-template-columns: 1fr 160px;
    gap: 0; border-bottom: 1px solid #eee; flex-shrink: 0;
  }}
  .chart-card {{ padding: 10px 12px; }}
  .chart-card h3 {{ font-size: 11px; font-weight: 600; color: #666; margin-bottom: 4px; }}
  .table-wrap {{ flex: 1; overflow-y: auto; }}
  .table-toolbar {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; border-bottom: 1px solid #eee;
    background: #fafafa; flex-shrink: 0;
    position: sticky; top: 0; z-index: 10;
  }}
  .table-toolbar h3 {{ font-size: 12px; font-weight: 600; flex: 1; color: #444; }}
  .table-toolbar input {{
    padding: 5px 10px; border: 1px solid #ddd;
    border-radius: 5px; font-size: 12px; width: 180px;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  thead th {{
    background: #f5f7fa; text-align: left;
    padding: 7px 8px; font-size: 10px; font-weight: 700;
    color: #555; border-bottom: 2px solid #e8eaed;
    cursor: pointer; user-select: none; white-space: nowrap;
    position: sticky; top: 0;
  }}
  thead th:hover {{ background: #eaedf0; }}
  thead th.sorted-asc::after  {{ content: ' ▲'; }}
  thead th.sorted-desc::after {{ content: ' ▼'; }}
  tbody tr {{
    cursor: pointer; transition: background .1s;
    border-bottom: 1px solid #f2f2f2;
  }}
  tbody tr:hover {{ background: #eef4ff; }}
  tbody tr.active {{ background: #ddeeff !important; }}
  tbody td {{ padding: 6px 8px; vertical-align: middle; }}
  .smiles-cell {{
    font-family: monospace; font-size: 10px;
    max-width: 160px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }}
  .dot {{
    display: inline-block; width: 9px; height: 9px;
    border-radius: 50%; vertical-align: middle;
  }}
  .no-results {{ text-align:center; padding:20px; color:#aaa; font-size:12px; }}

  /* RIGHT PANEL */
  .right {{
    flex: 1; display: flex; flex-direction: column;
    background: #f8f9fb; overflow: hidden;
  }}
  .graph-header {{
    padding: 10px 20px; border-bottom: 1px solid #e0e4ea;
    background: white; flex-shrink: 0;
  }}
  .graph-header .cid-label {{ font-size: 14px; font-weight: 700; color: #1f77b4; }}
  .graph-header .smiles-label {{ font-size: 11px; font-family: monospace; color: #666; margin-top: 2px; word-break: break-all; }}
  .graph-header .meta-pills {{ display:flex; gap:8px; margin-top:6px; flex-wrap:wrap; }}
  .pill {{
    background:#f0f4ff; border:1px solid #c8d8f8; border-radius:12px;
    padding:2px 10px; font-size:10px; color:#335;
  }}
  #graph-placeholder {{
    flex:1; display:flex; align-items:center; justify-content:center;
    color:#bbb; font-size:14px; flex-direction:column; gap:8px;
  }}
  #graph-plot {{ flex:1; min-height:0; }}
</style>
</head>
<body>
<header>
  <h1>Retrosynthesis Dashboard</h1>
  <div class="hcards">
    <div class="hcard"><div class="val">{n}</div><div class="lbl">molecules</div></div>
    <div class="hcard"><div class="val">{avg_routes:.1f}</div><div class="lbl">avg routes</div></div>
    <div class="hcard"><div class="val">{avg_depth:.1f}</div><div class="lbl">avg depth</div></div>
    <div class="hcard"><div class="val">{with_yield}</div><div class="lbl">with yield</div></div>
  </div>
</header>

<div class="body">
  <!-- LEFT -->
  <div class="left">
    <div class="charts-row">
      <div class="chart-card">
        <h3>Routes vs depth &nbsp;<span style="font-weight:400">(click point)</span></h3>
        <div id="scatter"></div>
      </div>
      <div class="chart-card">
        <h3>Depth dist.</h3>
        <div id="donut"></div>
      </div>
    </div>
    <div class="table-toolbar">
      <h3>All molecules ({n})</h3>
      <input id="search" type="text" placeholder="Search CID / SMILES…" oninput="filterTable()">
    </div>
    <div class="table-wrap">
      <table id="mol-table">
        <thead>
          <tr>
            <th onclick="sortTable(0)">CID</th>
            <th onclick="sortTable(1)">SMILES</th>
            <th onclick="sortTable(2)">Depth</th>
            <th onclick="sortTable(3)">Routes</th>
            <th onclick="sortTable(4)">Score</th>
            <th onclick="sortTable(5)">Yield</th>
          </tr>
        </thead>
        <tbody id="table-body">
{table_rows_html}
        </tbody>
      </table>
      <p id="no-results" class="no-results" style="display:none">No results.</p>
    </div>
  </div>

  <!-- RIGHT -->
  <div class="right">
    <div class="graph-header" id="graph-header">
      <div class="cid-label">← Select a molecule from the table</div>
    </div>
    <div id="graph-placeholder">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
        <circle cx="5" cy="12" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="19" cy="19" r="2"/>
        <line x1="7" y1="12" x2="17" y2="6"/><line x1="7" y1="12" x2="17" y2="18"/>
      </svg>
      <span>Click any row or scatter point to view its synthesis graph</span>
    </div>
    <div id="graph-plot" style="display:none"></div>
  </div>
</div>

<script>
const GRAPHS = {graphs_json};
const scatterData = {scatter_json};
const donutData   = {donut_json};

Plotly.newPlot('scatter', scatterData.data, scatterData.layout, {{responsive:true}});
Plotly.newPlot('donut',   donutData.data,   donutData.layout,   {{responsive:true}});

let activeCid = null;

function showGraph(cid, rowEl) {{
  cid = Number(cid);
  if (!GRAPHS[cid]) return;

  // highlight row
  document.querySelectorAll('#table-body tr').forEach(r => r.classList.remove('active'));
  if (rowEl) rowEl.classList.add('active');

  // update header
  const row = document.querySelector(`#table-body tr[data-cid="${{cid}}"]`);
  const smiles = row?.dataset.smiles || '';
  const depth  = row?.dataset.depth  || '';
  const routes = row?.dataset.routes || '';
  document.getElementById('graph-header').innerHTML = `
    <div class="cid-label">CID ${{cid}}</div>
    <div class="smiles-label">${{smiles}}</div>
    <div class="meta-pills">
      <span class="pill">Depth ${{depth}}</span>
      <span class="pill">${{routes}} routes</span>
    </div>`;

  // parse & render graph
  const figData = JSON.parse(GRAPHS[cid]);
  figData.layout.height = undefined;
  figData.layout.autosize = true;
  figData.layout.margin = {{l:20, r:20, t:60, b:20}};

  const plot = document.getElementById('graph-plot');
  document.getElementById('graph-placeholder').style.display = 'none';
  plot.style.display = 'block';

  if (activeCid === cid) {{
    Plotly.react('graph-plot', figData.data, figData.layout, {{responsive:true}});
  }} else {{
    Plotly.newPlot('graph-plot', figData.data, figData.layout, {{responsive:true}});
  }}
  activeCid = cid;
}}

// scatter click → show graph
document.getElementById('scatter').on('plotly_click', function(d) {{
  const cid = Number(d.points[0].customdata);
  const rowEl = document.querySelector(`#table-body tr[data-cid="${{cid}}"]`);
  showGraph(cid, rowEl);
  if (rowEl) rowEl.scrollIntoView({{block:'nearest', behavior:'smooth'}});
}});

// table search
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const rows = document.querySelectorAll('#table-body tr');
  let visible = 0;
  rows.forEach(row => {{
    const show = !q || row.dataset.cid.includes(q) || row.dataset.smiles.toLowerCase().includes(q);
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('no-results').style.display = visible === 0 ? '' : 'none';
}}

// table sort
let sortState = {{col:-1, asc:true}};
function sortTable(col) {{
  const tbody = document.getElementById('table-body');
  const rows  = Array.from(tbody.querySelectorAll('tr'));
  const asc   = sortState.col === col ? !sortState.asc : true;
  sortState   = {{col, asc}};
  rows.sort((a, b) => {{
    const aVal = a.cells[col]?.innerText.replace(/[^\d.\-]/g,'') || '';
    const bVal = b.cells[col]?.innerText.replace(/[^\d.\-]/g,'') || '';
    const aNum = parseFloat(aVal), bNum = parseFloat(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum-bNum : bNum-aNum;
    return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  }});
  rows.forEach(r => tbody.appendChild(r));
  document.querySelectorAll('thead th').forEach((th,i) => {{
    th.classList.remove('sorted-asc','sorted-desc');
    if (i===col) th.classList.add(asc?'sorted-asc':'sorted-desc');
  }});
}}
</script>
</body>
</html>"""
    return html


def load_records(cids_filter: Optional[List[int]] = None,
                 top: Optional[int] = None) -> List[Dict[str, Any]]:
    records = []
    with open(NDJSON) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("has_routes") and r.get("eval_score", 0) == 1:
                records.append(r)

    if cids_filter:
        records = [r for r in records if r["cid"] in cids_filter]
    elif top:
        records = records[:top]

    return records


def main():
    parser = argparse.ArgumentParser(description="Retrosynthesis graph visualiser")
    parser.add_argument("--top",  type=int, default=20,
                        help="Visualise the first N records (default 20)")
    parser.add_argument("--cids", type=str, default="",
                        help="Comma-separated CID list, e.g. 19,39,135")
    parser.add_argument("--all",  action="store_true",
                        help="Visualise all records (slow)")
    parser.add_argument("--clean", action="store_true",
                        help="Delete stale cid_*.html files in route_graphs/")
    args = parser.parse_args()

    if args.clean:
        stale = list(OUT_DIR.glob("cid_*.html"))
        for f in stale:
            f.unlink()
        print(f"Removed {len(stale)} stale cid_*.html files.")

    cids_filter = [int(c) for c in args.cids.split(",") if c.strip()] if args.cids else None
    top = None if args.all or cids_filter else args.top

    records = load_records(cids_filter=cids_filter, top=top)
    print(f"Loaded {len(records)} records from {NDJSON.name}")

    retro = OrdRetroSynth(duckdb_path=DB_PATH)

    processed = []

    for idx, rec in enumerate(records):
        cid    = rec["cid"]
        smiles = rec["smiles"]
        print(f"  [{idx+1}/{len(records)}] CID {cid}  {smiles[:60]}", end="  ", flush=True)

        retro.stats = SearchStats(
            target_smiles=smiles,
            max_depth=4,
            beam_width=25,
            per_node_limit=200,
        )

        try:
            routes = retro.build_routes(
                target_smiles=smiles,
                max_depth=4,
                beam_width=25,
                per_node_limit=200,
            )
            routes = [r for r in routes if r.steps]
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        if not routes:
            print("no routes")
            continue

        best_route, _ = retro.select_best_route(routes)

        G = route_to_dag(best_route, cid)

        
        max_depth_reached = max(
            (d.get("depth", 0) for _, d in G.nodes(data=True)), default=0
        )
        all_reactants = [
            n for n, d in G.nodes(data=True) if d.get("node_type") == "reactant"
        ]

        print(f"depth={max_depth_reached}  reactants={len(all_reactants)}")

        graph_json = dag_to_figure_json(G, cid, smiles, rec)

        processed.append({**rec,
                          "max_depth_reached": max_depth_reached,
                          "num_reactants": len(all_reactants),
                          "graph_json": graph_json})

    if not processed:
        print("Nothing to visualise.")
        return

    dashboard_html = build_dashboard_html(processed)
    OUT_FILE.write_text(dashboard_html)
    print(f"\nDashboard saved → {OUT_FILE}")
    print(f"Done. Open  {OUT_FILE}  in a browser.")


if __name__ == "__main__":
    main()
