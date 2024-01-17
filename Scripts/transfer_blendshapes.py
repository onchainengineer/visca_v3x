import sys
import carb
import omni.ext
import omni.usd
import omni.timeline
import omni.kit.app
from omni.services.core import main
from pxr import Usd, UsdGeom, UsdSkel, Vt, Gf, Sdf, Tf, Sdf
import os

from typing import Dict, List

facial_meshes_origin_paths: List[str] = [
    "MESH 1 ORIGIN PATH",
    "MESH 2 ORIGIN PATH",
    "MESH 3 ORIGIN PATH",
]

facial_meshes_target_paths: List[str] = [
    "MESH 1 TARGET PATH",
    "MESH 2 TARGET PATH",
    "MESH 3 TARGET PATH",
]

def assign_blendshapes() -> None:

    stage = omni.usd.get_context().get_stage()

    for index, facial_mesh_origin_path in enumerate(facial_meshes_origin_paths):
        facial_meshes_target_path = facial_meshes_target_paths[index]
        facial_mesh_origin = stage.GetPrimAtPath(facial_mesh_origin_path)
        facial_mesh_target = stage.GetPrimAtPath(facial_meshes_target_paths[index])
        

        blendShapes: List[UsdSkel.BlendShape] = [
            child_prim
            for child_prim in facial_mesh_origin.GetAllChildren()
            if child_prim.IsA(UsdSkel.BlendShape)
        ]

        blendShapeTargets: List[str] = []
        for blendShape in blendShapes:
            omni.kit.commands.execute("CopyPrimCommand",
                path_from=facial_mesh_origin_path + "/" + blendShape.GetName(),
                path_to=facial_meshes_target_path + "/" + blendShape.GetName())
            blendShapeTargets.append(facial_meshes_target_path + "/" + blendShape.GetName())

        blendShapeTargets_relationship: Usd.Relationship = facial_mesh_target.CreateRelationship("skel:blendShapeTargets")
        blendShapeTargets_relationship.SetTargets(blendShapeTargets)
        
        blendShapes_origin = facial_mesh_origin.GetAttribute("skel:blendShapes").Get()
        if blendShapes_origin is not None:
            targetBlendShapes = create_blendshape_attribute(facial_mesh_target, "skel:blendShapes")
            targetBlendShapes.Set(blendShapes_origin)

        blendShapeWeights_origin = facial_mesh_origin.GetAttribute("skel:blendShapeWeights").Get()
        if blendShapeWeights_origin is not None:
            targetBlendShapes = create_blendshapeweight_attribute(facial_mesh_target, "skel:blendShapeWeights")
            targetBlendShapes.Set(blendShapeWeights_origin)

def create_blendshape_attribute(prim: Usd.Prim, attribute_name: str) -> Usd.Attribute:
    attr: Usd.Attribute = prim.CreateAttribute(attribute_name, Sdf.ValueTypeNames.TokenArray)
    return attr

def create_blendshapeweight_attribute(prim: Usd.Prim, attribute_name: str) -> Usd.Attribute:
    attr: Usd.Attribute = prim.CreateAttribute(attribute_name, Sdf.ValueTypeNames.FloatArray)
    return attr


def main(args) -> None:
    assign_blendshapes()

if __name__ == "__main__":
    main(sys.argv[1:])







