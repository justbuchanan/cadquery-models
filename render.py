import cadquery as cq
from cadquery import exporters
import sys

result = cq.Workplane("XY" ).box(3, 3, 0.5).edges("|Z").fillet(0.125)

with open(sys.argv[1], 'w') as f:
    exporters.exportShape(result, exporters.ExportTypes.STL, f)
