import os
from datetime import datetime
from dataclasses import dataclass
import typing
import uuid

import Rhino
import Rhino.Geometry as rg

from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

import diffCheck.df_joint_detector
import diffCheck.df_util


@dataclass
class DFVertex:
    """
    This class represents a vertex, a simple container with 3 coordinates
    """

    x: float
    y: float
    z: float

    def __post_init__(self):
        self.x = self.x or 0.0
        self.y = self.y or 0.0
        self.z = self.z or 0.0

    def __repr__(self):
        return f"Vertex: X={self.x}, Y={self.y}, Z={self.z}"

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        if isinstance(other, DFVertex):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return False

    @classmethod
    def from_rg_point3d(cls, point: rg.Point3d):
        """
        Create a DFVertex from a Rhino Point3d object

        :param point: The Rhino Point3d object
        :return vertex: The DFVertex object
        """
        return cls(point.X, point.Y, point.Z)

    def to_rg_point3d(self):
        """
        Convert the vertex to a Rhino Point3d object

        :return point: The Rhino Point3d object
        """
        return rg.Point3d(self.x, self.y, self.z)


@dataclass
class DFFace:
    """
    This class represents a face, in diffCheck, a face is a collection of vertices.
    """

    # just as breps a first outer loop and then inner loops of DFVertices
    all_loops: typing.List[typing.List[DFVertex]]
    joint_id: int = None

    def __post_init__(self):
        if len(self.all_loops[0]) < 3:
            raise ValueError("A face must have at least 3 vertices")
        self.all_loops = self.all_loops

        self.joint_id = self.joint_id
        self.__is_joint = False
        self.__id = uuid.uuid4().int

        # if df_face is created from a rhino brep face, we store the rhino brep face
        self._rh_brepface = None

        self.is_cylinder = False

    def __repr__(self):
        return f"Face id: {len(self.id)}, IsJoint: {self.is_joint} Loops: {len(self.all_loops)}"

    def __hash__(self):
        outer_loop = tuple(
            tuple(vertex.__dict__.values()) for vertex in self.all_loops[0]
        )
        inner_loops = tuple(
            tuple(vertex.__dict__.values())
            for loop in self.all_loops[1:]
            for vertex in loop
        )
        return hash((outer_loop, inner_loops))

    def __eq__(self, other):
        if isinstance(other, DFFace):
            # check if 
            return self.all_loops == other.all_loops
        return False

    @classmethod
    def from_brep_face(cls, brep_face: rg.BrepFace, joint_id: int = None):
        """
        Create a DFFace from a Rhino Brep face

        :param brep_face: The Rhino Brep face
        :param joint_id: The joint id
        :return face: The DFFace object
        """
        all_loops = []

        if brep_face.IsCylinder():
            cls.is_cylinder = True
            df_face._rh_brepface = brep_face
            return df_face

        for idx, loop in enumerate(brep_face.Loops):
            loop_trims = loop.Trims
            loop_curve = loop.To3dCurve()
            loop_curve = loop_curve.ToNurbsCurve()
            loop_vertices = loop_curve.Points
            loop = []
            for l_v in loop_vertices:
                vertex = DFVertex(l_v.X, l_v.Y, l_v.Z)
                loop.append(vertex)
            all_loops.append(loop)

        df_face = cls(all_loops, joint_id)
        df_face._rh_brepface = brep_face

        return df_face

    def to_brep_face(self):
        """
        Convert the face to a Rhino Brep planar face

        :return brep_face: The Rhino Brep planar face
        """
        if self._rh_brepface is not None:
            return self._rh_brepface

        if self.is_cylinder:
            ghenv.Component.AddRuntimeMessage(
                RML.Warning, "The DFFace was a cylinder created from scratch \n \
                 , it cannot convert to brep.")

        brep_curves = []

        for loop in self.all_loops:
            inner_vertices = [
                rg.Point3d(vertex.x, vertex.y, vertex.z) for vertex in loop
            ]
            inner_polyline = rg.Polyline(inner_vertices)
            inner_curve = inner_polyline.ToNurbsCurve()
            brep_curves.append(inner_curve)

        brep = rg.Brep.CreatePlanarBreps(
            brep_curves, Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        )[0]

        return brep

    def to_mesh(self):
        """
        Convert the face to a Rhino Mesh

        :return mesh: The Rhino Mesh object
        """
        mesh = Rhino.Geometry.Mesh()

        mesh_parts = Rhino.Geometry.Mesh.CreateFromBrep(
                self.to_brep_face().DuplicateFace(True),
                Rhino.Geometry.MeshingParameters.QualityRenderMesh)
        
        for mesh_part in mesh_parts:
            mesh.Append(mesh_part)
        mesh.Faces.ConvertQuadsToTriangles()
        # mesh.Compact()

        return mesh

    @property
    def is_joint(self):
        if self.joint_id is not None:
            self.__is_joint = True
            return True
        self.__is_joint = False
        return False

    @property
    def id(self):
        return self.__id

@dataclass
class DFJoint:
    """
    This class represents a joint, in diffCheck, a joint is a collection of faces
    For convenience, this is used only as a return type from the DFBeam class's property for retrieveing joints
    """

    id: int
    faces: typing.List[DFFace]

    def __post_init__(self):
        self.id = self.id
        self.faces = self.faces or []

    def __repr__(self):
        return f"Joint id: {self.id}, Faces: {len(self.faces)}"

    def to_brep(self):
        """
        Convert the joint to a Rhino Brep object
        """
        brep = rg.Brep()
        for face in self.faces:
            brep.Append(face.to_brep_face())
        brep.Compact()
        return brep

    def to_mesh(self, max_edge_length):
        """
        Convert the joint to a Rhino Mesh object
        """
        rhino_brep_faces = [f.to_brep_face() for f in self.faces]
        mesh = rg.Mesh()

        new_faces = [f.DuplicateFace(True) for f in rhino_brep_faces]

        for f in new_faces:
            param = rg.MeshingParameters()
            param.MaximumEdgeLength = max_edge_length
            mesh_part = rg.Mesh.CreateFromBrep(f, param)[0]
            mesh.Append(mesh_part)

        mesh.Faces.ConvertQuadsToTriangles()
        mesh.Compact()
        return mesh

@dataclass
class DFBeam:
    """
    This class represents a beam, in diffCheck, a beam is a collection of faces
    """

    name: str
    faces: typing.List[DFFace]

    def __post_init__(self):
        self.name = self.name or "Unnamed Beam"
        self.faces = self.faces or []
        self._joint_faces = []
        self._side_faces = []

        self._joints = []

        self.__id = uuid.uuid4().int

    @classmethod
    def from_brep_face(cls, brep):
        """
        Create a DFBeam from a RhinoBrep object.
        It also removes duplicates and creates a list of unique faces.
        """
        faces : typing.List[DFFace] = []
        data_faces = diffCheck.df_joint_detector.JointDetector(brep).run()
        for data in data_faces:
            face = DFFace.from_brep_face(data[0], data[1])
            faces.append(face)
        beam = cls("Beam", faces)
        return beam

    def to_brep(self):
        """
        Convert the beam to a Rhino Brep object
        """
        brep = rg.Brep()
        for face in self.faces:
            brep.Append(face.to_brep_face())
        brep.Compact()

        return brep

    def to_mesh(self, max_edge_length):
        """
        Convert the beam to a Rhino Mesh object
        """
        rhino_brep_faces = [f.to_brep_face() for f in self.faces]
        mesh = rg.Mesh()

        new_faces = [f.DuplicateFace(True) for f in rhino_brep_faces]  # .DuplicateFace bypasses the problem of untrimmed faces that appear in f.to_brep_face

        for f in new_faces:
            param = rg.MeshingParameters()
            param.MaximumEdgeLength = max_edge_length
            mesh_part = rg.Mesh.CreateFromBrep(f, param)[0] #returns a list of meshes with one element
            mesh.Append(mesh_part)

        mesh.Compact()
        return mesh

    def __repr__(self):
        return f"Beam: {self.name}, Faces: {len(self.faces)}"

    @property
    def id(self):
        return self.__id

    @property
    def joint_faces(self):
        return [face for face in self.faces if face.is_joint]

    @property
    def side_faces(self):
        return [face for face in self.faces if not face.is_joint]

    @property
    def joints(self):
        joints : typing.List[DFJoint] = []
        temp_faces = self.joint_faces.copy()
        while len(temp_faces) > 0:
            joint_id = temp_faces[0].joint_id
            joint_faces = [face for face in temp_faces if face.joint_id == joint_id]
            joint = DFJoint(joint_id, joint_faces)
            joints.append(joint)
            temp_faces = [face for face in temp_faces if face.joint_id != joint_id]
        return joints


@dataclass
class DFAssembly:
    """
    This class represents an assembly of beams
    """

    beams: typing.List[DFBeam]
    name: str

    def __post_init__(self):
        self.beams = self.beams
        self.name = self.name or "Unnamed Assembly"

        self._all_jointfaces: typing.List[DFFace] = []
        self._all_sidefaces: typing.List[DFFace] = []

        self._all_joints: typing.List[DFJoint] = []
        
    def __repr__(self):
        return f"Assembly: {self.name}, Beams: {len(self.beams)}"

    def add_beam(self, beam: DFBeam):
        self.beams.append(beam)

    def remove_beam(self, beam_id: int):
        self.beams = [beam for beam in self.beams if beam.id != beam_id]

    def to_xml(self):
        """
        Dump the assembly's meshes to an XML file. On top of the DiffCheck datatypes and structure,
        we export the underlaying beams's meshes from Rhino as vertices and faces.

        :return xml_string: The pretty XML string
        """
        root = ET.Element("DFAssembly")
        root.set("name", self.name)
        # dfbeams
        for beam in self.beams:
            beam_elem = ET.SubElement(root, "DFBeam")
            beam_elem.set("name", beam.name)
            beam_elem.set("id", str(beam.id))
            # dffaces
            for face in beam.faces:
                face_elem = ET.SubElement(beam_elem, "DFFace")
                face_elem.set("id", str(face.id))
                face_elem.set("is_joint", str(face.is_joint))
                face_elem.set("joint_id", str(face.joint_id))
                # export linked mesh
                facerhmesh_elem = ET.SubElement(face_elem, "RhMesh")
                mesh = face.to_mesh()
                mesh_vertices = mesh.Vertices
                for idx, vertex in enumerate(mesh_vertices):
                    facerhmesh_vertex_elem = ET.SubElement(
                        facerhmesh_elem, "RhMeshVertex"
                    )
                    facerhmesh_vertex_elem.set("x", str(vertex.X))
                    facerhmesh_vertex_elem.set("y", str(vertex.Y))
                    facerhmesh_vertex_elem.set("z", str(vertex.Z))
                mesh_faces = mesh.Faces
                for idx, face in enumerate(mesh_faces):
                    facerhmesh_face_elem = ET.SubElement(facerhmesh_elem, "RhMeshFace")
                    facerhmesh_face_elem.set("v1", str(face.A))
                    facerhmesh_face_elem.set("v2", str(face.B))
                    facerhmesh_face_elem.set("v3", str(face.C))
                    facerhmesh_face_elem.set("v4", str(face.D))

        tree = ET.ElementTree(root)
        xml_string = ET.tostring(root, encoding="unicode")
        dom = parseString(xml_string)
        pretty_xml = dom.toprettyxml()

        return pretty_xml

    def dump_xml(self, pretty_xml: str, dir: str):
        """
        Dump the pretty XML to a file

        :param pretty_xml: The pretty XML string
        :param dir: The directory to save the XML
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(dir, f"{self.name}_{timestamp}.xml")

        with open(file_path, "w") as f:
            f.write(pretty_xml)

    @property
    def all_joint_faces(self):
        for beam in self.beams:
            self._all_jointfaces.extend(beam.joint_faces)
        return self._all_jointfaces

    @property
    def all_side_faces(self):
        for beam in self.beams:
            self._all_sidefaces.extend(beam.side_faces)
        return self._all_sidefaces

    @property
    def all_joints(self):
        for beam in self.beams:
            self._all_joints.extend(beam.joints)
        return self._all_joints