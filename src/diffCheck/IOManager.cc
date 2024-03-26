#include "IOManager.hh"

#include <igl/readPLY.h>



namespace diffCheck::io
{
    std::shared_ptr<diffCheck::geometry::DFPointCloud> ReadPLYPointCloud(const std::string &filename)
    {
        std::shared_ptr<diffCheck::geometry::DFPointCloud> pointCloud = std::make_shared<diffCheck::geometry::DFPointCloud>();
        Eigen::MatrixXd V;
        Eigen::MatrixXd C;
        Eigen::MatrixXd N;
        Eigen::MatrixXi F;
        
        igl::readPLY(filename, V, F, C, N);

        pointCloud->Points.resize(V.rows());
        for (int i = 0; i < V.rows(); i++)
        {
            pointCloud->Points[i] = V.row(i);
        }
        pointCloud->Colors.resize(C.rows());
        for (int i = 0; i < C.rows(); i++)
        {
            pointCloud->Colors[i] = C.row(i);
        }
        pointCloud->Normals.resize(N.rows());
        for (int i = 0; i < N.rows(); i++)
        {
            pointCloud->Normals[i] = N.row(i);
        }
        return pointCloud;
    }

    std::shared_ptr<diffCheck::geometry::DFMesh> ReadPLYMeshFromFile(const std::string &filename)
    {
        // check if the ply is from Rhino by searching for the string "Rhinoceros"
        std::ifstream file(filename);
        std::string line;
        bool isRhino = false;
        while (std::getline(file, line))
        {
            if (line.find("Rhinoceros") != std::string::npos)
            {
                isRhino = true;
                break;
            }
        }
        file.close();
        std::cout << "isRhino: " << isRhino << std::endl;

        // detect if the ply is of fixed variable lengths or not
        bool isFixedLength = false;
        std::ifstream file2(filename);
        std::string line2;
        while (std::getline(file2, line2))
        {
            if (line2.find("element vertex") != std::string::npos)
            {
                isFixedLength = true;
                break;
            }
        }
        file2.close();
        std::cout << "isFixedLength: " << isFixedLength << std::endl;
        







        std::shared_ptr<diffCheck::geometry::DFMesh> mesh = std::make_shared<diffCheck::geometry::DFMesh>();
        Eigen::MatrixXd V;
        Eigen::MatrixXd C;
        Eigen::MatrixXd N;
        Eigen::MatrixXi F;

        // read the ply file
        igl::readPLY(filename, V, F, C, N);

        mesh->Vertices.resize(V.rows());
        for (int i = 0; i < V.rows(); i++)
        {
            mesh->Vertices[i] = V.row(i);
        }
        mesh->Faces.resize(F.rows());
        for (int i = 0; i < F.rows(); i++)
        {
            mesh->Faces[i] = F.row(i);
        }
        mesh->ColorsVertex.resize(C.rows());
        for (int i = 0; i < C.rows(); i++)
        {
            mesh->ColorsFace[i] = C.row(i);
        }
        mesh->NormalsVertex.resize(N.rows());
        for (int i = 0; i < N.rows(); i++)
        {
            mesh->NormalsFace[i] = N.row(i);
        }

        return mesh;
    }
} // namespace diffCheck::io