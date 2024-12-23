#! python3

import System

import Rhino
from ghpythonlib.componentbase import executingcomponent as component
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


from diffCheck.diffcheck_bindings import dfb_segmentation
from diffCheck.diffcheck_bindings import dfb_geometry

from diffCheck import df_cvt_bindings



class DFCADSegmentator(component):
    def RunScript(self,
        i_clouds: System.Collections.Generic.IList[Rhino.Geometry.PointCloud],
        i_assembly,
        i_angle_threshold: float = 0.1,
        i_association_threshold: float = 0.1) -> Rhino.Geometry.PointCloud:

        if i_clouds is None or i_assembly is None:
            self.AddRuntimeMessage(RML.Warning, "Please provide a cloud and an assembly to segment.")
            return None
        if i_angle_threshold is None:
            i_angle_threshold = 0.1
        if i_association_threshold is None:
            i_association_threshold = 0.1

        o_clusters = []
        df_clusters = []
        # we make a deepcopy of the input clouds
        df_clouds = [df_cvt_bindings.cvt_rhcloud_2_dfcloud(cloud.Duplicate()) for cloud in i_clouds]

        df_beams = i_assembly.beams
        df_beams_meshes = []
        rh_beams_meshes = []

        for df_b in df_beams:
            rh_b_mesh_faces = [df_b_f.to_mesh() for df_b_f in df_b.side_faces]
            df_b_mesh_faces = [df_cvt_bindings.cvt_rhmesh_2_dfmesh(rh_b_mesh_face) for rh_b_mesh_face in rh_b_mesh_faces]
            df_beams_meshes.append(df_b_mesh_faces)
            rh_beams_meshes.append(rh_b_mesh_faces)

            # different association depending on the type of beam
            df_asssociated_cluster_faces = dfb_segmentation.DFSegmentation.associate_clusters(
                is_roundwood=df_b.is_roundwood,
                reference_mesh=df_b_mesh_faces,
                unassociated_clusters=df_clouds,
                angle_threshold=i_angle_threshold,
                association_threshold=i_association_threshold
            )

            df_asssociated_cluster = dfb_geometry.DFPointCloud()
            for df_associated_face in df_asssociated_cluster_faces:
                df_asssociated_cluster.add_points(df_associated_face)

            dfb_segmentation.DFSegmentation.clean_unassociated_clusters(
                is_roundwood=df_b.is_roundwood,
                unassociated_clusters=df_clouds,
                associated_clusters=[df_asssociated_cluster],
                reference_mesh=[df_b_mesh_faces],
                angle_threshold=i_angle_threshold,
                association_threshold=i_association_threshold
            )

            df_clusters.append(df_asssociated_cluster)

        o_clusters = [df_cvt_bindings.cvt_dfcloud_2_rhcloud(cluster) for cluster in df_clusters]

        for o_cluster in o_clusters:
            if not o_cluster.IsValid:
                o_cluster = None
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Some beams could not be segmented and were replaced by 'None'")  # noqa: F821


        return o_clusters
