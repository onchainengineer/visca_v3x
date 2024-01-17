from omni.kit.scripting import BehaviorScript
from omni.kit.scripting.scripts import Sdf

import omni.timeline
import omni.anim.graph.core as ag
import omni.appwindow
import omni.log

import random
import math

import numpy as np

from typing import Any, List, Type, Dict, Optional, Tuple

from pxr import Gf, Usd, UsdSkel, UsdGeom, Tf, Sdf

from .animation_graph_builder import AnimationGraphBuilder

from dataclasses import dataclass

from .animation_graph_builder_config import AnimationGraphBuilderConfig


@dataclass
class Gesture:
    prim: UsdSkel.Animation
    name: str


@dataclass
class Posture:
    prim_variants: List[UsdSkel.Animation]
    name: str

@dataclass
class SkelRootState:
    skel_root_parent_prim_name: str = ""
    initialization_count: int = 0
    variant_state_variable_value: int = 0
    last_variant_start_state_time: float = float('-inf')
    last_variant_end_state_time: float = float('-inf')
    last_gesture_start_state_time: float = float('-inf')
    last_gesture_end_state_time: float = float('-inf')

def print_or_log(message: str, stream_id: Optional[str] = None) -> None:
    if stream_id:
        message = f"[{stream_id}] {message}"
    
    print(message)
    # omni.log.info(message, channel="omni.avatarstudio.assets.behavior_script")

class AnimationGraphBuilderBehaviorScript(BehaviorScript):
    def __init__(self, prim_path: Sdf.Path) -> None:
        super().__init__(prim_path)

        self._builder: AnimationGraphBuilder

    def on_init(self) -> None:
        print_or_log("AnimationGraphBuilderBehaviorScript: on_init")

        # Parameters
        self._gesture_state_variable_name: str = "gesture_state"
        self._posture_state_variable_name: str = "posture_state"
        self._variant_state_variable_name: str = "variant_state"

        self._joint_positions_variable_name = "JointPositions"
        self._joint_rotations_variable_name = "JointRotations"
        self._root_position_displacement_variable_name = "RootPositionDisplacement"
        self._root_rotation_displacement_variable_name = "RootRotationDisplacement"
        self._blend_shape_weights_variable_name = "BlendShapeWeights"
        self._blinking_strength_variable_name = "BlinkingStrength"
        self._blend_shape_strength_variable_name = "BlendShapeStrength"

        # Workspace
        self._config = AnimationGraphBuilderConfig()
        
        self._start_state_posture_name: str = self._config.default_posture_name
        self._main_state_machine_prim_path: str = self._config.anim_graph_prim_path + "/MainStateMachine"
        self._anim_graph_start_clip_prim_path: str = (
            self._main_state_machine_prim_path
            + "/GesturesMainState/GesturesStateMachine/Start/AnimationClip"
        )
        self._anim_graph_end_clip_prim_path: str = (
            self._main_state_machine_prim_path
            + "/GesturesMainState/GesturesStateMachine/End/AnimationClip"
        )
        
        # Key: skel_root_prim_path
        self._skel_root_states: Dict[str, SkelRootState] = {}
        
        self._postures: List[Posture]
        self._gestures: List[Gesture]

        # Init
        self._stage: Usd.Stage = omni.usd.get_context().get_stage()
        
        self._builder = AnimationGraphBuilder(self._config.default_transition_time)

        # Get all gesture animation clips
        self._gestures: List[Gesture] = [
            Gesture(child_prim, child_prim.GetName())
            for child_prim in self._stage.GetPrimAtPath(
                self._config.gesture_scope_prim_path
            ).GetAllChildren()
            if child_prim.IsA(UsdSkel.Animation)
        ]
        # print_or_log(self._gestures)

        # Get all posture animation clips
        self._postures = []
        for scope_prim in self._stage.GetPrimAtPath(
            self._config.posture_scope_prim_path
        ).GetAllChildren():
            scope_name: str = scope_prim.GetName()

            # print_or_log(f"Scope: {scope_name}")

            prim_variants: List[UsdSkel.Animation] = []
            for child_prim in scope_prim.GetAllChildren():
                # print_or_log(f"Child: {child_prim.GetName()}")

                if child_prim.IsA(UsdSkel.Animation):
                    # print_or_log(f"SkelAnimation: {child_prim.GetName()}")
                    prim_variants.append(child_prim)

            self._postures.append(Posture(prim_variants, scope_prim.GetName()))
        # print_or_log(self._postures)

        # Check if AnimationGraph exists
        # if self._stage.GetPrimAtPath(self._config.anim_graph_prim_path).IsValid():
        #     print_or_log(
        #         f"Existing animation graph found at '{self._config.anim_graph_prim_path}'! Skipping animation graph generation!")
        #     return

        if self._stage.GetPrimAtPath(self._main_state_machine_prim_path).IsValid():
            print_or_log(
                f"Existing main state machine prim found at '{self._main_state_machine_prim_path}'! Skipping main state prim generation!")
            return

        # Delete the main state machine
        self._builder.clear_prim(self._main_state_machine_prim_path)
    
        # Create an AnimationGraph
        # Sdf.ValueTypeNames.String
        # Sdf.ValueTypeNames.Vector3dArray
        # Sdf.ValueTypeNames.Vector3fArray
        # Sdf.ValueTypeNames.Vector4dArray
        # Sdf.ValueTypeNames.Vector4fArray
        # Sdf.ValueTypeNames.Vector3f
        # Sdf.ValueTypeNames.Vector3d
        # Sdf.ValueTypeNames.Vector4f
        # Sdf.ValueTypeNames.Vector4d

        # Sdf.ValueTypeNames.Float
        # Sdf.ValueTypeNames.FloatArray
        # Sdf.ValueTypeNames.Float3
        # Sdf.ValueTypeNames.Float3Array
        # Sdf.ValueTypeNames.Float4
        # Sdf.ValueTypeNames.Float4Array

        animation_graph_prim_path: str = self._builder.add_animation_graph(
            "/World",
            "AnimationGraph",
            [
                (self._posture_state_variable_name, Sdf.ValueTypeNames.String, "none"),
                (self._gesture_state_variable_name, Sdf.ValueTypeNames.String, "none"),
                (self._variant_state_variable_name, Sdf.ValueTypeNames.String, "none"),
                (
                    self._joint_positions_variable_name,
                    Sdf.ValueTypeNames.Float3Array,
                    [(0.0, 1.0, 2.0), (0.0, 1.0, 2.0)],
                ),
                (
                    self._joint_rotations_variable_name,
                    Sdf.ValueTypeNames.Float4Array,
                    [(0.0, 1.0, 2.0, 3.0), (0.0, 1.0, 2.0, 3.0)],
                ),
                (
                    self._root_position_displacement_variable_name,
                    Sdf.ValueTypeNames.Float3,
                    (0.0, 1.0, 2.0),
                ),
                (
                    self._root_rotation_displacement_variable_name,
                    Sdf.ValueTypeNames.Float4,
                    (0.0, 1.0, 2.0, 3.0),
                ),
                (
                    self._blend_shape_weights_variable_name,
                    Sdf.ValueTypeNames.FloatArray,
                    [],
                ),
                (self._blinking_strength_variable_name, Sdf.ValueTypeNames.Float, 1.0),
                (
                    self._blend_shape_strength_variable_name,
                    Sdf.ValueTypeNames.Float,
                    1.0,
                ),
            ],
        )

        # Create main state machine
        main_state_machine_prim_path: str = self._builder.add_state_machine_node(
            animation_graph_prim_path, f"MainStateMachine"
        )
         
        # Connect the main state machine to the AnimationGraph pose output
        # self._builder.connect_nodes(main_state_machine_prim_path, animation_graph_prim_path, "inputs:pose")
        self._builder.connect_nodes(main_state_machine_prim_path, self._config.anim_graph_prim_path + "/Blend", "inputs:pose0")

        # Create the gesture state machine
        gestures_main_state_prim_path: str = self._builder.add_empty_state(
            main_state_machine_prim_path, "GesturesMainState"
        )

        def gestures_state_machine(gestures_main_state_prim_path: str) -> None:
            state_machine_prim_path: str = self._builder.add_state_machine_node(
                gestures_main_state_prim_path, "GesturesStateMachine"
            )
            
            # Connect the gesture state machine to the gesture main state pose output
            # TODO: REname to gesture_state_machine....
            self._builder.connect_nodes(state_machine_prim_path, gestures_main_state_prim_path, "inputs:pose")

            # Create start node
            start_state_prim_path: str = self._builder.add_state_with_animation(
                state_machine_prim_path,
                "Start",
                self._config.start_animation_prim_path,
                False,
                is_start_state=True,
            )

            # Create end node
            end_state_prim_path: str = self._builder.add_state_with_animation(
                state_machine_prim_path,
                "End",
                self._config.end_animation_prim_path,
                False,
            )

            # Create a state for all gestures
            for gesture in self._gestures:
                state_prim_path: str = self._builder.add_state_with_animation(
                    state_machine_prim_path, gesture.name, gesture.prim.GetPath(), False
                )
                # Connect all gesture nodes to the start and end node
                self._builder.add_compare_variable_transition(
                    start_state_prim_path,
                    state_prim_path,
                    self._gesture_state_variable_name,
                    "==",
                    gesture.name,
                )
                self._builder.add_compare_variable_transition(
                    state_prim_path,
                    start_state_prim_path,
                    self._gesture_state_variable_name,
                    "!=",
                    gesture.name,
                )
                self._builder.add_time_fraction_crossed_transition(
                    state_prim_path, end_state_prim_path
                )

            # Connect the end node with the start node
            self._builder.add_compare_variable_transition(
                end_state_prim_path,
                start_state_prim_path,
                self._gesture_state_variable_name,
                "==",
                "none",
            )

        gestures_state_machine(gestures_main_state_prim_path)

        # Create the posture state machines
        def postures_state_machines(main_state_machine_prim_path: str) -> None:
            # For each posture create a state machine
            posture_main_state_prim_paths: List[str] = []

            for posture_index, posture in enumerate(self._postures):
                # Set the first state or the state with a matching start state posture name as the start state
                is_start_state: bool = (
                    posture.name == self._start_state_posture_name or posture_index == 0
                )

                posture_main_state_prim_path: str = self._builder.add_empty_state(
                    main_state_machine_prim_path,
                    f"PostureMainState_{posture.name}",
                    is_start_state,
                )
                posture_main_state_prim_paths.append(posture_main_state_prim_path)

                variant_state_machine_prim_path: str = self._builder.add_state_machine_node(
                    posture_main_state_prim_path, "VariantStateMachine"
                )
                
                # Connect the variant state machine to the posture main state pose output
                self._builder.connect_nodes(variant_state_machine_prim_path, posture_main_state_prim_path, "inputs:pose")

                # Create the start and the end states
                # Note: We make the end node the start state and not the start state. With that, we will always randomize the variant state when this posture state is activated.
                start_state_prim_path: str = self._builder.add_state_with_animation(
                    variant_state_machine_prim_path,
                    "Start",
                    posture.prim_variants[0].GetPath(),
                    loop=False,
                    is_start_state=False,
                )

                end_state_prim_path: str = self._builder.add_state_with_animation(
                    variant_state_machine_prim_path,
                    "End",
                    posture.prim_variants[0].GetPath(),
                    loop=False,
                    is_start_state=True,
                )

                # For each posture variant create a state
                variant_state_prim_paths: List[str] = []
                for variant_index, outer_prim_variant in enumerate(
                    posture.prim_variants
                ):
                    outer_variant_state_prim_path: str = (
                        self._builder.add_state_with_animation(
                            variant_state_machine_prim_path,
                            outer_prim_variant.GetName(),
                            outer_prim_variant.GetPath(),
                            loop=False,
                            is_start_state=False,
                        )
                    )
                    variant_state_prim_paths.append(outer_variant_state_prim_path)

                # Connect all variant states with the end and the start state
                for variant_index, variant_prim in enumerate(posture.prim_variants):
                    self._builder.add_compare_variable_transition(
                        start_state_prim_path,
                        variant_state_prim_paths[variant_index],
                        self._variant_state_variable_name,
                        "==",
                        str(variant_index),
                    )

                    self._builder.add_time_fraction_crossed_transition(
                        variant_state_prim_paths[variant_index], end_state_prim_path
                    )

                # End to start transition
                self._builder.add_compare_variable_transition(
                    end_state_prim_path,
                    start_state_prim_path,
                    self._variant_state_variable_name,
                    "==",
                    "none",
                )

            # Connect all posture states in the main state machine with the gesture state
            for index, posture in enumerate(self._postures):
                posture_main_state_prim_path: str = posture_main_state_prim_paths[index]

                self._builder.add_compare_variable_transition(
                    posture_main_state_prim_path,
                    gestures_main_state_prim_path,
                    self._gesture_state_variable_name,
                    "!=",
                    "none",
                )

                self._builder.add_compare_two_variables_transition(
                    gestures_main_state_prim_path,
                    posture_main_state_prim_path,
                    self._gesture_state_variable_name,
                    "==",
                    "none",
                    "AND",
                    self._posture_state_variable_name,
                    "==",
                    # FIXME: For now ignore the case of the posture state for compatibility reasons
                    posture.name.lower(),
                    # posture.name,
                )

            # Connect all posture states in the main state machine together
            for outer_index, outer_posture in enumerate(self._postures):
                for inner_index, inner_posture in enumerate(self._postures):
                    if inner_posture.name != outer_posture.name:
                        # print_or_log(f"{inner_posture.name} -> {outer_posture.name}")
                        self._builder.add_compare_two_variables_transition(
                            posture_main_state_prim_paths[outer_index],
                            posture_main_state_prim_paths[inner_index],
                            self._gesture_state_variable_name,
                            "==",
                            "none",
                            "AND",
                            self._posture_state_variable_name,
                            "==",
                            # FIXME: For now ignore the case of the posture state for compatibility reasons
                            inner_posture.name.lower(),
                            # inner_posture.name,
                        )

        postures_state_machines(main_state_machine_prim_path)

        # Assign the new animation graph to the SkelRoot prim
        skel_root_prim = self._stage.GetPrimAtPath(self._config.skel_root_prim_path)
        skel_root_prim.GetRelationship("animationGraph").SetTargets(
            [self._config.anim_graph_prim_path]
        )

        # Assign the UsdSkeleton prim to the animation graph
        animation_graph_prim = self._stage.GetPrimAtPath(animation_graph_prim_path)
        animation_graph_prim.GetRelationship("skel:skeleton").SetTargets(
            [self._config.skeleton_prim_path]
        )

        return

        # Generate the eye blinking and A2F blending graph
        pose_provider_node_prim_path: str = self._builder.add_pose_provider_node(
            animation_graph_prim_path, "PoseProvider_A2F"
        )
        blinking_darting_animation_clip_node_prim_path: str = (
            self._builder.add_animation_clip_node(
                animation_graph_prim_path,
                "AnimationClip_Blinking_Darting",
                self._config.blinking_and_darting_animation_prim_path,
                loop=True,
            )
        )
        blend_blinking_darting_node_prim_path: str = self._builder.add_blend_node(
            animation_graph_prim_path, "Blend_Blinking"
        )
        blend_node_prim_path: str = self._builder.add_blend_node(
            animation_graph_prim_path, "Blend"
        )
        filter_node_prim_path: str = self._builder.add_filter_node(
            animation_graph_prim_path, "Filter"
        )

        read_joint_positions_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path, self._joint_positions_variable_name
            )
        )
        read_joint_rotations_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path, self._joint_rotations_variable_name
            )
        )
        read_root_position_displacement_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path,
                self._root_position_displacement_variable_name,
            )
        )
        read_root_rotation_displacement_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path,
                self._root_rotation_displacement_variable_name,
            )
        )
        read_blend_shape_weights_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path, self._blend_shape_weights_variable_name
            )
        )
        read_blinking_strength_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path, self._blinking_strength_variable_name
            )
        )
        read_blend_shape_strength_variable_node_prim_path: str = (
            self._builder.add_variable_node(
                animation_graph_prim_path, self._blend_shape_strength_variable_name
            )
        )

        self._builder.connect_nodes(
            read_blend_shape_weights_variable_node_prim_path,
            pose_provider_node_prim_path,
            "inputs:blendShapes",
        )
        self._builder.connect_nodes(
            read_joint_positions_variable_node_prim_path,
            pose_provider_node_prim_path,
            "inputs:jointsPositions",
        )
        self._builder.connect_nodes(
            read_joint_rotations_variable_node_prim_path,
            pose_provider_node_prim_path,
            "inputs:jointsRotations",
        )
        self._builder.connect_nodes(
            read_root_position_displacement_variable_node_prim_path,
            pose_provider_node_prim_path,
            "inputs:rootPositionDisplacement",
        )
        self._builder.connect_nodes(
            read_root_rotation_displacement_variable_node_prim_path,
            pose_provider_node_prim_path,
            "inputs:rootRotationDisplacement",
        )
        self._builder.connect_nodes(
            read_blinking_strength_variable_node_prim_path,
            blend_blinking_darting_node_prim_path,
            "inputs:blendWeight",
        )
        self._builder.connect_nodes(
            read_blend_shape_strength_variable_node_prim_path,
            blend_node_prim_path,
            "inputs:blendWeight",
        )

        # Connect blinking darting blend node inputs
        self._builder.connect_nodes(
            pose_provider_node_prim_path,
            blend_blinking_darting_node_prim_path,
            "inputs:pose0",
        )
        self._builder.connect_nodes(
            blinking_darting_animation_clip_node_prim_path,
            blend_blinking_darting_node_prim_path,
            "inputs:pose1",
        )

        # Connect filter node inputs
        self._builder.connect_nodes(
            blend_blinking_darting_node_prim_path, filter_node_prim_path, "inputs:pose"
        )

        # Connect main blend node inputs
        # TODO: Disconnect the automatic connection first or let this override it.
        self._builder.connect_nodes(
            main_state_machine_prim_path, blend_node_prim_path, "inputs:pose0"
        )
        self._builder.connect_nodes(
            filter_node_prim_path, blend_node_prim_path, "inputs:pose1"
        )

        # Connect the animation graph output
        self._builder.connect_nodes(
            blend_node_prim_path, animation_graph_prim_path, "inputs:pose"
        )

        print_or_log(
            "======================= ANIMATION GRAPH GENERATION DONE ======================="
        )

    def on_destroy(self) -> None:
        # print_or_log("AnimationGraphBuilderBehaviorScript: on_destroy")
        pass

    def on_stop(self) -> None:
        # print_or_log(f"AnimationGraphBuilderBehaviorScript: on_stop")
        self._skel_root_states.clear()
        
    # def on_play(self) -> None:
        # print_or_log(f"AnimationGraphBuilderBehaviorScript: on_play")

    def on_update(self, current_time: float, delta_time: float) -> None:
        # print_or_log(f"AnimationGraphBuilderBehaviorScript: on_update | Time: {current_time}")
        
        # Find all the skel roots including the duplicates created for the various streams
        skel_root_prim_name = Sdf.Path(self._config.skel_root_prim_path).elementString
        skel_root_parent_prim_path = Sdf.Path(self._config.skel_root_prim_path)
        skel_root_parent_parent_prim_path: Sdf.Path = skel_root_parent_prim_path.GetParentPath().GetParentPath()
        
        all_skel_root_parent_parent_child_prims = self._stage.GetPrimAtPath(skel_root_parent_parent_prim_path).GetAllChildren()
        
        # Ignore all prims that are not a replica of "Rig_Retarget"
        all_skel_root_parent_parent_child_prims = [prim for prim in all_skel_root_parent_parent_child_prims if str(prim.GetName()).startswith("Rig_Retarget") and str(prim.GetName()) != "Rig_Retarget"] 
        
        # Create paths that are pointing to the skel root
        all_skel_root_prim_paths: List[str] = [str(prim.GetPath()) + "/" + skel_root_prim_name for prim in all_skel_root_parent_parent_child_prims]
                
        # Remove unused states
        self._skel_root_states = {skel_root_prim_path: skel_root_state for skel_root_prim_path, skel_root_state in self._skel_root_states.items() if skel_root_prim_path in all_skel_root_prim_paths}
        
        for prim in all_skel_root_parent_parent_child_prims:
            skel_root_parent_prim_name: str = prim.GetName()

            assert skel_root_parent_prim_name.startswith("Rig_Retarget") 
            
            skel_root_prim_path: str = skel_root_parent_parent_prim_path.pathString + "/" + skel_root_parent_prim_name + "/" + skel_root_prim_name
            # print_or_log(f"Skel root path: {skel_root_prim_path}")
            
            # Initialize state if it does not exist yet
            if not skel_root_prim_path in self._skel_root_states:
                self._skel_root_states[skel_root_prim_path] = SkelRootState()
                self._skel_root_states[skel_root_prim_path].skel_root_parent_prim_name = skel_root_parent_prim_name
                        
        # Process all the skel roots
        for skel_root_prim_path, skel_root_state in self._skel_root_states.items():
            # print_or_log(f"Processing skel root: {skel_root_prim_path}") 
            # print_or_log(skel_root_state)
            self.update_with_skel_root(skel_root_prim_path, skel_root_state, current_time)
            
        assert len(self._skel_root_states) == len(all_skel_root_parent_parent_child_prims), f"{len(self._skel_root_states)} == {len(all_skel_root_parent_parent_child_prims)}"

    def update_with_skel_root(self, skel_root_prim_path: str, skel_root_state: SkelRootState, current_time: float) -> None:
        # Initialization phase
        
        # Note: We need to get the character at every iteration as we suspect that when deleting character instances,
        # the references get invalidated.
        character = ag.get_character(skel_root_prim_path)
        
        def print_or_log_stream(message: str) -> None:
            print_or_log(message, skel_root_state.skel_root_parent_prim_name)
        
        if character is None:
            print_or_log_stream("Failed to get the character instance! Skipping animation graph update.")
            return

        # Note: For some reason setting animation graph variables in the first iteration in which we have detected the 
        # new avatar prim does not work. As a workaround we initialize the variable twice in a row.
        if skel_root_state.initialization_count < 2:
            print_or_log_stream("Initializing animation graph variables")

            print_or_log_stream("Setting animation graph variables")
            character.set_variable(self._gesture_state_variable_name, "none")
            
            # character.set_variable(self._posture_state_variable_name, "Talking")
            # character.set_variable(self._posture_state_variable_name, "Idle")
            # character.set_variable(self._posture_state_variable_name, "Listening")
            # character.set_variable(self._posture_state_variable_name, "Thinking")
            # character.set_variable(self._posture_state_variable_name, "Attentive")
            character.set_variable(
                # FIXME: We currently normalize all variable names to lowercase for compatibility reasons. We should
                # undo this in the future for more robustness. The same change has also been applied to the animation
                # graph microservice endpoints.
                self._posture_state_variable_name, self._config.default_posture_name.lower()
                # self._posture_state_variable_name, self._config.default_posture_name
            )

            skel_root_state.variant_state_variable_value = 0
            character.set_variable(
                self._variant_state_variable_name,
                str(skel_root_state.variant_state_variable_value),
            )
            
            skel_root_state.initialization_count += 1
            
            if skel_root_state.initialization_count < 2:
                return 

        # Main phase
        
        # When we reach the end state, we reset the gesture state to "none". This will make the gesture state machine
        # transition to the start state, so that we are ready to transition to a gesture, when a new gesture event
        # comes in. At the same time this will also trigger a transition from the gesture state to the posture states.
        if character.is_node_active(self._anim_graph_end_clip_prim_path):
            # character.set_variable(self._gesture_state_variable_name, "none")
            # print_or_log_stream("END NODE")
            if current_time - skel_root_state.last_gesture_end_state_time < 0.1:
                print_or_log_stream(f"Skipping gesture end | Time: {current_time}")
            else:
                print_or_log_stream("GESTURES END NODE")
                
                character.set_variable(self._gesture_state_variable_name, "none")
                skel_root_state.last_gesture_end_state_time = current_time

        # if character.is_node_active(self._anim_graph_start_clip_prim_path):
        #     if current_time - skel_root_state.last_gesture_start_state_time < 0.1:
        #         print_or_log_stream(f"Skipping gesture start | Time: {current_time}")
        #     else:
        #         print_or_log_stream("GESTURES START NODE")
        #         skel_root_state.last_gesture_start_state_time = current_time

        # Logic to randomize the variant state
        for posture in self._postures:
            # Note: This might be triggered multiple times before the new variable has an effect
            # Note: Ideally we would get/read the animation graph variable to check if the transition has already happened
            # and if there is a mismatch with the current state we do not trigger a new update yet. To work around this
            # we simply use a minimum delta time between state changes.
            if character.is_node_active(
                f"{self._main_state_machine_prim_path}/PostureMainState_{posture.name}/VariantStateMachine/Start/AnimationClip"
            ):
                if current_time - skel_root_state.last_variant_start_state_time < 0.1:
                    print_or_log_stream(f"Skipping posture start | Posture: {posture.name} | Time: {current_time}")
                    continue

                print_or_log_stream(f"VARIANT START NODE | Posture: {posture.name} | Time: {current_time}")

                # TODO: Implement other iteration patterns: e.g. random or random of unvisited.
                skel_root_state.variant_state_variable_value = (
                    skel_root_state.variant_state_variable_value + 1
                ) % len(posture.prim_variants)
                print_or_log_stream(f"Variant state variable value: {skel_root_state.variant_state_variable_value} | Posture: {posture.name}")
                character.set_variable(
                    self._variant_state_variable_name,
                    str(skel_root_state.variant_state_variable_value),
                )
                skel_root_state.last_variant_start_state_time = current_time
                break

            # Note: This might be triggered multiple times before the new variable has an effect
            if character.is_node_active(
                f"{self._main_state_machine_prim_path}/PostureMainState_{posture.name}/VariantStateMachine/End/AnimationClip"
            ):
                if current_time - skel_root_state.last_variant_end_state_time < 0.1:
                    print_or_log_stream(f"Skipping posture end | Posture: {posture.name} | Time: {current_time}")
                    continue

                print_or_log_stream(f"VARIANT END NODE | Posture: {posture.name} | Time: {current_time}")

                character.set_variable(self._variant_state_variable_name, "none")
                skel_root_state.last_variant_end_state_time = current_time
                break