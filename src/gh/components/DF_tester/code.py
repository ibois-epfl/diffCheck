#! python3

import System

import Rhino
import Rhino.Geometry as rg
from ghpythonlib.componentbase import executingcomponent as component

import Grasshopper as gh
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

import diffCheck
import diffCheck.df_cvt_bindings
from diffCheck import diffcheck_bindings

class DFTester(component):
    def RunScript(self):
        """
            The component test and import bind module for diffCheck.
        """
        ghenv.Component.Message = f"diffCheck v: {diffCheck.__version__}"
        is_binding_imported = diffcheck_bindings.dfb_test.test()

        if not is_binding_imported:
            ghenv.Component.AddRuntimeMessage(RML.Warning, "Bindings not imported.")
        else:
            ghenv.Component.AddRuntimeMessage(RML.Remark, "Bindings imported.")

        print(f"diffCheck test: {diffCheck.df_cvt_bindings.test_bindings()}")

        return is_binding_imported

# if __name__ == "__main__":
#     tester = DFTester()
#     tester.RunScript()
