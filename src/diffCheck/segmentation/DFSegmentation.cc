#include "DFSegmentation.hh"

#include <cilantro/utilities/point_cloud.hpp>
#include <cilantro/core/nearest_neighbors.hpp>
#include <cilantro/clustering/connected_component_extraction.hpp>

namespace diffCheck::segmentation
{   
    std::vector<std::shared_ptr<geometry::DFPointCloud>> DFSegmentation::NormalBasedSegmentation(
        std::shared_ptr<geometry::DFPointCloud> &pointCloud,
        float normalThresholdDegree,
        int minClusterSize,
        bool useKnnNeighborhood,
        int knnNeighborhoodSize,
        float radiusNeighborhoodSize,
        bool colorClusters)
    {
        if (!pointCloud->HasNormals())
        {
            DIFFCHECK_WARN("The point cloud does not have normals. Estimating normals with 50 neighbors.");
            pointCloud->EstimateNormals(true, 50);
        }

        std::shared_ptr<cilantro::PointCloud3f> cilantroPointCloud = pointCloud->Cvt2CilantroPointCloud();

        std::vector<std::shared_ptr<geometry::DFPointCloud>> segments;
        if (useKnnNeighborhood)
        {
            cilantro::KNNNeighborhoodSpecification<int> neighborhood(knnNeighborhoodSize);

            cilantro::NormalsProximityEvaluator<float, 3> similarityEvaluator(
            cilantroPointCloud->normals, 
            normalThresholdDegree*M_PI/180.0f);

            cilantro::ConnectedComponentExtraction3f<> segmenter(cilantroPointCloud->points);
            segmenter.segment(neighborhood, similarityEvaluator, minClusterSize);
            auto clusterToPointMap = segmenter.getClusterToPointIndicesMap();
            int nSegments = segmenter.getNumberOfClusters();

            for (int indice = 0; indice<nSegments; indice++)
            {
                std::shared_ptr<geometry::DFPointCloud> segment = std::make_shared<geometry::DFPointCloud>();
                for (auto pointIndice : clusterToPointMap[indice])
                {
                    Eigen::Vector3d point = cilantroPointCloud->points.col(pointIndice).cast<double>();
                    Eigen::Vector3d normal = cilantroPointCloud->normals.col(pointIndice).cast<double>();
                    segment->Points.push_back(point);
                    segment->Normals.push_back(normal);
                    if (cilantroPointCloud->hasColors())
                    {
                        Eigen::Vector3d color = cilantroPointCloud->colors.col(pointIndice).cast<double>();
                        segment->Colors.push_back(color);
                    }
                }
                if (colorClusters)
                    segment->ApplyColor(Eigen::Vector3d::Random());
                segments.push_back(segment);
            }
        }
        else
        {
            cilantro::RadiusNeighborhoodSpecification<float> neighborhood(radiusNeighborhoodSize);
            cilantro::NormalsProximityEvaluator<float, 3> similarityEvaluator(
            cilantroPointCloud->normals,
            normalThresholdDegree*M_PI/180.0f);

            cilantro::ConnectedComponentExtraction3f<> segmenter(cilantroPointCloud->points);
            segmenter.segment(neighborhood, similarityEvaluator, minClusterSize);

            auto clusterToPointMap = segmenter.getClusterToPointIndicesMap();
            int nSegments = segmenter.getNumberOfClusters();

            for (int indice = 0; indice<nSegments; indice++)
            {
                std::shared_ptr<geometry::DFPointCloud> segment = std::make_shared<geometry::DFPointCloud>();
                for (auto pointIndice : clusterToPointMap[indice])
                {
                    Eigen::Vector3d point = cilantroPointCloud->points.col(pointIndice).cast<double>();
                    Eigen::Vector3d normal = cilantroPointCloud->normals.col(pointIndice).cast<double>();
                    segment->Points.push_back(point);
                    segment->Normals.push_back(normal);
                    if (cilantroPointCloud->hasColors())
                    {
                        Eigen::Vector3d color = cilantroPointCloud->colors.col(pointIndice).cast<double>();
                        segment->Colors.push_back(color);
                    }
                }
                if (colorClusters)
                    segment->ApplyColor(Eigen::Vector3d::Random());
                segments.push_back(segment);
            }
        }

        return segments;
    }

    std::shared_ptr<geometry::DFPointCloud> DFSegmentation::AssociateClustersToMeshes(
        std::vector<std::shared_ptr<geometry::DFMesh>> referenceMesh,
        std::vector<std::shared_ptr<geometry::DFPointCloud>> &clusters,
        double associationThreshold)
    {
        std::shared_ptr<geometry::DFPointCloud> unifiedPointCloud = std::make_shared<geometry::DFPointCloud>();
        std::vector<std::shared_ptr<geometry::DFPointCloud>> segmentsRemainder;

        // iterate through the mesh faces given as function argument
        for (std::shared_ptr<diffCheck::geometry::DFMesh> face : referenceMesh)
        {
            std::shared_ptr<geometry::DFPointCloud> correspondingSegment;
            std::shared_ptr<open3d::geometry::TriangleMesh> o3dFace;
            o3dFace = face->Cvt2O3DTriangleMesh();

            // Getting the center of the mesh face
            Eigen::Vector3d faceCenter;
            // open3d::geometry::OrientedBoundingBox orientedBoundingBox = o3dFace->GetMinimalOrientedBoundingBox();
            faceCenter = o3dFace->GetCenter();

            // Getting the normal of the mesh face
            
            Eigen::Vector3d faceNormal = face->GetFirstNormal();

            // iterate through the segments to find the closest ones compared to the face center taking the normals into account
            Eigen::Vector3d segmentCenter;
            Eigen::Vector3d segmentNormal;
            double faceDistance = std::numeric_limits<double>::max();
            for (auto segment : clusters)
            {
                for (auto point : segment->Points)
                {
                    segmentCenter += point;
                }
                segmentCenter /= segment->GetNumPoints();

                for (auto normal : segment->Normals)
                {
                    segmentNormal += normal;
                }
                segmentNormal.normalize();

                double currentDistance = (faceCenter - segmentCenter).norm() / std::abs(segmentNormal.dot(faceNormal));
                // if the distance is smaller than the previous one, update the distance and the corresponding segment
                if (currentDistance < faceDistance)
                {
                    correspondingSegment = segment;
                    faceDistance = currentDistance;
                }
            }
            
            // get the triangles of the face.
            std::vector<Eigen::Vector3i> faceTriangles = o3dFace->triangles_;

            for (Eigen::Vector3d point : correspondingSegment->Points)
            {
                bool pointInFace = false;
                /*
                To check if the point is in the face, we take into account all the triangles forming the face.
                We calculate the area of each triangle, then check if the sum of the areas of the tree triangles 
                formed by two of the points of the referencr triangle and our point is equal to the reference triangle area 
                (within a user-defined margin). If it is the case, the triangle is in the face.
                */
                for (Eigen::Vector3i triangle : faceTriangles)
                {
                    // reference triangle
                    Eigen::Vector3d v0 = o3dFace->vertices_[triangle[0]];
                    Eigen::Vector3d v1 = o3dFace->vertices_[triangle[1]];
                    Eigen::Vector3d v2 = o3dFace->vertices_[triangle[2]];
                    Eigen::Vector3d n = (v1 - v0).cross(v2 - v0);
                    double referenceTriangleArea = n.norm()*0.5;
                    
                    // triangle 1
                    Eigen::Vector3d n1 = (v1 - v0).cross(point - v0);
                    double area1 = n1.norm()*0.5;

                    // triangle 2
                    Eigen::Vector3d n2 = (v2 - v1).cross(point - v1);
                    double area2 = n2.norm()*0.5;

                    // triangle 3
                    Eigen::Vector3d n3 = (v0 - v2).cross(point - v2);
                    double area3 = n3.norm()*0.5;

                    double res = ( area1 + area2 + area3 - referenceTriangleArea) / referenceTriangleArea;
                    if (res < associationThreshold)
                    {
                        pointInFace = true;
                        break;
                    }
                }
                if (pointInFace)
                {
                    unifiedPointCloud->Points.push_back(point);
                    unifiedPointCloud->Normals.push_back(
                        correspondingSegment->Normals[std::distance(
                            correspondingSegment->Points.begin(), 
                            std::find(correspondingSegment->Points.begin(), 
                            correspondingSegment->Points.end(), 
                            point))]
                        );
                }
            }
            // removing points from the segment that are in the face
            for(Eigen::Vector3d point : unifiedPointCloud->Points)
            {
                correspondingSegment->Points.erase(
                    std::remove(
                        correspondingSegment->Points.begin(), 
                        correspondingSegment->Points.end(), 
                        point), 
                    correspondingSegment->Points.end());
            }
            if (correspondingSegment->GetNumPoints() == 0)
            {
                clusters.erase(
                    std::remove(
                        clusters.begin(), 
                        clusters.end(), 
                        correspondingSegment), 
                    clusters.end());
            }
        }
        return unifiedPointCloud;
    }

    void DFSegmentation::CleanUnassociatedClusters(
        std::vector<std::shared_ptr<geometry::DFPointCloud>> &unassociatedClusters,
        std::vector<std::shared_ptr<geometry::DFPointCloud>> &existingPointCloudSegments,
        std::vector<std::vector<std::shared_ptr<geometry::DFMesh>>> meshes,
        double associationThreshold)
    {
        for (std::shared_ptr<geometry::DFPointCloud> cluster : unassociatedClusters)
        {
            Eigen::Vector3d clusterCenter;
            Eigen::Vector3d clusterNormal;
            for (Eigen::Vector3d point : cluster->Points)
            {
                clusterCenter += point;
            }
            clusterCenter /= cluster->GetNumPoints();
            for (Eigen::Vector3d normal : cluster->Normals)
            {
                clusterNormal += normal;
            }
            clusterNormal /= cluster->GetNumPoints();

            std::shared_ptr<diffCheck::geometry::DFMesh> testMesh;
            int meshIndex;
            int faceIndex ;
            double distance = std::numeric_limits<double>::max();
            for (std::vector<std::shared_ptr<geometry::DFMesh>> piece : meshes)
            {
                for (std::shared_ptr<geometry::DFMesh> meshFace : piece)
                {
                    Eigen::Vector3d faceCenter;
                    Eigen::Vector3d faceNormal;

                    std::shared_ptr<open3d::geometry::TriangleMesh> o3dFace = meshFace->Cvt2O3DTriangleMesh();
                    
                    Eigen::Vector3d faceNormal = meshFace->GetFirstNormal();

                    // std::shared_ptr<open3d::geometry::OrientedBoundingBox> orientedBoundingBox(new open3d::geometry::OrientedBoundingBox(o3dFace->GetMinimalOrientedBoundingBox()));
                    faceCenter = o3dFace->GetCenter();
                    /*
                    To make sure we select the right meshFace, we add another metric:
                    Indeed, from experimentation, sometimes the wrong mesh face is selected, because it is parallel to the correct one 
                    (so the normal don't play a role) and the center of the face is closer to the cluster center than the correct face.
                    To prevent this, we take into the account the angle between the line linking the center of the meshFace considered 
                    and the center of the point cloud cluster and the normal of the cluster. This value should be close to pi/2

                    The following two lines are not super optimized but more readable thatn the optimized version
                    */

                    double clusterNormalToJunctionLineAngle = std::abs(std::acos(clusterNormal.dot((clusterCenter - faceCenter).normalized())));

                    double currentDistance = (clusterCenter - faceCenter).norm()   * std::pow(std::cos(clusterNormalToJunctionLineAngle), 2) / std::pow(clusterNormal.dot(faceNormal), 2);
                    if (currentDistance < distance)
                    {
                        distance = currentDistance;
                        meshIndex = std::distance(meshes.begin(), std::find(meshes.begin(), meshes.end(), piece));
                        faceIndex = std::distance(piece.begin(), std::find(piece.begin(), piece.end(), meshFace));
                        testMesh = meshFace;
                    }
                }
            }
            // diffCheck::visualizer::Visualizer vis;
            // vis.AddPointCloud(cluster);
            // vis.AddMesh(meshes[meshIndex][faceIndex]);
            // vis.Run();
            std::shared_ptr<geometry::DFPointCloud> completed_segment = existingPointCloudSegments[meshIndex];
            for (Eigen::Vector3d point : cluster->Points)
            {
                bool pointInFace = false;
                std::shared_ptr<open3d::geometry::TriangleMesh> o3dFace = meshes[meshIndex][faceIndex]->Cvt2O3DTriangleMesh();
                std::vector<Eigen::Vector3i> faceTriangles = o3dFace->triangles_;
                for (Eigen::Vector3i triangle : faceTriangles)
                {
                    Eigen::Vector3d v0 = o3dFace->vertices_[triangle[0]];
                    Eigen::Vector3d v1 = o3dFace->vertices_[triangle[1]];
                    Eigen::Vector3d v2 = o3dFace->vertices_[triangle[2]];
                    Eigen::Vector3d n = (v1 - v0).cross(v2 - v0);
                    double referenceTriangleArea = n.norm()*0.5;
                    Eigen::Vector3d n1 = (v1 - v0).cross(point - v0);
                    double area1 = n1.norm()*0.5;
                    Eigen::Vector3d n2 = (v2 - v1).cross(point - v1);
                    double area2 = n2.norm()*0.5;
                    Eigen::Vector3d n3 = (v0 - v2).cross(point - v2);
                    double area3 = n3.norm()*0.5;
                    double res = ( area1 + area2 + area3 - referenceTriangleArea) / referenceTriangleArea;
                    if (res < associationThreshold)
                    {
                        pointInFace = true;
                        break;
                    }
                }
                if (pointInFace)
                {
                    completed_segment->Points.push_back(point);
                    completed_segment->Normals.push_back(cluster->Normals[std::distance(cluster->Points.begin(), std::find(cluster->Points.begin(), cluster->Points.end(), point))]);
                }
            }
            std::vector<int> indicesToRemove;
            for (int i = 0; i < cluster->Points.size(); ++i) 
            {
                if (std::find(completed_segment->Points.begin(), completed_segment->Points.end(), cluster->Points[i]) != completed_segment->Points.end()) 
                {
                    indicesToRemove.push_back(i);
                }
            }

            for (auto it = indicesToRemove.rbegin(); it != indicesToRemove.rend(); ++it) 
            {
                std::swap(cluster->Points[*it], cluster->Points.back());
                cluster->Points.pop_back();
                std::swap(cluster->Normals[*it], cluster->Normals.back());
                cluster->Normals.pop_back();
            }
        }
    };
} // namespace diffCheck::segmentation