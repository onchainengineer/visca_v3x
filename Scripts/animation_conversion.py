omni.kit.commands.execute(
 'CreateRetargetAnimationsCommand',
  source_skeleton_path='YOUR_SKELETON_PATH', #The Skeleton prim your animation is based on (must have retargeting tags)
  target_skeleton_path='/World/Animations/Rig_Retarget/character/OUTPUT/root_JNT/root_JNT', #The default Skeleton
  source_animation_paths=['YOUR_ANIMATION_PATH'], #Your SkelAnimation prim
  target_animation_parent_path='/World/Animations/Animations/TARGET_STATE_SCOPE', #The scope your animation belongs in (eg. /World/Animations/Animations/Postures/Idle)
    set_root_identity=False
)
print("Animation retargeted.")

