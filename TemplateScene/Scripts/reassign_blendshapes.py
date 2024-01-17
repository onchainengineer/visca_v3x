import sys
import carb
import omni.ext
import omni.usd
import omni.anim.graph.core as ag
import omni.timeline
import omni.kit.app
from omni.services.core import main
from pxr import Usd, UsdGeom, UsdSkel, Vt, Gf, Sdf, Tf, Sdf
import os

from typing import Dict, List


#List of Meshes that use facial blendshapes.
#Replace these with the prim paths to all facial prims of type Mesh
facial_meshes_prim_paths: List[str] = [
    "World/YOUR_CHARACTERS_FACIAL_MESH_1",
    "World/YOUR_CHARACTERS_FACIAL_MESH_2",
    "World/YOUR_CHARACTERS_FACIAL_MESH_3",
    "World/YOUR_CHARACTERS_FACIAL_MESH_4",
]

# Dictionary defining associated blendshape names
# Replace the names on the left of the : with the corresponding names of your character's blendshapes
# The example names are based on Reallusion's naming
blendshape_name_mapping: Dict[str, str] = {
    "A14_Eye_Blink_Left":"eyeBlinkLeft",
    "A08_Eye_Look_Down_Left":"eyeLookDownLeft",
    "A11_Eye_Look_In_Left":"eyeLookInLeft",
    "A10_Eye_Look_Out_Left":"eyeLookOutLeft",
    "A06_Eye_Look_Up_Left":"eyeLookUpLeft",
    "A16_Eye_Squint_Left":"eyeSquintLeft",
    "A18_Eye_Wide_Left":"eyeWideLeft",
    "A15_Eye_Blink_Right":"eyeBlinkRight",
    "A09_Eye_Look_Down_Right":"eyeLookDownRight",
    "A12_Eye_Look_In_Right":"eyeLookInRight",
    "A13_Eye_Look_Out_Right":"eyeLookOutRight",
    "A07_Eye_Look_Up_Right":"eyeLookUpRight",
    "A17_Eye_Squint_Right":"eyeSquintRight",
    "A18_Eye_Wide_Left":"eyeWideRight",
    "A26_Jaw_Forward":"jawForward",
    "A27_Jaw_Left":"jawLeft",
    "A28_Jaw_Right":"jawRight",
    "A25_Jaw_Open":"jawOpen",
    "A37_Mouth_Close":"mouthClose",
    "A29_Mouth_Funnel":"mouthFunnel",
    "A30_Mouth_Pucker":"mouthPucker",
    "A31_Mouth_Left":"mouthLeft",
    "A32_Mouth_Right":"mouthRight",
    "A38_Mouth_Smile_Left":"mouthSmileLeft",
    "A39_Mouth_Smile_Right":"mouthSmileRight",
    "A40_Mouth_Frown_Left":"mouthFrownLeft",
    "A41_Mouth_Frown_Right":"mouthFrownRight",
    "A42_Mouth_Dimple_Left":"mouthDimpleLeft",
    "A43_Mouth_Dimple_Right":"mouthDimpleRight",
    "A50_Mouth_Stretch_Left":"mouthStretchLeft",
    "A51_Mouth_Stretch_Right":"mouthStretchRight",
    "A34_Mouth_Roll_Lower":"mouthRollLower",
    "A33_Mouth_Roll_Upper":"mouthRollUpper",
    "A36_Mouth_Shrug_Lower":"mouthShrugLower",
    "A35_Mouth_Shrug_Upper":"mouthShrugUpper",
    "A48_Mouth_Press_Left":"mouthPressLeft",
    "A49_Mouth_Press_Right":"mouthPressRight",
    "A46_Mouth_Lower_Down_Left":"mouthLowerDownLeft",
    "A47_Mouth_Lower_Down_Right":"mouthLowerDownRight",
    "A44_Mouth_Upper_Up_Left":"mouthUpperUpLeft",
    "A45_Mouth_Upper_Up_Right":"mouthUpperUpRight",
    "A02_Brow_Down_Left":"browDownLeft",
    "A03_Brow_Down_Right":"browDownRight",
    "A01_Brow_Inner_Up":"browInnerUp",
    "A04_Brow_Outer_Up_Left":"browOuterUpLeft",
    "A05_Brow_Outer_Up_Right":"browOuterUpRight",
    "A20_Cheek_Puff":"cheekPuff",
    "A21_Cheek_Squint_Left":"cheekSquintLeft",
    "A22_Cheek_Squint_Right":"cheekSquintRight",
    "A23_Nose_Sneer_Left":"noseSneerLeft",
    "A24_Nose_Sneer_Right":"noseSneerRight",
    "A52_Tongue_Out":"tongueOut",
}








def rename_blendshapes() -> None:

    stage = omni.usd.get_context().get_stage()

    for facial_meshes_prim_path in facial_meshes_prim_paths:
        facial_mesh_prim = stage.GetPrimAtPath(facial_meshes_prim_path)
        
        blendshape_names: List[str] = [
            child_prim.GetName()
            for child_prim in facial_mesh_prim.GetAllChildren()
            if child_prim.IsA(UsdSkel.BlendShape)
        ]
        
        skel_blendshapes: List[str] = []
        for blend_shape_name in blendshape_names:
            
            if blend_shape_name not in blendshape_name_mapping:
                # print(f"Blendshape mapping for blendshape '{blend_shape_name}' not found!")
                skel_blendshapes.append(blend_shape_name)
                continue
            
            mapped_blendshape_name: str = blendshape_name_mapping[blend_shape_name]
            print(f"'{blend_shape_name}' --> mapped to --> '{mapped_blendshape_name}'")
            
            skel_blendshapes.append(mapped_blendshape_name)
                
        facial_mesh_prim.GetAttribute("skel:blendShapes").Set(skel_blendshapes)


def main(args) -> None:
    rename_blendshapes()

if __name__ == "__main__":
    main(sys.argv[1:])