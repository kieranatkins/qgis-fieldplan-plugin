import math
from collections import defaultdict

def _calculate_bearing(o_x, o_y, d_x, d_y):
    dx = d_x - o_x
    dy = d_y - o_y
    bearing = math.degrees(math.atan2(dx, dy)) % 360
    return bearing

def _find_line_point_distance(line_x1, line_y1, line_x2, line_y2, point_x, point_y):
    """
    Calculate the shortest distance between a point and a line segment, and find the closest point on the line.
    
    Args:
        line_x1, line_y1: Coordinates of the first endpoint of the line
        line_x2, line_y2: Coordinates of the second endpoint of the line  
        point_x, point_y: Coordinates of the point
    
    Returns:
        tuple: (distance, closest_x, closest_y) where:
            - distance: shortest distance between point and line
            - closest_x, closest_y: coordinates of the closest point on the line
    """
    # Calculate line vector components
    line_dx = line_x2 - line_x1
    line_dy = line_y2 - line_y1
    
    # Calculate line length squared
    line_length_squared = line_dx ** 2 + line_dy ** 2
    
    # Handle case where line points are identical
    if line_length_squared == 0:
        closest_x, closest_y = line_x1, line_y1
        distance = math.sqrt((line_x1 - point_x) ** 2 + (line_y1 - point_y) ** 2)
        return distance, closest_x, closest_y
    
    # Calculate projection parameter t
    # t represents how far along the line the closest point is (0 = at line_x1, 1 = at line_x2)
    t = ((point_x - line_x1) * line_dx + (point_y - line_y1) * line_dy) / line_length_squared
    
    # Clamp t to [0, 1] to ensure the closest point is on the line segment
    t = max(0, min(1, t))
    
    # Calculate the closest point on the line
    closest_x = line_x1 + t * line_dx
    closest_y = line_y1 + t * line_dy
    
    # Calculate the distance
    distance = math.sqrt((closest_x - point_x) ** 2 + (closest_y - point_y) ** 2)
    
    return distance, closest_x, closest_y

def _line_intersection(line_a, line_b):
    """
    Calculate the intersection point of two lines in UTM coordinates.
    Each line is in format [x1, y1, x2, y2] where x=easting, y=northing.
    Returns (x, y) intersection point or None if lines are parallel.
    """
    x1, y1, x2, y2 = line_a
    x3, y3, x4, y4 = line_b
    
    # Calculate denominator using double precision
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    # Lines are parallel or coincident (using small tolerance)
    if abs(denom) < 1e-10:
        return None
    
    # Calculate intersection using line-line intersection formula
    # This works for any Cartesian coordinates including UTM
    px_numer = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    py_numer = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
    
    px = px_numer / denom
    py = py_numer / denom
    
    return (px, py)

def _four_lines_intersect(line1, line2, line3, line4):
    """
    Find the four intersection points where four lines intersect in UTM coordinates.
    Each line parameter is in format [x1, y1, x2, y2] (easting, northing).
    
    Assumes lines form a quadrilateral in order: line1→line2→line3→line4→line1.
    
    Returns a list of four points [(x,y), (x,y), (x,y), (x,y)] in order:
    [intersection of line1&line2, line2&line3, line3&line4, line4&line1]
    Returns None if any pair of lines are parallel.
    """
    # Calculate the four intersection points
    p1 = _line_intersection(line1, line2)
    p2 = _line_intersection(line2, line3)
    p3 = _line_intersection(line3, line4)
    p4 = _line_intersection(line4, line1)
    
    # Check if any intersection failed
    if None in [p1, p2, p3, p4]:
        return None
    
    return [p1, p2, p3, p4]

def _create_field_plan(params):
    origin_x, origin_y = params['origin'].x(), params['origin'].y()
    grid_origin_x, grid_origin_y = params['margin'][0], params['margin'][1]
    bearing = params['bearing_radians']
    left = params['is_left']
    grid_gap = params['grid_gap']
    grid_rows = [int(r) for r in params['rows']]
    grid_cols = [int(c) for c in params['columns']]
    one = params['1']
    two = params['2']
    three = params['3']
    four = params['4'] # grid plot length
    five = params['5'] # grid alley
    subplots = params['subplots']

    polygons = []
    grid_ids = []
    column_ids = []
    row_ids = []
    plot_ids = []

    grid_gap = grid_gap + [0] # Add a zero so last iteration has final grid gap value

    # Iterate over each grid
    for b, (cols, rows, pl, a, bg) in enumerate(zip(grid_cols, grid_rows, four, five, grid_gap)):
        for row in range(rows):
            for col in range(cols):
                for p in range(subplots):
                    # Bottom left                                                       
                    bl_x = grid_origin_x
                    bl_x += col * ((subplots * one) + ((subplots-1) * two) + three)
                    bl_x += p * (one + two)

                    bl_y = grid_origin_y
                    bl_y += row * (pl + a)    

                    # Bottom right                                                  
                    br_x = bl_x + one
                    br_y = bl_y                                                                                             

                    # Top left
                    tl_x = bl_x
                    tl_y = bl_y + pl

                    # Top right
                    tr_x = bl_x + one
                    tr_y = bl_y + pl

                    # Must be in clockwise order
                    polygon = []
                    for x, y in [(bl_x, bl_y), (tl_x, tl_y), (tr_x, tr_y), (br_x, br_y)]:
                        x = x if left else -x
                        rotated_x = x * math.cos(bearing) - y * math.sin(bearing)
                        rotated_y = x * math.sin(bearing) + y * math.cos(bearing)

                        x = origin_x + rotated_x
                        y = origin_y - rotated_y

                        polygon.append((x, y))
                    
                    polygons.append(polygon)
                    row_ids.append(int(row+1))
                    column_ids.append(int(col+1))
                    plot_ids.append(int(p+1))
                    grid_ids.append(int(b+1))

        grid_origin_y += ((rows * pl) + ((rows - 1) * a) + bg)

    return polygons, grid_ids, column_ids, row_ids, plot_ids

def _calculate_lines(features, ppc, boundary_margin, bearing):
    # each feat dict {'polygon':[(x, y), (x, y), (x, y), (x, y)] (in form bottom left, top left, top right, bottom right), etc.}

    # Calculate guidance lines
    cols = defaultdict(list)
    for f in features:
        cols[f['col']].append(f)
    
    gl_coords = []
    gl_cols = []
    for col_id, col in cols.items():
        # calculate bounding box for row then find line that intersects
        grids = [f['grid'] for f in col]
        max_grid_rows = [f for f in col if f['grid'] == max(grids)]
        min_grid_rows = [f for f in col if f['grid'] == min(grids)]
        max_row = [f for f in max_grid_rows if f['row'] == max([f['row'] for f in max_grid_rows])]
        min_row = [f for f in min_grid_rows if f['row'] == min([f['row'] for f in min_grid_rows])]

        bl = [f['polygon'][0] for f in min_row if f['plot'] == 1][0]       # the lowest row, the first shape's bl coord
        br = [f['polygon'][3] for f in min_row if f['plot'] == ppc][0]       # the lowest row, the last shape's br coord
        tl = [f['polygon'][1] for f in max_row if f['plot'] == 1][0]       # the highest row, the first shapes tl coord
        tr = [f['polygon'][2] for f in max_row if f['plot'] == ppc][0]       # the highest row, the last shapes tr coord

        x1, y1 = (bl[0] + br[0]) / 2, (bl[1] + br[1]) / 2
        x2, y2 = (tl[0] + tr[0]) / 2, (tl[1] + tr[1]) / 2

        # Create a 1 meter buffer beyond the edges of the guidance lines
        dx = x2 - x1
        dy = y2 - y1
        
        # Calculate length of the vector
        length = math.sqrt(dx*dx + dy*dy)
        
        # Normalize the direction vector
        if length > 0:
            ux = dx / length
            uy = dy / length
        else:
            ux, uy = 0, 0
        
        # Extend by 1 unit on each side
        x1_extended = x1 - ux
        y1_extended = y1 - uy
        x2_extended = x2 + ux
        y2_extended = y2 + uy

        gl_coords.append([x1_extended, y1_extended, x2_extended, y2_extended])
        gl_cols.append(col_id)

    # Split features into grids
    grids = defaultdict(list)
    for f in features:
        grids[f['grid']].append(f)

    # Calculate alley lines and grid boundaries
    # Something wrong with the logic to find the edge boundaries for both alleys lines and grid boundaries
    al_coords = []
    al_rows = []
    al_grid = []

    bl_coords = []
    bl_grid = []

    for grid_id, grid in grids.items():
        rows = defaultdict(list)
        for f in grid:
            rows[f['row']].append(f)
        
        row_keys = sorted(list(rows.keys()), key=int)
        for rk1, rk2 in zip(row_keys, row_keys[1:]):
            # calculate bounding box of the alley between rows within a grid
            row1 = rows[rk1]
            row2 = rows[rk2]

            cols_row1 = [f['col'] for f in row1]
            # feedback.pushInfo(f'{rk1}: {len(row1)}, {len(cols_row1)}, {max(cols_row1)}, {min(cols_row1)} {rk2}: {len(row2)}')
            min_col_row1 = [f for f in row1 if f['col'] == min(cols_row1)]
            max_col_row1 = [f for f in row1 if f['col'] == max(cols_row1)]

            cols_row2 = [f['col'] for f in row2]
            min_col_row2 = [f for f in row2 if f['col'] == min(cols_row2)]
            max_col_row2 = [f for f in row2 if f['col'] == max(cols_row2)]

            bl = [f['polygon'][1] for f in min_col_row1 if f['plot'] == 1][0]  # The shape in the 1st row first col, the first plot, and the 1st (tl) coord
            br = [f['polygon'][2] for f in max_col_row1 if f['plot'] == ppc][0]  # The shape in the 1st row last col, the last plot, and the 2nd (tr) coord
            tl = [f['polygon'][0] for f in min_col_row2 if f['plot'] == 1][0]  # The shape in the 2nd row first col, the first plot, and the 0th (bl) coord
            tr = [f['polygon'][3] for f in max_col_row2 if f['plot'] == ppc][0]  # The shape in the 2nd row last col, the last plot, and the 3rd (br) coord

            x1, y1 = (bl[0] + tl[0]) / 2, (bl[1] + tl[1]) / 2
            x2, y2 = (br[0] + tr[0]) / 2, (br[1] + tr[1]) / 2

            # x1, y1 = bl[0], bl[1]
            # x2, y2 = tr[0], tr[1]

            al_coords.append([x1, y1, x2, y2])
            al_rows.append(rk1)
            al_grid.append(grid_id)

        # Calculate bounding box of grid - change this so the grid boundaries are for the widest row, not the upper and lower ones
        row1 = rows[min(rows.keys())]
        row2 = rows[max(rows.keys())]

        # Find top and bottom boundaries       
        cols_row1 = [f['col'] for f in row1]
        min_col_row1 = [f for f in row1 if f['col'] == min(cols_row1)]
        max_col_row1 = [f for f in row1 if f['col'] == max(cols_row1)]

        cols_row2 = [f['col'] for f in row2]
        min_col_row2 = [f for f in row2 if f['col'] == min(cols_row2)]
        max_col_row2 = [f for f in row2 if f['col'] == max(cols_row2)]

        lower_l = [f['polygon'][0] for f in min_col_row1 if f['plot'] == 1][0]      # the first rows min column, the first shapes bl coord
        lower_r = [f['polygon'][3] for f in max_col_row1 if f['plot'] == ppc][0]      # the first rows max column, the last shapes br coord
        upper_l = [f['polygon'][1] for f in min_col_row2 if f['plot'] == 1][0]      # the last rows min column, the first shapes tl coord
        upper_r = [f['polygon'][2] for f in max_col_row2 if f['plot'] == ppc][0]         # the last rows max column, the last shapes tr coord

        # Find left and right boundaries
        wide_row_id = max(rows.keys(), key=lambda x: len(rows[x]))
        wide_row = rows[wide_row_id]
        wide_row_cols = [f['col'] for f in wide_row]
        
        wide_row_left = [f['polygon'] for f in wide_row if f['plot'] == 1 and f['col'] == min(wide_row_cols)][0]
        wide_row_right = [f['polygon'] for f in wide_row if f['plot'] == ppc and f['col'] == max(wide_row_cols)][0]

        left_u = wide_row_left[1]
        left_l = wide_row_left[0]
        right_u = wide_row_right[2]
        right_l = wide_row_right[3]

        top = [*upper_l, *upper_r]
        bottom = [*lower_l, *lower_r]
        left = [*left_u, *left_l]
        right = [*right_u, *right_l]
        
        tr, br, bl, tl = _four_lines_intersect(top, right, bottom, left)

        # adjust for margins
        x_margin = boundary_margin * math.sin(bearing)
        y_margin = boundary_margin * math.cos(bearing)
        tr, tl = (tr[0] - x_margin, tr[1] - y_margin), (tl[0] - x_margin, tl[1] - y_margin)
        br, bl = (br[0] + x_margin, br[1] + y_margin), (bl[0] + x_margin, bl[1] + y_margin)

        b1 = [*bl, *br]
        b2 = [*tl, *tr]

        bl_coords.append(b1)
        bl_grid.append(grid_id)

        bl_coords.append(b2)
        bl_grid.append(grid_id)

    return gl_coords, gl_cols, al_coords, al_rows, al_grid, bl_coords, bl_grid
        
def _get_board_ids(value, grid_size):
    grid_index = value // grid_size
    start = grid_index * grid_size
    return list(range(start, start + grid_size))

