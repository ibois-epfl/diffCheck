#! python3
"""
    This module contains the utility functions to vizualize differences
"""

import Rhino.Geometry as rg
from System.Drawing import Color


class DFVizSettings:
    """
    This class compiles the settings for the vizualization into one object
    """

    def __init__(self, source_valueType, target_valueType, upper_threshold,
                 lower_threshold, palette):

        self.source_valueType = source_valueType
        self.target_valueType = target_valueType

        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.palette = palette


def interpolate_color(color1, color2, t):
    """Interpolate between two colors."""

    r = int(color1.R + (color2.R - color1.R) * t)
    g = int(color1.G + (color2.G - color1.G) * t)
    b = int(color1.B + (color2.B - color1.B) * t)
    return Color.FromArgb(r, g, b)


def value_to_color(value, min_value, max_value):
    """Map a value to a color based on a spectral colormap."""

    if value < min_value:
        value = min_value
    elif value > max_value:
        value = max_value

    # Define the spectral colormap (simplified)
    colormap = [
        Color.FromArgb(0, 0, 255),  # Blue
        Color.FromArgb(0, 255, 255),  # Cyan
        Color.FromArgb(0, 255, 0),  # Green
        Color.FromArgb(255, 255, 0),  # Yellow
        Color.FromArgb(255, 0, 0),  # Red
    ]

    # Normalize the value within the range
    if min_value == max_value:
        t = 0.5
    else:
        t = (value - min_value) / (max_value - min_value)

    # Determine the segment in the colormap
    n = len(colormap)-1
    idx = int(t * n)
    if idx >= n:
        idx = n - 1
    t = (t * n) - idx

    # Interpolate between the two colors
    color1 = colormap[idx]
    color2 = colormap[idx + 1]

    return interpolate_color(color1, color2, t)


def color_pcd(pcd, values, min_value, max_values):

    for i, p in enumerate(pcd):
        mapped_color = value_to_color(values[i], min_value, max_values)
        p.Color = mapped_color
    return pcd


def create_legend(min_value, max_value, steps=10, base_point=rg.Point3d(0, 0, 0),
                  width=0.5, height=1, spacing=0):
    """
    Create a legend in Rhino with colored hatches and text labels.

    Parameters:
    min_value (float): Minimum value for the legend.
    max_value (float): Maximum value for the legend.
    steps (int): Number of steps in the legend.
    base_point (rg.Point3d): The base point where the legend starts.
    width (float): Width of each rectangle.
    height (float): Height of each rectangle.
    spacing (float): Spacing between rectangles.
    """
    x, y, z = base_point.X, base_point.Y, base_point.Z

    legend_geometry = []

    for i in range(steps+1):

        value = min_value + (max_value - min_value) * i / steps
        color = value_to_color(value, min_value, max_value)

        if i > 0:
            mesh = rg.Mesh()
            for pt in rect_pts:
                mesh.Vertices.Add(pt)
            # color mesh
            mesh.Faces.AddFace(0, 1, 2, 3)
            
            mesh.VertexColors.Add(previous_color.R, previous_color.G, previous_color.B)
            mesh.VertexColors.Add(previous_color.R, previous_color.G, previous_color.B)
            mesh.VertexColors.Add(color.R, color.G, color.B)
            mesh.VertexColors.Add(color.R, color.G, color.B)

            polyline = rg.Polyline(rect_pts)

            legend_geometry.append(mesh)
            legend_geometry.append(polyline.ToPolylineCurve())

        text_pt = rg.Point3d(x + 1.25 * width + spacing, y + i * (height + spacing) + height / 10, z)
        text_entity = rg.TextEntity()
        text_entity.Plane = rg.Plane(text_pt, rg.Vector3d.ZAxis)
        text_entity.Text = f"{value:.2f}"
        text_entity.TextHeight = height / 5
        legend_geometry.append(text_entity)

        rect_pts = [
            rg.Point3d(x, y + i * (height + spacing), z),
            rg.Point3d(x + width, y + i * (height + spacing), z),
            rg.Point3d(x + width, y + (i + 1) * height + i * spacing, z),
            rg.Point3d(x, y + (i + 1) * height + i * spacing, z),
        ]

        previous_color = color

    return legend_geometry


def create_histogram(values, min_value, max_value, steps=100, base_point=rg.Point3d(0, 0, 0), height=0.1, spacing=0):
    """
    Create a histogram in Rhino with a polyline representing value frequencies.

    Parameters:
    values (list of float): List of values to calculate the histogram.
    min_value (float): Minimum value for the histogram.
    max_value (float): Maximum value for the histogram.
    steps (int): Number of steps in the histogram.
    base_point (rg.Point3d): The base point where the histogram starts.
    height (float): Height of each bin in the histogram.
    spacing (float): Spacing between bins.
    """
    histogram_geometry = []

    # Calculate the size of each bin
    bin_size = (max_value - min_value) / steps

    # Initialize the frequency counts for each bin
    frequencies = [0] * (steps + 1)

    # Count the frequencies of values in each bin
    for value in values:
        if value < min_value:
            value = min_value
        elif value > max_value:
            value = max_value
        bin_index = (value - min_value) // bin_size
        bin_index = int(bin_index)
        frequencies[bin_index] += 1

    x, y, z = base_point.X, base_point.Y, base_point.Z

    # Create points for the polyline representing the histogram
    points = []
    for i in range(steps+1):

        bar_height = frequencies[i] * 0.01 * height
        print(bar_height)
        points.append(rg.Point3d(x - bar_height - 0.15 , y + i * (spacing + height), z))

    # Create the polyline and add it to the histogram geometry
    polyline = rg.Curve.CreateInterpolatedCurve(points, 1)
    histogram_geometry.append(polyline)

    return histogram_geometry
