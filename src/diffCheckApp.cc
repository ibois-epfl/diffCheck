#include "diffCheck.hh"
#include "diffCheck/log.hh"

#include <iostream>
#include <fstream>

// checking computation time 
#include <chrono>

int main()
{
  auto initTime = std::chrono::high_resolution_clock::now();

  std::shared_ptr<diffCheck::geometry::DFPointCloud> pcdSrc = std::make_shared<diffCheck::geometry::DFPointCloud>();
  std::vector<std::shared_ptr<diffCheck::geometry::DFMesh>> meshSrc = std::vector<std::shared_ptr<diffCheck::geometry::DFMesh>>();
  std::vector<std::shared_ptr<diffCheck::geometry::DFPointCloud>> segments;
  std::vector<std::string> meshPaths;

  std::string meshesFolderPath = R"(C:\Users\localuser\Desktop\again_other_meshes_for_diffCheck\)";

  for (int i = 1; i <= 4; i++)
  {
    std::string meshPath = meshesFolderPath + std::to_string(i) + ".ply";
    std::shared_ptr<diffCheck::geometry::DFMesh> mesh = std::make_shared<diffCheck::geometry::DFMesh>();
    mesh->LoadFromPLY(meshPath);
    meshSrc.push_back(mesh);
  }

  std::string pathPcdSrc = R"(C:\Users\localuser\Desktop\cleaned_AC_pc_90deg.ply)";

  pcdSrc->LoadFromPLY(pathPcdSrc);

  pcdSrc->EstimateNormals();
  segments = diffCheck::segmentation::DFSegmentation::NormalBasedSegmentation(
    pcdSrc,
    2.0f,
    100,
    true,
    30,
    0.5f,
    false);
  std::cout << "number of segments:" << segments.size()<< std::endl;

  std::shared_ptr<diffCheck::geometry::DFPointCloud> unifiedSegments = 
    diffCheck::segmentation::DFSegmentation::AssociateSegments(meshSrc, segments, .1);

  diffCheck::visualizer::Visualizer vis;
  for (auto segment : segments)
  {
    // colorize the segments with random colors
    double r = static_cast<double>(rand()) / RAND_MAX;
    double g = static_cast<double>(rand()) / RAND_MAX;
    double b = static_cast<double>(rand()) / RAND_MAX;

    segment->Colors.clear();
    for (int i = 0; i < segment->Points.size(); i++)
    {
      segment->Colors.push_back(Eigen::Vector3d(r, g, b));
    }
    // vis.AddPointCloud(segment);

  }
  for(auto mesh : meshSrc)
  {
    vis.AddMesh(mesh);
  }

  for (int i = 0; i < unifiedSegments->Points.size(); i++)
  {
    unifiedSegments->Colors.push_back(Eigen::Vector3d(0, 0, 0));
  }
  vis.AddPointCloud(unifiedSegments);

  auto endTime = std::chrono::high_resolution_clock::now();
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - initTime);
  std::cout << "Computation time:" << duration.count() << std::endl;

  vis.Run();
  return 0;
}