from dataclasses import dataclass


@dataclass
class AnimationGraphBuilderConfig:
    skel_root_prim_path: str = "/World/Animations/Rig_Retarget/character"
    skeleton_prim_path: str = (
        "/World/Animations/Rig_Retarget/character/OUTPUT/root_JNT/root_JNT"
    )

    posture_scope_prim_path: str = "/World/Animations/Animations/Postures"
    gesture_scope_prim_path: str = "/World/Animations/Animations/Gestures"

    blinking_and_darting_animation_prim_path: str = (
        "/World/Animations/Animations/Partial/Blinking_Darting"
    )
    start_animation_prim_path: str = "/World/Animations/Animations/Tests/Test_1"
    end_animation_prim_path: str = "/World/Animations/Animations/Tests/Test_4"

    anim_graph_prim_path: str = "/World/AnimationGraph"

    # default_posture_name: str = "Head_Idle"
    default_posture_name: str = "Attentive"

    default_transition_time: float = 0.7
