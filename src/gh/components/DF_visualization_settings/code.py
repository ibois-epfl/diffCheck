#! python3

import System
import typing
import Rhino
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper as gh
from Grasshopper import Instances
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

from diffCheck import df_visualization


def add_str_valuelist(self,
    values_list: typing.List[str],
    nickname: str,
    indx: int,
    X_param_coord: float,
    Y_param_coord: float,
    X_offset: int=87
    ) -> None:
    """
        Adds a value list of string values to the component input

        :param values_list: a list of string values to add to the value list
        :param nickname: the nickname of the value list
        :param indx: the index of the input parameter
        :param X_param_coord: the x coordinate of the input parameter
        :param Y_param_coord: the y coordinate of the input parameter
        :param X_offset: the offset of the value list from the input parameter
    """
    param = ghenv.Component.Params.Input[indx]  # noqa: F821
    if param.SourceCount == 0:
        valuelist = gh.Kernel.Special.GH_ValueList()
        valuelist.NickName = nickname
        valuelist.Description = "Select the value to use with DFVizSettings"
        selected = valuelist.FirstSelectedItem
        valuelist.ListItems.Clear()
        for v in values_list:
            vli = gh.Kernel.Special.GH_ValueListItem(str(v),str('"' + v + '"'))
            valuelist.ListItems.Add(vli)
        if selected in values_list:
            valuelist.SelectItem(values_list.index(selected))
        valuelist.CreateAttributes()
        valuelist.Attributes.Pivot = System.Drawing.PointF(
            X_param_coord - (valuelist.Attributes.Bounds.Width) - X_offset,
            Y_param_coord - (valuelist.Attributes.Bounds.Height / 2 + 0.1)
            )
        valuelist.Attributes.ExpireLayout()
        gh.Instances.ActiveCanvas.Document.AddObject(valuelist, False)
        ghenv.Component.Params.Input[indx].AddSource(valuelist)  # noqa: F821

def add_slider(self,
    nickname: str,
    indx: int,
    lower_bound: float,
    upper_bound: float,
    default_value: float,
    X_param_coord: float,
    Y_param_coord: float,
    X_offset: int=100
    ) -> None:
    """
        Adds a slider to the component input

        :param nickname: the nickname of the slider
        :param indx: the index of the input parameter
        :param X_param_coord: the x coordinate of the input parameter
        :param Y_param_coord: the y coordinate of the input parameter
        :param X_offset: the offset of the slider from the input parameter
    """
    param = ghenv.Component.Params.Input[indx]  # noqa: F821
    if param.SourceCount == 0:
        slider = gh.Kernel.Special.GH_NumberSlider()
        slider.NickName = nickname
        slider.Description = "Set the value for the threshold"
        slider.Slider.Minimum = System.Decimal(lower_bound)
        slider.Slider.Maximum = System.Decimal(upper_bound)
        slider.Slider.DecimalPlaces = 3
        slider.Slider.SmallChange = System.Decimal(0.001)
        slider.Slider.LargeChange = System.Decimal(0.01)
        slider.Slider.Value = System.Decimal(default_value)
        slider.CreateAttributes()
        slider.Attributes.Pivot = System.Drawing.PointF(
            X_param_coord - (slider.Attributes.Bounds.Width) - X_offset,
            Y_param_coord - (slider.Attributes.Bounds.Height / 2 - 0.1)
            )
        slider.Attributes.ExpireLayout()
        gh.Instances.ActiveCanvas.Document.AddObject(slider, False)
        ghenv.Component.Params.Input[indx].AddSource(slider)  # noqa: F821

def add_plane_object(self,
    nickname: str,
    indx: int,
    X_param_coord: float,
    Y_param_coord: float,
    X_offset: int=75
    ) -> None:
    """
        Adds a plane object to the component input

        :param nickname: the nickname of the plane object
        :param indx: the index of the input parameter
        :param X_param_coord: the x coordinate of the input parameter
        :param Y_param_coord: the y coordinate of the input parameter
        :param X_offset: the offset of the plane object from the input parameter
    """
    param = ghenv.Component.Params.Input[indx]  # noqa: F821
    if param.SourceCount == 0:
        doc = Instances.ActiveCanvas.Document
        if doc:
            plane = gh.Kernel.Parameters.Param_Plane()
            plane.NickName = nickname
            plane.CreateAttributes()
            plane.Attributes.Pivot = System.Drawing.PointF(
                X_param_coord - (plane.Attributes.Bounds.Width) - X_offset,
                Y_param_coord
                )
            plane.Attributes.ExpireLayout()
            doc.AddObject(plane, False)
            ghenv.Component.Params.Input[indx].AddSource(plane)  # noqa: F821


class DFVisualizationSettings(component):
    def __init__(self):
        self.poss_value_types = ["Dist", "MEAN", "RMSE", "MAX", "MIN", "STD"]
        self.poss_palettes = ["Jet", "Rainbow", "RdPu", "Viridis"]

        ghenv.Component.ExpireSolution(True)  # noqa: F821
        ghenv.Component.Attributes.PerformLayout()  # noqa: F821
        params = getattr(ghenv.Component.Params, "Input")  # noqa: F821
        for j in range(len(params)):
            Y_cord = params[j].Attributes.InputGrip.Y
            X_cord = params[j].Attributes.Pivot.X
            input_indx = j
            if "i_value_type" == params[j].NickName:
                add_str_valuelist(
                    ghenv.Component,  # noqa: F821
                    self.poss_value_types,
                    "DF_value_t",
                    input_indx, X_cord, Y_cord)
            if "i_palette" == params[j].NickName:
                add_str_valuelist(
                    ghenv.Component,  # noqa: F821
                    self.poss_palettes,
                    "DF_palette",
                    input_indx, X_cord, Y_cord)
            if "i_legend_height" == params[j].NickName:
                add_slider(
                    ghenv.Component,  # noqa: F821
                    "DF_legend_height",
                    input_indx,
                    0.000, 20.000, 10.000,
                    X_cord, Y_cord)
            if "i_legend_width" == params[j].NickName:
                add_slider(
                    ghenv.Component,  # noqa: F821
                    "DF_legend_width",
                    input_indx,
                    0.000, 2.000, 0.500,
                    X_cord, Y_cord)
            if "i_legend_plane" == params[j].NickName:
                add_plane_object(
                    ghenv.Component,  # noqa: F821
                    "DF_legend_plane",
                    input_indx, X_cord, Y_cord)
            if "i_histogram_scale_factor" == params[j].NickName:
                add_slider(
                    ghenv.Component,  # noqa: F821
                    "DF_histogram_scale_factor",
                    input_indx,
                    0.000, 1.000, 0.01,
                    X_cord, Y_cord)

    def RunScript(self,
        i_value_type: str,
        i_palette: str,
        i_upper_threshold: float,
        i_lower_threshold: float,
        i_legend_height: float,
        i_legend_width: float,
        i_legend_plane: Rhino.Geometry.Plane,
        i_histogram_scale_factor: float,
        i_one_histogram_per_item: bool):

        """
        Compiles all the visualization settings to feed to the visualization component

        :param i_value_type: selected type indicates Which values to display. Possible values: "dist", "RMSE", "MAX", "MIN", "STD"
        :param i_palette: Select a color palette to map the values to. Possible values: "Jet", "Rainbow", "RdPu", "Viridis"
        :param i_upper_threshold: Thresholds the values with a maximum value
        :param i_lower_threshold: Thresholds the values with a minimum value
        :param i_legend_height: the total height of the legend
        :param i_legend_width: the total width of the legend
        :param i_legend_plane: the construction plane of the legend
        :param i_histogram_scale_factor: Scales the height of the histogram with a factor

        :returns o_viz_settings: the results of the comparison all in one object
        """
        # set default values
        if i_value_type is not None:
            if i_value_type not in self.poss_value_types:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Possible values for i_value_type are: dist, MEAN, RMSE, MAX, MIN, STD")  # noqa: F821
                return None
        else:
            i_value_type = "Dist"
        if i_palette is not None:
            if i_palette not in self.poss_palettes:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Possible values for i_palette are: Jet, Rainbow, RdPu, Viridis")  # noqa: F821
                return None
        else:
            i_palette = "Jet"
        if i_legend_height is None:
            i_legend_height = 10
        if i_legend_width is None:
            i_legend_width = 0.5
        if i_legend_plane is None:
            i_legend_plane = Rhino.Geometry.Plane.WorldXY
        if i_histogram_scale_factor is None:
            i_histogram_scale_factor = 0.01
        if i_one_histogram_per_item is None:
            i_one_histogram_per_item = False

        # pack settings
        o_viz_settings = df_visualization.DFVizSettings(i_value_type,
                                                        i_palette,
                                                        i_upper_threshold,
                                                        i_lower_threshold,
                                                        i_legend_height,
                                                        i_legend_width,
                                                        i_legend_plane,
                                                        i_histogram_scale_factor,
                                                        i_one_histogram_per_item)

        return o_viz_settings
