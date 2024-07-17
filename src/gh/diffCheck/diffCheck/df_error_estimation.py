#! python3
"""
    This module contains the utility functions to compute the difference between source and target
"""

import numpy as np
from diffCheck import diffcheck_bindings
import Rhino.Geometry as rg


def cloud_2_cloud_comparison(source_list, target_list):
    """
        Compute the Euclidean distance for every point of a source pcd to its
        closest point on a target pointcloud
    """
    results = DFVizResults()
    for source, target in zip(source_list, target_list):
        distances = cloud_2_cloud_distance(source, target)
        results.add(source, target, distances)

    return results


def cloud_2_cloud_distance(source, target):
    """
        Compute the Euclidean distance for every point of a source pcd to its
        closest point on a target pointcloud
    """

    return np.asarray(source.compute_distance(target))


def cloud_2_rhino_mesh_comparison(cloud_source_list, rhino_mesh_target_list, signed_flag, swap):
    """
        Compute the Euclidean distance for every point of a source pcd to its
        closest point on a target pointcloud
    """
    results = DFVizResults()

    for source, target in zip(cloud_source_list, rhino_mesh_target_list):
        if swap:
            # this mean we want to vizualize the result on the target mesh
            distances = rhino_mesh_2_cloud_distance(target, source, signed_flag)
        else:
            # this means we want to vizualize the result on the source pcd
            distances = cloud_2_rhino_mesh_distance(source, target, signed_flag)

        if swap:
            results.add(target, source, distances)
        else:
            results.add(source, target, distances)

    return results


# def cloud_2_mesh_distance(source, target, signed=False):
#     """
#         Calculate the distance between every point of a source pcd to its closest point on a target DFMesh
#     """

#     # for every point on the PCD compute the point_2_mesh_distance
#     if signed:
#         distances = np.asarray(target.compute_distance(source, is_abs=False))
#     else:
#         distances = np.asarray(target.compute_distance(source, is_abs=True))

#     return distances

def rhino_mesh_2_cloud_distance(source, target, signed=False):
    """
        Calculate the distance between every vertex of a Rhino Mesh to its closest point on a PCD
    """
    #make a Df point cloud containing all the vertices of the source rhino mesh
    df_pcd_from_mesh_vertices = diffcheck_bindings.dfb_geometry.DFPointCloud()
    df_pcd_from_mesh_vertices.points = [[pt.X, pt.Y, pt.Z] for pt in source.Vertices]
    #calculate the distances
    distances = np.asarray(df_pcd_from_mesh_vertices.compute_distance(target))

    if signed:
        for p in target.points:

            rhp = rg.Point3d(p[0], p[1], p[2])
            closest_meshPoint = source.ClosestMeshPoint(rhp, 1000)
            closest_point = closest_meshPoint.Point
            distance = rhp.DistanceTo(closest_point)
            # Calculate the direction from target to source
            direction = rhp - closest_point
            # Calculate the signed distance
            normal = source.NormalAt(closest_meshPoint)
            dot_product = direction * normal
            if dot_product < 0:
                distance = - distance

    return np.asarray(distances)


def cloud_2_rhino_mesh_distance(source, target, signed=False):
    """
        Calculate the distance between every point of a source pcd to its closest point on a target Rhino Mesh
    """

    #for every point on the point cloud find distance to mesh
    distances = []

    for p in source.points:

        rhp = rg.Point3d(p[0], p[1], p[2])
        closest_meshPoint = target.ClosestMeshPoint(rhp, 1000)
        closest_point = closest_meshPoint.Point
        distance = rhp.DistanceTo(closest_point)

        if signed:
            # Calculate the direction from target to source
            direction = rhp - closest_point
            # Calculate the signed distance
            normal = target.NormalAt(closest_meshPoint)
            dot_product = direction * normal
            if dot_product < 0:
                distance = -distance

        distances.append(distance)

    return np.asarray(distances)


class DFVizResults:
    """
    This class compiles the resluts of the error estimation into one object
    """

    def __init__(self):

        self.source = []
        self.target = []

        self.distances_mse = []
        self.distances_max_deviation = []
        self.distances_min_deviation = []
        self.distances_sd_deviation = []
        self.distances = []

    def add(self, source, target, distances):

        self.source.append(source)
        self.target.append(target)

        self.distances_mse.append(np.sqrt(np.mean(distances ** 2)))
        self.distances_max_deviation.append(np.max(distances))
        self.distances_min_deviation.append(np.min(distances))
        self.distances_sd_deviation.append(np.std(distances))
        self.distances.append(distances.tolist())
