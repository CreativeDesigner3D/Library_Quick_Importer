import bpy
import os
from .pc_lib import pc_utils
from . import qi_utils

class FILEBROWSER_PT_qi_headers(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'UI'
    bl_label = "Library"
    bl_category = "Attributes"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        #Only display when active and File Browser is not open as separate window
        if len(context.area.spaces) > 1:
            pyclone = pc_utils.get_scene_props(context.scene)
            if pyclone.active_library_name == 'Quick Importer':
                return True   
        return False

    def draw(self, context):
        layout = self.layout
        props = qi_utils.get_scene_props(context.scene)
        props.draw(layout,context)


class QI_PT_library_settings(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_label = "Library"
    bl_region_type = 'HEADER'
    bl_ui_units_x = 20

    def draw(self, context):
        layout = self.layout
        props = qi_utils.get_scene_props(context.scene)
        props.draw_library_settings(layout, context)


class QI_MT_saved_paths(bpy.types.Menu):
    bl_label = "Library"

    def draw(self, context):
        layout = self.layout
        props = qi_utils.get_scene_props(context.scene)
        for directory in props.saved_paths:
            layout.operator('qi.change_library_path',text=directory.name,icon='FILE_FOLDER').filepath = directory.path


classes = (
    FILEBROWSER_PT_qi_headers,
    QI_PT_library_settings,
    QI_MT_saved_paths,
)

register, unregister = bpy.utils.register_classes_factory(classes)                