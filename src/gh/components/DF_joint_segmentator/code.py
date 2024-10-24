"""Extracts the joints from a point cloud."""
#! python3

import System
import math

import Rhino
import ghpythonlib.treehelpers

from diffCheck import diffcheck_bindings
from diffCheck import df_cvt_bindings as df_cvt

from ghpythonlib.componentbase import executingcomponent as component


ABSTOL = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance

class DFJointSegmentator(component):
    def __init__(self):
        super(DFJointSegmentator, self).__init__()
    def RunScript(self,
            i_clusters: System.Collections.Generic.List[Rhino.Geometry.PointCloud],
            i_assembly,
            i_angle_threshold: float,
            i_distance_threshold: float,
            i_correspondence_distance: float,
            i_joint_displacement_tolerance: float):

        if i_clusters is None or i_assembly is None:
            return None
        if i_angle_threshold is None:
            i_angle_threshold = 0.1
        if i_distance_threshold is None:
            i_distance_threshold = 0.1
        if i_correspondence_distance is None:
            i_correspondence_distance = 0.005
        if i_joint_displacement_tolerance is None:
            i_joint_displacement_tolerance =0.05
        if len(i_clusters) == 0:
            raise ValueError("No clusters given.")
        if not isinstance(i_clusters[0], Rhino.Geometry.PointCloud):
            raise ValueError("The input clusters must be PointClouds.")

        # get number of joints
        n_joints = i_assembly.total_number_joints

        # prepping the reference meshes
        df_joints = [[] for _ in range(n_joints)]
        rh_joints = [[] for _ in range(n_joints)]
        for joint in i_assembly.all_joints:
            for face in joint.faces:
                face = face.to_mesh()
                face.Subdivide()
                face.Faces.ConvertQuadsToTriangles()
                rh_joints[joint.id].append(face)
                df_joints[joint.id].append(df_cvt.cvt_rhmesh_2_dfmesh(face))
        o_reference_point_clouds = []
        o_joint_faces_segments = []
        df_cloud_clusters = [df_cvt.cvt_rhcloud_2_dfcloud(cluster) for cluster in i_clusters]
        df_joint_clouds = []
        o_joint_segments = []

        # compute the center of the joints
        rh_joint_centers = []
        for rh_joint in rh_joints:
            vertices = []
            for face in rh_joint:
                for vertice in face.Vertices:
                    vertices.append(Rhino.Geometry.Point3d(vertice.X, vertice.Y, vertice.Z))
            joint_center = Rhino.Geometry.BoundingBox(vertices).Center
            rh_joint_centers.append([joint_center.X, joint_center.Y, joint_center.Z])

        # for each joint, find the corresponding faces, store them as such but also merge them, generate a reference point cloud, and register the merged clusters to the reference point cloud
        for i, df_joint in enumerate(df_joints):
            rh_joint_faces_segments = []
            reference_joint_center = rh_joint_centers[i]

            # create the reference point cloud
            ref_df_joint_cloud = diffcheck_bindings.dfb_geometry.DFPointCloud()
            for face in df_joint:
                ref_face_cloud = face.sample_points_uniformly(1000)
                ref_df_joint_cloud.add_points(ref_face_cloud)
            o_reference_point_clouds.append(df_cvt.cvt_dfcloud_2_rhcloud(ref_df_joint_cloud))

            # find the corresponding clusters and merge them
            df_joint_cloud = diffcheck_bindings.dfb_geometry.DFPointCloud()
            df_joint_face_segments = diffcheck_bindings.dfb_segmentation.DFSegmentation.associate_clusters(False, df_joint, df_cloud_clusters, i_angle_threshold, i_distance_threshold)
            for df_joint_face_segment in df_joint_face_segments:
                df_joint_cloud.add_points(df_joint_face_segment)

            # get the center of the segment
            if len(df_joint_cloud.points)>0:
                df_cloud_bb_points = df_joint_cloud.get_tight_bounding_box()
                x, y, z = 0, 0, 0
                for i in range(len(df_cloud_bb_points)):
                    x += df_cloud_bb_points[i][0]
                    y += df_cloud_bb_points[i][1]
                    z += df_cloud_bb_points[i][2]
                x = x/8 # because a bb has 8 corners
                y = y/8
                z = z/8
                segment_center = [x, y, z]
                segment_dist_to_ref = math.sqrt(math.pow(segment_center[0]-reference_joint_center[0], 2)
                                                + math.pow(segment_center[1]-reference_joint_center[1], 2)
                                                + math.pow(segment_center[2]-reference_joint_center[2], 2))
                if segment_dist_to_ref > i_joint_displacement_tolerance:
                    rh_joint_cloud = df_cvt.cvt_dfcloud_2_rhcloud(df_joint_cloud)
                    rh_joint_cloud.SetUserString("df_sanity_scan_check", "1")
                    o_joint_segments.append(rh_joint_cloud)
                else:
                    rh_joint_cloud = df_cvt.cvt_dfcloud_2_rhcloud(df_joint_cloud)
                    rh_joint_cloud.SetUserString("df_sanity_scan_check", "0")
                    o_joint_segments.append(rh_joint_cloud)
            else:
                rh_joint_cloud = df_cvt.cvt_dfcloud_2_rhcloud(df_joint_cloud)
                rh_joint_cloud.SetUserString("df_sanity_scan_check", "2")
                o_joint_segments.append(rh_joint_cloud)

            # register the joint faces to the reference point cloud
            transform = diffcheck_bindings.dfb_registrations.DFRefinedRegistration.O3DICP(df_joint_cloud, ref_df_joint_cloud, max_correspondence_distance = i_correspondence_distance)
            for df_joint_face_segment in df_joint_face_segments:
                df_joint_face_segment.apply_transformation(transform)
                rh_joint_faces_segments.append(df_cvt.cvt_dfcloud_2_rhcloud(df_joint_face_segment))
            df_joint_clouds.append(df_joint_cloud)
            o_joint_faces_segments.append(rh_joint_faces_segments)

        for rh_joint_faces, rh_joint in zip(o_joint_faces_segments, o_joint_segments):
            for joint_face in rh_joint_faces:
                joint_face.SetUserString("df_sanity_scan_check", rh_joint.GetUserString("df_sanity_scan_check"))

        o_gh_tree_joint_faces_segments = ghpythonlib.treehelpers.list_to_tree(o_joint_faces_segments)

        return o_gh_tree_joint_faces_segments, o_joint_segments, o_reference_point_clouds
