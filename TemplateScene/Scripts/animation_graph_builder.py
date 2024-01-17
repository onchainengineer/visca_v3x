import omni.anim.graph.core as ag
import omni.usd

import random

from typing import List, Optional, Tuple, Any

from pxr import Gf, Usd, UsdSkel, UsdGeom, Tf, Sdf


class AnimationGraphBuilder:
    def __init__(self, default_transition_time: float = 0.8) -> None:
        self._stage: Usd.Stage

        # Parameters
        self._default_transition_time: float = default_transition_time
        self._ui_position_noise_range: float = 300.0

        # Workspace
        self._stage: Usd.Stage = omni.usd.get_context().get_stage()

    # TODO: Use Sdf.Path instead of str
    def clear_prim(self, prim_path: str) -> None:
        self._stage.RemovePrim(prim_path)

    def add_state_machine_node(self, parent_prim_path: str, state_machine_name: str) -> str:
        state_machine_prim_path: str = parent_prim_path + "/" + state_machine_name

        state_machine = ag.AnimGraphSchema.StateMachine.Define(
            self._stage, state_machine_prim_path
        )
        state_machine: Usd.Prim = self._stage.GetPrimAtPath(state_machine_prim_path)

        attribute: Usd.Attribute = state_machine.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return state_machine_prim_path

    def add_animation_graph(
        self,
        parent_prim_path: str,
        animation_graph_name: str,
        variable_names_and_types: List[Tuple[str, Sdf.ValueTypeName, Any]],
    ) -> str:
        animation_graph_prim_path: str = parent_prim_path + "/" + animation_graph_name

        # Create a new AnimationGraph
        graph = ag.AnimGraphSchema.AnimationGraph.Define(
            self._stage, animation_graph_prim_path
        )

        # Create/set a animation graph variable
        # Note: We need to get the AnimationGraph prim again, otherwise creating an attribute freezes program execution
        graph = self._stage.GetPrimAtPath(animation_graph_prim_path)
        for variable_name, variable_type, variable_value in variable_names_and_types:
            attribute: Usd.Attribute = graph.CreateAttribute(
                "anim:graph:variable:" + variable_name, variable_type
            )
            attribute.Set(variable_value)

        return animation_graph_prim_path

    def add_empty_state(
        self, state_machine_prim_path: str, prim_name: str, is_start_state: bool = False
    ) -> str:
        state_prim_path: str = state_machine_prim_path + "/" + prim_name

        state_prim = ag.AnimGraphSchema.State.Define(self._stage, state_prim_path)
        state_prim = self._stage.GetPrimAtPath(state_prim_path)

        # Random ui position
        attribute: Usd.Attribute = state_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        # Set start state
        if is_start_state:
            self.connect_nodes(
                state_prim_path, state_machine_prim_path, "inputs:startState"
            )

        return state_prim_path

    def add_state_with_animation(
        self,
        state_machine_prim_path: str,
        prim_name: str,
        animation_prim_path: str,
        loop: bool = True,
        is_start_state: bool = False,
    ) -> str:
        state_prim_path: str = self.add_empty_state(
            state_machine_prim_path, prim_name, is_start_state
        )

        clip_prim_path: str = self.add_animation_clip_node(
            state_prim_path, "AnimationClip", animation_prim_path, loop
        )

        self.connect_nodes(clip_prim_path, state_prim_path, "inputs:pose")

        return state_prim_path

    def _transition_base_prim_path(
        self,
        from_state_prim_path: str,
        to_state_prim_path: str,
    ) -> str:
        base_from_prim_path: str = from_state_prim_path.rsplit("/", 1)[0]
        base_to_prim_path: str = to_state_prim_path.rsplit("/", 1)[0]

        assert base_from_prim_path == base_to_prim_path

        base_prim_path: str = base_from_prim_path + "/"

        return base_prim_path

    def add_pose_provider_node(self, parent_prim_path: str, prim_name: str) -> str:
        pose_provider_prim_path: str = parent_prim_path + "/" + prim_name

        pose_provider_prim = ag.AnimGraphSchema.PoseProvider.Define(
            self._stage, pose_provider_prim_path
        )
        clip_pose_provider_prim = self._stage.GetPrimAtPath(pose_provider_prim_path)

        attribute: Usd.Attribute = clip_pose_provider_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return pose_provider_prim_path

    def add_animation_clip_node(
        self,
        parent_prim_path: str,
        prim_name: str,
        animation_prim_path: str,
        loop: bool = True,
    ) -> str:
        clip_prim_path: str = parent_prim_path + "/" + prim_name

        clip_prim = ag.AnimGraphSchema.AnimationClip.Define(self._stage, clip_prim_path)
        clip_prim = self._stage.GetPrimAtPath(clip_prim_path)
        clip_prim.GetAttribute("inputs:loop").Set(loop)

        clip_prim.GetRelationship("inputs:animationSource").SetTargets(
            [animation_prim_path]
        )

        attribute: Usd.Attribute = clip_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return clip_prim_path

    def add_blend_node(self, parent_prim_path: str, prim_name: str) -> str:
        blend_prim_path: str = parent_prim_path + "/" + prim_name

        blend_prim = ag.AnimGraphSchema.Blend.Define(self._stage, blend_prim_path)
        blend_prim = self._stage.GetPrimAtPath(blend_prim_path)

        attribute: Usd.Attribute = blend_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return blend_prim_path

    def add_filter_node(self, parent_prim_path: str, prim_name: str) -> str:
        filter_prim_path: str = parent_prim_path + "/" + prim_name

        filter_prim = ag.AnimGraphSchema.Filter.Define(self._stage, filter_prim_path)
        filter_prim = self._stage.GetPrimAtPath(filter_prim_path)

        attribute: Usd.Attribute = filter_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return filter_prim_path

    def add_variable_node(self, parent_prim_path: str, variable_name: str) -> str:
        read_variable_prim_path: str = parent_prim_path + "/" + "Read_" + variable_name

        read_variable_prim = ag.AnimGraphSchema.ReadVariable.Define(
            self._stage, read_variable_prim_path
        )
        read_variable_prim = self._stage.GetPrimAtPath(read_variable_prim_path)
        read_variable_prim.GetAttribute("inputs:variableName").Set(variable_name)

        attribute: Usd.Attribute = read_variable_prim.CreateAttribute(
            "ui:position", Sdf.ValueTypeNames.Float2
        ).Set(
            Gf.Vec2f(
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
                random.uniform(
                    -self._ui_position_noise_range, self._ui_position_noise_range
                ),
            )
        )

        return read_variable_prim_path

    def connect_nodes(
        self,
        source_prim_path: str,
        target_prim_path: str,
        target_relationship_name: str,
    ) -> None:
        target_prim = self._stage.GetPrimAtPath(target_prim_path)
        target_prim.GetRelationship(target_relationship_name).SetTargets(
            [source_prim_path]
        )

    def add_compare_variable_transition(
        self,
        from_state_prim_path: str,
        to_state_prim_path: str,
        variable: str,
        operator: str,
        value: str,
        duration: Optional[float] = None,
    ) -> str:
        """
        operator: "==" or "!="
        """

        if duration is None:
            duration = self._default_transition_time

        base_prim_path: str = self._transition_base_prim_path(
            from_state_prim_path, to_state_prim_path
        )

        transition_prim_path: str = (
            base_prim_path
            + f"Transition_{str.split(from_state_prim_path, '/')[-1]}_{str.split(to_state_prim_path, '/')[-1]}"
        )

        # Create a Transition
        transition = ag.AnimGraphSchema.Transition.Define(
            self._stage, transition_prim_path
        )
        transition = self._stage.GetPrimAtPath(transition_prim_path)
        transition.GetAttribute("inputs:durationTime").Set(duration)

        self.connect_nodes(from_state_prim_path, transition_prim_path, "inputs:state")
        self.connect_nodes(to_state_prim_path, transition_prim_path, "outputs:state")

        # Create a Condition
        condition = ag.AnimGraphSchema.ConditionCompareVariable.Define(
            self._stage, transition_prim_path + "/Condition"
        )
        condition: Usd.Prim = self._stage.GetPrimAtPath(
            transition_prim_path + "/Condition"
        )

        condition.GetAttribute("inputs:variableName").Set(variable)
        condition.GetAttribute("inputs:operator").Set(operator)
        # Note: For some reason we cannot simply set the attribute value. So, we simply recreate it.
        condition.CreateAttribute("inputs:value", Sdf.ValueTypeNames.String)
        condition.GetAttribute("inputs:value").Set(value)

        self.connect_nodes(
            transition_prim_path + "/Condition",
            transition_prim_path,
            "inputs:condition",
        )

        return transition_prim_path

    def add_compare_two_variables_transition(
        self,
        from_state_prim_path: str,
        to_state_prim_path: str,
        variable_a: str,
        operator_a: str,
        value_a: str,
        logical_operator: str,
        variable_b: str,
        operator_b: str,
        value_b: str,
        duration: Optional[float] = None,
    ) -> str:
        """
        operator: "==" or "!="
        logical_operator: "AND" or "OR"
        """

        if duration is None:
            duration = self._default_transition_time

        base_prim_path: str = self._transition_base_prim_path(
            from_state_prim_path, to_state_prim_path
        )

        transition_prim_path: str = (
            base_prim_path
            + f"Transition_{str.split(from_state_prim_path, '/')[-1]}_{str.split(to_state_prim_path, '/')[-1]}"
        )

        # Create a Transition
        transition = ag.AnimGraphSchema.Transition.Define(
            self._stage, transition_prim_path
        )
        transition = self._stage.GetPrimAtPath(transition_prim_path)
        transition.GetAttribute("inputs:durationTime").Set(duration)

        self.connect_nodes(from_state_prim_path, transition_prim_path, "inputs:state")
        self.connect_nodes(to_state_prim_path, transition_prim_path, "outputs:state")

        # Create a Condition (A)
        condition_a_prim_path: str = transition_prim_path + "/ConditionA"
        condition_a = ag.AnimGraphSchema.ConditionCompareVariable.Define(
            self._stage, condition_a_prim_path
        )
        condition_a: Usd.Prim = self._stage.GetPrimAtPath(condition_a_prim_path)
        condition_a.GetAttribute("inputs:variableName").Set(variable_a)
        condition_a.GetAttribute("inputs:operator").Set(operator_a)
        # Note: For some reason we cannot simply set the attribute value. So, we simply recreate it.
        condition_a.CreateAttribute("inputs:value", Sdf.ValueTypeNames.String)
        condition_a.GetAttribute("inputs:value").Set(value_a)

        # Create a Condition (B)
        condition_b_prim_path: str = transition_prim_path + "/ConditionB"
        condition_b = ag.AnimGraphSchema.ConditionCompareVariable.Define(
            self._stage, condition_b_prim_path
        )
        condition_b: Usd.Prim = self._stage.GetPrimAtPath(condition_b_prim_path)
        condition_b.GetAttribute("inputs:variableName").Set(variable_b)
        condition_b.GetAttribute("inputs:operator").Set(operator_b)
        # Note: For some reason we cannot simply set the attribute value. So, we simply recreate it.
        condition_b.CreateAttribute("inputs:value", Sdf.ValueTypeNames.String)
        condition_b.GetAttribute("inputs:value").Set(value_b)

        # Create AND condition
        condition_and_prim_path: str = transition_prim_path + "/ConditionAnd"
        condition_and = ag.AnimGraphSchema.ConditionAND.Define(
            self._stage, condition_and_prim_path
        )
        condition_and: Usd.Prim = self._stage.GetPrimAtPath(condition_and_prim_path)

        self.connect_nodes(
            condition_a_prim_path, condition_and_prim_path, "inputs:condition0"
        )
        self.connect_nodes(
            condition_b_prim_path, condition_and_prim_path, "inputs:condition1"
        )

        self.connect_nodes(
            condition_and_prim_path, transition_prim_path, "inputs:condition"
        )

        return transition_prim_path

    def add_time_fraction_crossed_transition(
        self,
        from_state_prim_path: str,
        to_state_prim_path: str,
        fraction: float = 0.95,
        duration: Optional[float] = None,
    ) -> str:
        if duration is None:
            duration = self._default_transition_time

        base_prim_path: str = self._transition_base_prim_path(
            from_state_prim_path, to_state_prim_path
        )

        transition_prim_path: str = (
            base_prim_path
            + f"Transition_{str.split(from_state_prim_path, '/')[-1]}_{str.split(to_state_prim_path, '/')[-1]}"
        )

        # Create a Transition
        transition = ag.AnimGraphSchema.Transition.Define(
            self._stage, transition_prim_path
        )
        transition = self._stage.GetPrimAtPath(transition_prim_path)
        transition.GetAttribute("inputs:durationTime").Set(duration)

        self.connect_nodes(from_state_prim_path, transition_prim_path, "inputs:state")
        self.connect_nodes(to_state_prim_path, transition_prim_path, "outputs:state")

        # Create a Condition
        condition_prim_path: str = transition_prim_path + "/Condition"
        condition = ag.AnimGraphSchema.ConditionTimeFractionCrossed.Define(
            self._stage, condition_prim_path
        )
        condition: Usd.Prim = self._stage.GetPrimAtPath(condition_prim_path)
        condition.GetAttribute("inputs:fraction").Set(fraction)

        self.connect_nodes(
            condition_prim_path, transition_prim_path, "inputs:condition"
        )

        return transition_prim_path
