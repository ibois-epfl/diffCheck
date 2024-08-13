#! python3

import Rhino

import diffCheck
from diffCheck import diffcheck_bindings
from diffCheck import df_cvt_bindings as df_cvt
import diffCheck.df_util

from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML
from ghpythonlib.componentbase import executingcomponent as component

import typing

ABSTOL = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance

class DFJointSegmentator(component):
    # def __init__(self):
    #     super(DFJointSegmentator, self).__init__()
    def RunScript(self, 
                  i_clusters: typing.List[Rhino.Geometry.PointCloud], 
                  i_assembly: diffCheck.df_geometries.DFAssembly,
                  i_angle_threshold: float,
                  i_distance_threshold: float):
        """
        Amongst clusters, associates the clusters to the individual joints, 
        creates a reference point cloud for each joint, 
        and returns the joint segments, the reference point clouds, and the ICP transformations from the first to the second.

        :param i_clusters: The clusters to be associated to the joints.
        :param i_assembly: The DFAssembly containing the joints we want to segment.
        :param i_angle_threshold: The angle threshold for the association of the clusters to the joints.
        :param i_distance_threshold: The distance threshold for the association of the clusters to the joints.
        """
        if i_angle_threshold is None : i_angle_threshold = 0.1
        if i_distance_threshold is None : i_distance_threshold = 0.1
        
        if len(i_clusters) == 0:
            raise ValueError("No clusters given.")

        if not isinstance(i_clusters[0], Rhino.Geometry.PointCloud):
            raise ValueError("The input clusters must be PointClouds.")
        
        all_joints = i_assembly.all_joints
        if not isinstance(all_joints[0].faces[0].to_mesh(), Rhino.Geometry.Mesh):
            raise ValueError("The input joints must be convertible to Meshes.")
            
        # get number of joints
        n_joints = max([joint.id for joint in all_joints]) + 1

        # prepping the reference meshes
        joints = [[] for _ in range(n_joints)]
        for joint in all_joints:
            for face in joint.faces:
                face = face.to_mesh()
                face.Subdivide()
                face.Faces.ConvertQuadsToTriangles()
                joints[joint.id].append(df_cvt.cvt_rhmesh_2_dfmesh(face))

        joint_clouds = []
        transforms = []
        joint_segments = []
        df_clouds = [df_cvt.cvt_rhcloud_2_dfcloud(cluster) for cluster in i_clusters]

        # for each joint, find the corresponding clusters and merge them, generate a reference point cloud, and register the merged clusters to the reference point cloud
        for joint in joints:
            # create the reference point cloud
            joint_cloud = diffcheck_bindings.dfb_geometry.DFPointCloud()

            for face in joint:
                face_cloud = face.sample_points_uniformly(1000)
                joint_cloud.add_points(face_cloud)

            joint_clouds.append(df_cvt.cvt_dfcloud_2_rhcloud(joint_cloud))

            # find the corresponding clusters and merge them
            segment = diffcheck_bindings.dfb_segmentation.DFSegmentation.associate_clusters(joint, df_clouds, i_angle_threshold, i_distance_threshold)
            diffcheck_bindings.dfb_segmentation.DFSegmentation.clean_unassociated_clusters(df_clouds, [segment], [joint], i_angle_threshold, i_distance_threshold)
            
            # register the merged clusters to the reference point cloud
            registration = diffcheck_bindings.dfb_registrations.DFRefinedRegistration.O3DICP(segment, joint_cloud)
            res = registration.transformation_matrix
            transforms.append(df_cvt.cvt_ndarray_2_rh_transform(res))
            joint_segments.append(df_cvt.cvt_dfcloud_2_rhcloud(segment))
        
        o_joint_segments = []
        o_transforms = []
        o_reference_point_clouds = []
        for  joint_segment, transform, _joint_cloud in zip(joint_segments, transforms, joint_clouds):
            if joint_segment.IsValid:
                o_joint_segments.append(joint_segment)
                o_transforms.append(transform)
                o_reference_point_clouds.append(_joint_cloud)
            else:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Some joints could not be segmented and were ignored.")

        return o_joint_segments, o_transforms, o_reference_point_clouds

# if __name__ == "__main__":
#     comp = DFJointSegmentator()
#     o_joint_segments, o_transforms, o_reference_point_clouds = comp.RunScript(i_clusters, i_assembly, i_angle_threshold, i_distance_threshold)
#     for i in range(len(o_joint_segments)):
#         o_joint_segments[i].Transform(o_transforms[i])
