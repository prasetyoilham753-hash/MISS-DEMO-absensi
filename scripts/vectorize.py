import sys

def trace_pbm(pbm_path, svg_path):
    with open(pbm_path, 'r') as f:
        header = []
        while len(header) < 3:
            line = f.readline().strip()
            if line and not line.startswith('#'):
                header.extend(line.split())
        w = int(header[1])
        h = int(header[2])
        grid = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                grid.extend(int(x) for x in line.split())

    # Foreground pixels are 0 (white text on black in original)
    fg = set()
    for y in range(h):
        for x in range(w):
            if grid[y * w + x] == 0:
                fg.add((x, y))

    # Directed edges between grid cells: (x, y) cell has 4 edges
    # Top: (x, y) -> (x+1, y)
    # Right: (x+1, y) -> (x+1, y+1)
    # Bottom: (x+1, y+1) -> (x, y+1)
    # Left: (x, y+1) -> (x, y)
    edges = {}
    
    for (x, y) in fg:
        # Top edge
        if (x, y - 1) not in fg:
            edges[(x, y)] = (x + 1, y)
        # Right edge
        if (x + 1, y) not in fg:
            edges[(x + 1, y)] = (x + 1, y + 1)
        # Bottom edge
        if (x, y + 1) not in fg:
            edges[(x + 1, y + 1)] = (x, y + 1)
        # Left edge
        if (x - 1, y) not in fg:
            edges[(x, y + 1)] = (x, y)

    # Note: because multiple edges can share a vertex, let's use adjacency list with visited tracking
    from collections import defaultdict
    adj = defaultdict(list)
    for (x, y) in fg:
        if (x, y - 1) not in fg:
            adj[(x, y)].append((x + 1, y))
        if (x + 1, y) not in fg:
            adj[(x + 1, y)].append((x + 1, y + 1))
        if (x, y + 1) not in fg:
            adj[(x + 1, y + 1)].append((x, y + 1))
        if (x - 1, y) not in fg:
            adj[(x, y + 1)].append((x, y))

    visited_edges = set()
    loops = []

    for start_node in list(adj.keys()):
        for next_node in adj[start_node]:
            if (start_node, next_node) in visited_edges:
                continue
            
            loop = [start_node]
            curr = next_node
            visited_edges.add((start_node, next_node))
            
            while curr != start_node:
                loop.append(curr)
                # Pick next unvisited edge
                found = False
                for candidate in adj[curr]:
                    if (curr, candidate) not in visited_edges:
                        visited_edges.add((curr, candidate))
                        curr = candidate
                        found = True
                        break
                if not found:
                    break
            if curr == start_node and len(loop) >= 3:
                loops.append(loop)

    # Simplify loops: remove colinear points
    def simplify(points):
        if len(points) < 3:
            return points
        res = []
        n = len(points)
        for i in range(n):
            p_prev = points[(i - 1) % n]
            p_curr = points[i]
            p_next = points[(i + 1) % n]
            dx1 = p_curr[0] - p_prev[0]
            dy1 = p_curr[1] - p_prev[1]
            dx2 = p_next[0] - p_curr[0]
            dy2 = p_next[1] - p_curr[1]
            if dx1 * dy2 == dy1 * dx2:
                continue
            res.append(p_curr)
        return res

    # Further simplify with tolerance
    def rdp(pts, epsilon=0.5):
        if len(pts) < 3:
            return pts
        def get_dist(p, a, b):
            if a == b:
                return ((p[0]-a[0])**2 + (p[1]-a[1])**2)**0.5
            num = abs((b[1]-a[1])*p[0] - (b[0]-a[0])*p[1] + b[0]*a[1] - b[1]*a[0])
            den = ((b[1]-a[1])**2 + (b[0]-a[0])**2)**0.5
            return num / den

        dmax = 0
        idx = 0
        for i in range(1, len(pts) - 1):
            d = get_dist(pts[i], pts[0], pts[-1])
            if d > dmax:
                idx = i
                dmax = d
        if dmax > epsilon:
            r1 = rdp(pts[:idx+1], epsilon)
            r2 = rdp(pts[idx:], epsilon)
            return r1[:-1] + r2
        else:
            return [pts[0], pts[-1]]

    svg_paths = []
    for loop in loops:
        simp = simplify(loop)
        if len(simp) > 4:
            simp = rdp(simp + [simp[0]], epsilon=0.45)[:-1]
        if len(simp) >= 3:
            d = f"M {simp[0][0]} {simp[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in simp[1:]) + " Z"
            svg_paths.append(d)

    path_data = " ".join(svg_paths)
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" fill="currentColor" fill-rule="evenodd">
  <path d="{path_data}" />
</svg>'''
    
    with open(svg_path, 'w') as f:
        f.write(svg_content)
    print(f"Generated SVG with {len(svg_paths)} paths, size {len(svg_content)} bytes")

if __name__ == '__main__':
    trace_pbm('public/assets/aistudio/clean.pbm', 'public/assets/aistudio/misstheism_vector.svg')
