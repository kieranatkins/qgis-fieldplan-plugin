ORIGIN = "Origin (northing, easting) - The initial point from which the field plan will be built, following the bearing. Refer to diagram for visualisation."
BEARING = "Bearing (degrees) - The direction in which the field plan will be built, starting at the origin. Refer to diagram for visualisation."
FIELD_BOUNDARY = "Field boundary (vector layer) - An optional vector layer where any generated shapes that lie outside of the vector shapes will be automatically deleted and the ID numbering system will ignore."
SNAP_TO_SHAPE = "Snap to shape (vector layer) - An optional vector layer where the origin will update to the closest point of the closest polygon's edge."
DIRECTION = "Direction - (left/right) - Defines which direction to build the field plan related to the bearing line."
MARGIN = "Margin (meters) - Defines two values as a spacing between the origin and the beggining of the field plan. X refers to the distance perpendicular to the bearing line, Y refers to the distance parallel to the bearing line. TODO Include in diagram."
GRID_NUMBER = "Grid number (ineteger) - The number of grids to be included in the field plan. Each grid can have individually addressed rows, columns and values for dimension 4 and 5 using comma-separated values (CSV)."
GRID_GAP = "Grid gap (metres - CSV) - The distance between each grid. Can input a single value or n-1 comma-separated values (CSV) where n is the number of grids."
SUBPLOTS = "Subplots (integer) - The number of subplots within a single plot. Useful for when sowing occurs in groups."
ROWS = "Rows (integer - CSV) - The number of plots in the dimension parallel to the bearing line. Can input a single value or n comma-separated values (CSV) where n is the number of grids."
COLUMNS = "Columns (integer - CSV) - The number of plots in the dimension perpendicular to the bearing line. Can input a single value or n comma-separated values (CSV) where n is the number of grids."
ONE = "1 (metres) - The width of each plot, or subplots when subplots > 1."
TWO = "2 (metres) - The distance between each subplots. Does nothing when subplots = 1."
THREE = "3 (metres) - The distance between each plot perpendicular to the bearing line."
FOUR = "4 (metres - CSV) - The length of each plot. Can input a single value or n comma-separated values (CSV) where n is the number of grids."
FIVE = "5 (metres - CSV) - The distance between each plot parallel to the bearing line. Can input a single value or n comma-separated values (CSV) where n is the number of grids."
COLUMN_SERPENTINE_ID = "Column serpentine ID - Reverses the direction of ID counting of alternate columns."
SUBPLOT_SERPENTINE_ID = "Subplot serpentine ID - Reverses the direction of ID counting within alternate subplots. Does nothing when subplots = 1."
REVERSE_SUBPLOT_ID = "Reverse subplot ID - Flips which subplots have reverse ID counting. Meaningless when subplots = 1 or when subplot serpentine ID is False."
RETURN_GUIDANCE_LINES = "Return guidance lines - Returns straight centre lines through each column across grids. Useful for GPS-guided equipment. Note: Lines go 1 metre beyond the ends of the edge grids"
RETURN_ALLEY_LINES = "Return alley lines - Returns straight centre lines through each row. Useful for GPS-guided equipment."
RETURN_GRID_BOUNDARIES = "Return grid boundaries - Returns lines along the boundary of the upper and lower rows of each grid."
GRID_BOUNDARY_MARGIN = "Grid boundary margin (metres) - Adds a fixed distance between end of grid and beginning of grid boundary lines."

HELP_DICT = {
    "origin":ORIGIN,
    "bearing":BEARING,
    "field_boundary":FIELD_BOUNDARY,
    "snap":SNAP_TO_SHAPE,
    "direction":DIRECTION,
    "margin":MARGIN,
    "grid_number":GRID_NUMBER,
    "grid_gap":GRID_GAP,
    "subplots":SUBPLOTS,
    "rows":ROWS,
    "columns":COLUMNS,
    "1":ONE,
    "2":TWO,
    "3":THREE,
    "4":FOUR,
    "5":FIVE,
    "column_serpentine_id":COLUMN_SERPENTINE_ID,
    "subplot_serpentine_id":SUBPLOT_SERPENTINE_ID,
    "reverse_subplot_id":REVERSE_SUBPLOT_ID,
    "return_guidance_lines":RETURN_GUIDANCE_LINES,
    "return_alley_lines":RETURN_ALLEY_LINES,
    "return_grid_boundaries":RETURN_GRID_BOUNDARIES,
    "grid_boundary_margin":GRID_BOUNDARY_MARGIN
}