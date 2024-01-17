import sys
import carb
import omni.ext
import omni.usd
import omni.kit.app
import math
from omni.services.core import main
from pxr import Usd, UsdGeom, UsdSkel, Vt, Gf, Sdf, Tf, Sdf
import os

def generate_non_skin_blendshapes():


    eye_left_mesh_paths: List[str] = [
        "EYE MESH 1 PATH",
        "EYE MESH 2 PATH",
    ]
    eye_left_pivot_path: str = "EYE PIVOT PATH LEFT"

    eye_right_mesh_paths: List[str] = [
        "EYE MESH 1 PATH",
        "EYE MESH 2 PATH",
    ]  
    eye_right_pivot_path: str = "EYE PIVOT PATH RIGHT"

    jaw_mesh_paths: List[str] = [
        "JAW MESH 1 PATH",
        "JAW MESH 2 PATH",
    ]  
    pivot_jaw_path: str = "JAW PIVOT PATH"

    axis_forward: Gf.Vec3d = (0, 0, 1)
    axis_up: Gf.Vec3d = (0, 1, 0)
    axis_right: Gf.Vec3d = (-1, 0, 0)

    scale_factor: float = 1.0


    eye_rotation: float = 25.0
    jaw_open_rotation: float =  20.0
    jaw_side_rotation: float =  8.5
    jaw_forward_translation: float = 1.0


    # Create stage
    stage = omni.usd.get_context().get_stage()
  
    for eye_mesh_path in eye_left_mesh_paths:
        create_empty_blendshapes(eye_mesh_path)
        points = stage.GetPrimAtPath(eye_mesh_path).GetAttribute("points")
        pivot = get_prim_position(eye_left_pivot_path, scale_factor, axis_forward, axis_up, axis_right)
        
        # eyeLookDownLeft       
        assign_offset(get_rotation_offsets(points, pivot, -eye_rotation, axis_right), eye_mesh_path, "eyeLookDownLeft")
        # eyeLookInLeft
        assign_offset(get_rotation_offsets(points, pivot, -eye_rotation, axis_up), eye_mesh_path, "eyeLookInLeft")
        # eyeLookOutLeft
        assign_offset(get_rotation_offsets(points, pivot, eye_rotation, axis_up), eye_mesh_path, "eyeLookOutLeft")
        # eyeLookUpLeft
        assign_offset(get_rotation_offsets(points, pivot, eye_rotation, axis_right), eye_mesh_path, "eyeLookUpLeft")

    for eye_mesh_path in eye_right_mesh_paths:
        create_empty_blendshapes(eye_mesh_path)
        points = stage.GetPrimAtPath(eye_mesh_path).GetAttribute("points")
        pivot = get_prim_position(eye_right_pivot_path, scale_factor, axis_forward, axis_up, axis_right)
        
        # eyeLookDownRight
        assign_offset(get_rotation_offsets(points, pivot, -eye_rotation, axis_right), eye_mesh_path, "eyeLookDownRight")
        # eyeLookInRight
        assign_offset(get_rotation_offsets(points, pivot, eye_rotation, axis_up), eye_mesh_path, "eyeLookInRight")
        # eyeLookOutRight
        assign_offset(get_rotation_offsets(points, pivot, -eye_rotation, axis_up), eye_mesh_path, "eyeLookOutRight")
        # eyeLookUpRight
        assign_offset(get_rotation_offsets(points, pivot, eye_rotation, axis_right), eye_mesh_path, "eyeLookUpRight")

    for jaw_mesh_path in jaw_mesh_paths:
        create_empty_blendshapes(jaw_mesh_path)
        points = stage.GetPrimAtPath(jaw_mesh_path).GetAttribute("points")
        pivot = get_prim_position(pivot_jaw_path, scale_factor, axis_forward, axis_up, axis_right)
        
        # jawOpen
        assign_offset(get_rotation_offsets(points, pivot, -jaw_open_rotation, axis_right), jaw_mesh_path, "jawOpen")
        # jawRight
        assign_offset(get_rotation_offsets(points, pivot, -jaw_side_rotation, axis_up), jaw_mesh_path, "jawRight")
        # jawLeft
        assign_offset(get_rotation_offsets(points, pivot, jaw_side_rotation, axis_up), jaw_mesh_path, "jawLeft")
        # jawForward
        assign_offset(get_translation_offset(points, jaw_forward_translation, axis_forward, scale_factor), jaw_mesh_path, "jawForward")




def get_prim_position(prim_path, scale_factor, axis_forward: Gf.Vec3d, axis_up: Gf.Vec3d, axis_right: Gf.Vec3d):
    stage = omni.usd.get_context().get_stage()

    prim = stage.GetPrimAtPath(prim_path)

    if not prim:
        print(f"Prim at path '{prim_path}' not found in the stage.")
        return None

    xform = UsdGeom.Xform(prim)

    # Get the world-space transform of the prim.
    world_transform = xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Extract the translation component from the transform.
    position = world_transform.ExtractTranslation() * scale_factor
    new_x = position[0] * axis_right[0] + position[1] * axis_up[0] + position[2] * axis_forward[0]
    new_y = position[0] * axis_right[1] + position[1] * axis_up[1] + position[2] * axis_forward[1]
    new_z = position[0] * axis_right[2] + position[1] * axis_up[2] + position[2] * axis_forward[2]

    position_converted: Gf.Vec3d  = (new_x, new_y, new_z)

    return position_converted


def get_rotation_offsets(points, pivot, angle_degrees, axis):
    rotation = Gf.Matrix4d(1.0)
    rotation.SetRotateOnly(Gf.Rotation(axis, angle_degrees))

    offsets = []

    pivot_point = vec3d_to_vec3f(pivot)

    # Rotate Points around Pivot
    for point in points.Get():
        translated_point = point - pivot_point
        rotated_point = rotation.Transform(translated_point)
        final_point = rotated_point + pivot_point
        offset_point = final_point - point
        offsets.append(offset_point)

    return offsets

def get_translation_offset(points, translation, axis, scale_factor):
    offsets = []

    # Move Points in direction
    translation_vector: Gf.Vec3f = (axis[0] * scale_factor * translation, axis[1] * scale_factor * translation, axis[2] * scale_factor * translation)
    print (translation_vector)
    for point in points.Get():
        translated_point = point + translation_vector
        offset_point = translated_point - point
        offsets.append(offset_point)

    return offsets
    

def assign_offset(offsets, prim_path: str, prim_name: str):
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path + '/' + prim_name)
    prim.GetAttribute("offsets").Set(offsets)

def empty_points(points):
    emptyValues = []
    for point in points.Get():
        emptyValues.append(Gf.Vec3f(0,0,0))
    return emptyValues

def point_indices(points):
    indices = []
    count = 0
    for point in points.Get():
        indices.append(count)
        count += 1
    return indices
    
def vec3d_to_vec3f(vec3d: Gf.Vec3f):
    return Gf.Vec3f(float(vec3d[0]), float(vec3d[1]), float(vec3d[2]))

def create_empty_blendshapes(prim_path: str):
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsA(UsdGeom.Mesh):
        print(f"Prim at path '{prim_path}' is not of type 'Mesh'.")
        return None
    points = prim.GetAttribute("points")

    blendShape_names: List[str] = ["eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft", "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeSquintRight", "eyeWideRight", "jawForward", "jawLeft", "jawRight", "jawOpen", "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight", "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper", "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthUpperUpLeft", "mouthUpperUpRight", "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight", "tongueOut"]
    blendShape_weight_values: List[float] = [0] * 52
    blendShapes = prim.CreateAttribute("skel:blendShapes", Sdf.ValueTypeNames.TokenArray)
    blendShapes.Set(blendShape_names)
    blendShape_weights = prim.CreateAttribute("skel:blendShapeWeights", Sdf.ValueTypeNames.FloatArray)
    blendShape_weights.Set(blendShape_weight_values)
    blendShapeTargets = []
    for blendShape_name in blendShape_names:
        blendShape_path = prim_path + '/' + blendShape_name
        blendShapeTargets.append(blendShape_path)
        blendShape_prim = stage.DefinePrim(blendShape_path, "BlendShape")
        offsets = blendShape_prim.CreateAttribute("offsets", Sdf.ValueTypeNames.Point3fArray)
        offsets.Set(empty_points(points))
        pointIndices = blendShape_prim.CreateAttribute("pointIndices", Sdf.ValueTypeNames.IntArray)
        pointIndices.Set(point_indices(points))

    blendShapeTargets_relationship: Usd.Relationship = prim.CreateRelationship("skel:blendShapeTargets")
    blendShapeTargets_relationship.SetTargets(blendShapeTargets)

    

if __name__ == "__main__":
    generate_non_skin_blendshapes()






