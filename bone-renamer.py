bl_info = {
    "name": "Bone Renamer",
    "author": "Nona-B.",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Edit Tab",
    "description": "Provides two methods for renaming bones: 'Incremental Rename' which renames the selected bone and its children by incrementing a number in the assigned name, and 'Alphabetical Rename' which renames the selected bones alphabetically. It also includes options to apply the new name to the root bone, to move '_L' or '_R' to the end of names, and to add '_Root' to the end of the root bone's name in 'Alphabetical Rename'.",
    "category": "3D View",
}

import bpy
import re
import string

def get_incremented_name(bone_name, increment):
    matches = re.findall(r'\d+', bone_name)
    
    if matches:
        last_match = matches[-1]
        new_number = str(int(last_match) + increment).zfill(len(last_match))
        return bone_name.replace(last_match, new_number, 1)

    return bone_name

def move_lr_to_end(name):
    if name.endswith("_L"):
        name = name[:-2] + "_L"
    elif name.endswith("_R"):
        name = name[:-2] + "_R"
    elif "_L_" in name:
        name = name.replace("_L_", "_") + "_L"
    elif "_R_" in name:
        name = name.replace("_R_", "_") + "_R"
    return name


def rename_children_bones(self, context):
    obj = bpy.context.edit_object
    armature = obj.data

    if obj.mode == 'EDIT':
        new_name = context.scene.new_name_value
        if not new_name or not re.search(r'\d', new_name):
            self.report({'ERROR'}, "The input name is either empty or does not contain a number.")
            return {'CANCELLED'}

        for bone in armature.edit_bones:
            if bone.select:
                bone.name = new_name
                for i, child in enumerate(bone.children_recursive):
                    child.name = get_incremented_name(bone.name, i+1)
                    
        return {'FINISHED'}

def alphabetical_rename(self, context):
    obj = bpy.context.edit_object
    armature = obj.data

    if obj.mode == 'EDIT':
        new_name = context.scene.new_name_value
        if not new_name:
            self.report({'ERROR'}, "The input name is empty.")
            return {'CANCELLED'}

        root_bone = None
        if context.scene.include_root_bone:
            root_bone = context.active_bone
            if root_bone:
                root_bone.name = new_name + "_Root"
                if context.scene.move_lr_to_end:
                    root_bone.name = move_lr_to_end(root_bone.name)
                selected_bones = [bone for bone in context.selected_bones if bone != root_bone]
            else:
                self.report({'ERROR'}, "No active bone selected.")
                return {'CANCELLED'}
        else:
            selected_bones = context.selected_bones.copy()

        selected_bones.sort(key=lambda x: x.name)
        
        for i, bone in enumerate(selected_bones):
            bone_name = f"{new_name}_{string.ascii_uppercase[i]}_00"
            if context.scene.move_lr_to_end and bone != root_bone:
                bone_name = move_lr_to_end(bone_name)
            bone.name = bone_name
            for j, child in enumerate(bone.children_recursive):
                child.name = get_incremented_name(bone.name, j+1)
                
        return {'FINISHED'}

class GetBoneNameOperator(bpy.types.Operator):
    bl_idname = "object.get_bone_name"
    bl_label = "Get Bone Name"
    bl_description = "Get the name of the currently active bone and insert it into the 'Name' input field."

    def execute(self, context):
        active_bone = context.active_bone
        if active_bone:
            context.scene.new_name_value = active_bone.name
        else:
            self.report({'ERROR'}, "No active bone selected.")
        return {'FINISHED'}

class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.incremental_rename"
    bl_label = "Incremental Rename"
    bl_description = "Rename the selected bone and its children by incrementing a number in the assigned name."

    def execute(self, context):
        return rename_children_bones(self, context)

class AlphabeticalOperator(bpy.types.Operator):
    bl_idname = "object.alphabetical_rename"
    bl_label = "Alphabetical Rename"
    bl_description = "Rename the selected bones alphabetically. If 'Include Root Bone' is checked, the new name is also applied to the active bone. If 'Move _L/_R to End' is checked, '_L' or '_R' in the new name is moved to the end."

    def execute(self, context):
        return alphabetical_rename(self, context)

class OBJECT_PT_custom_panel(bpy.types.Panel):
    bl_idname = "object.custom_panel"
    bl_label = "Bone Renamer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.get_bone_name")
        row = layout.row()
        row.prop(context.scene, "new_name_value", text="Name")
        layout.operator("object.incremental_rename")
        row = layout.row()
        row.prop(context.scene, "include_root_bone")
        row.prop(context.scene, "move_lr_to_end")
        layout.operator("object.alphabetical_rename")

def register():
    bpy.types.Scene.new_name_value = bpy.props.StringProperty(
        name="New Name",
        description="The new name to assign",
        default=""
    )

    bpy.types.Scene.include_root_bone = bpy.props.BoolProperty(
        name="Include Root Bone",
        description="Whether to include the root bone in the renaming process",
        default=False
    )

    bpy.types.Scene.move_lr_to_end = bpy.props.BoolProperty(
        name="Move _L/_R to End",
        description="Whether to move '_L' or '_R' in the new name to the end in 'Alphabetical Rename'",
        default=False
    )

    bpy.utils.register_class(GetBoneNameOperator)
    bpy.utils.register_class(SimpleOperator)
    bpy.utils.register_class(AlphabeticalOperator)
    bpy.utils.register_class(OBJECT_PT_custom_panel)

def unregister():
    del bpy.types.Scene.new_name_value
    del bpy.types.Scene.include_root_bone
    del bpy.types.Scene.move_lr_to_end

    bpy.utils.unregister_class(GetBoneNameOperator)
    bpy.utils.unregister_class(SimpleOperator)
    bpy.utils.unregister_class(AlphabeticalOperator)
    bpy.utils.unregister_class(OBJECT_PT_custom_panel)

if __name__ == "__main__":
    register()
