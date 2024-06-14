#! python3
"""
    This module contains the utility functions to compute the difference between source and target
"""

import numpy as np
import open3d as o3d

from diffCheck import diffcheck_bindings

def cloud_2_cloud_distance(source, target, signed=False):
    """
        Compute the Euclidean distance for every point of a source pcd to its closest point on a target pointcloud
    """
    distances = np.asarray(source.compute_P2PDistance(target))

    if signed:

        # Build a KD-tree for the target points
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(target.points)
        kdtree = o3d.geometry.KDTreeFlann(pcd)
        print("KD-tree built successfully.")

        for i in range(len(source.points)):

            query = np.asarray(source.points[i], dtype=np.float64).reshape(3)
            # Query the KD-tree to find the nearest neighbor
            try:
                _, idx, _ = kdtree.search_knn_vector_3d(query, 1)
            except Exception as e:
                print(f"Error querying KD-tree for point {i}: {e}")
                continue
            
            closest_idx = idx[0]
            # Calculate the direction from target to source
            direction = source.points[i] - target.points[closest_idx]

            # Calculate the signed distance
            dot_product = np.dot(direction, target.normals[closest_idx])
            if dot_product < 0:
                distances[i] = -distances[i]

    return distances


def cloud_2_mesh_distance(source, target):
    """
        Calculate the distance between every point of a source pcd to its closest point on a target mesh
    """

    # for every point on the PCD compute the point_2_mesh_distance

    distances = np.ones(len(source.points), dtype=float)

    for i in range(len(source.points)):
        distances[i] = point_2_mesh_distance(target, source.points[i])

    return distances


def point_2_mesh_distance(geo, query_point):
    """
        Calculate the closest distance between a point and a target geometry
    """
    # make a kdtree of the vertices to get the relevant vertices indexes
    pcd = diffcheck_bindings.dfb_geometry.DFPointCloud()
    pcd.points = geo.vertices
    kd_tree = o3d.geometry.KDTreeFlann(pcd)

    # assume smallest distance is the distance to the closest vertex
    _, idx, _ = kd_tree.search_knn_vector_3d(query_point, 1)
    if idx:
        nearest_vertex_idx = idx[0]
    else:
        raise ValueError("The mesh or brep has no vertices. Please provide a valid geometry.")
    nearest_vertex = np.asarray(geo.vertices)[nearest_vertex_idx]
    dist = np.linalg.norm(query_point - nearest_vertex)

    # Find its neighbors with distance less than _dist_ multiplied by two.
    search_distance = dist * 2
    _, v_indices, _ = kd_tree.search_radius_vector_3d(query_point, search_distance)
    
    # Find the faces that belong to these filtered vertices.
    geo_triangles = np.asarray(geo.triangles)
    candidate_mask = np.isin(geo_triangles, v_indices)
    candidate_faces = geo_triangles[np.any(candidate_mask, axis=1)]

    # Step 4: Loop over candidate faces
    shortest_distance = float('inf')
    
    for face in candidate_faces:
        #v0, v1, v2 = np.asarray(geo.vertices)[face]
        pt_face_dist = point_2_face_distance(face, query_point)
        if pt_face_dist < shortest_distance:
            shortest_distance = pt_face_dist
    
    return shortest_distance


def point_2_face_distance(face,  point):
    """
        Calculate the closest distance between a point and a face
    """

    if len(face.vertices) == 3:
        return point_2_triangle_distance(point, face)
    elif len(face.vertices) == 4:
        return point_2_quad_distance(point, face)
    else:
        raise ValueError("Face must be a triangle or quadrilateral")


def point_2_triangle_distance(point, triangle):
    """
        Calculate the shortest distance from a point to a triangle.
    """
    a, b, c = triangle

    bary_coords = barycentric_coordinates(point, a, b, c)

    # If the point is inside or on the triangle, use the barycentric coordinates to find the closest point
    if np.all(bary_coords >= 0):
        closest_point = bary_coords[0] * a + bary_coords[1] * b + bary_coords[2] * c
    
    # If the point is outside the triangle, project it onto the triangle edges and find the closest point
    else:
        proj = np.array([np.dot(point - a, b - a) / np.dot(b - a, b - a), 
                         np.dot(point - b, c - b) / np.dot(c - b, c - b), 
                         np.dot(point - c, a - c) / np.dot(a - c, a - c)])
        proj = np.clip(proj, 0, 1)
        closest_point = np.array([a + proj[0] * (b - a), b + proj[1] * (c - b), c + proj[2] * (a - c)]).min(axis=0)
    
    return np.linalg.norm(closest_point - point)


def barycentric_coordinates(p, a, b, c):
    """
        Calculate the barycentric coordinates of point p with respect to the triangle defined by points a, b, and c.
    """
    v0 = b - a
    v1 = c - a
    v2 = p - a

    d00 = np.dot(v0, v0)
    d01 = np.dot(v0, v1)
    d11 = np.dot(v1, v1)
    d20 = np.dot(v2, v0)
    d21 = np.dot(v2, v1)

    denom = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w

    return np.array([u, v, w])


def point_2_quad_distance(point, quad):
    """
        Calculate the shortest distance from a point to a quadrilateral.
    """
    a, b, c, d = quad.vertices
    
    # Calculate the distance to the two triangles that form the quadrilateral
    return min(point_2_triangle_distance(point, [a, b, c]), 
               point_2_triangle_distance(point, [c, d, a]))


def compute_mse(distances):
    """
        Calculate mean squared distance
    """
    mse = np.sqrt(np.mean(distances ** 2))

    return mse


def compute_max_deviation(distances):
    """
        Calculate max deviation of distances
    """
    max_deviation = np.max(distances)

    return max_deviation


def compute_min_deviation(distances):
    """
        Calculate min deviation of distances
    """

    min_deviation = np.min(distances)

    return min_deviation


def compute_standard_deviation(distances):
    """
        Calculate standard deviation of distances
    """
    standard_deviation = np.std(distances)

    return standard_deviation
