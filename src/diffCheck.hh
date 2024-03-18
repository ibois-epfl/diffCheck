#pragma once

#include <GL/glew.h>
#include <GLFW/glfw3.h>

#include <open3d/Open3D.h>

#include "diffcheckpch.hh"

// #include "diffCheck/glHeader.hh"
#include "diffCheck/libHeaderTemplate.hh"  // This is a dummy include to test the include path

namespace diffCheck {
    /// @brief Function 1 of the library
    int func1();

    /// @brief Function 2 of the library
    int func2();

    /// @brief Function 3 of the library
    int func3();

    /// @brief Testing open3d import
    void testOpen3d();

    /// @brief Testing libigl import
    void testLibigl();

}  // namespace diffCheck