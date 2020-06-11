import bpy,os,inspect
from bpy_extras.io_utils import ImportHelper

from bpy.types import (Header, 
                       Menu, 
                       Panel, 
                       Operator,
                       PropertyGroup)

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       EnumProperty,
                       CollectionProperty)
from . import qi_utils
from .pc_lib import pc_utils


class qi_OT_activate(Operator):
    bl_idname = "qi.activate"
    bl_label = "Activate Library"
    bl_options = {'UNDO'}
    
    library_name: StringProperty(name='Library Name')

    def execute(self, context):
        props = qi_utils.get_scene_props(context.scene)
        path = props.active_path
        if os.path.exists(path):
            pc_utils.update_file_browser_path(context,path)
        else:
            default_path = qi_utils.get_library_path()
            pc_utils.update_file_browser_path(context,default_path)

        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                for space in area.spaces:
                    if space.type == 'FILE_BROWSER':
                        params = space.params
                        params.use_filter = False
                        params.display_type = props.library_view

        return {'FINISHED'}


class qi_OT_drop(Operator):
    bl_idname = "qi.drop"
    bl_label = "Drop File"
    bl_options = {'UNDO'}
    
    filepath: StringProperty(name='Library Name')

    def execute(self, context):
        path, ext = os.path.splitext(self.filepath)

        #TODO: Add all possible import extensions
        if ext in {'.glb','.gltf'}:
            bpy.ops.qi.gltf(filepath=self.filepath)
        elif ext in {'.png','.jpg','.jpeg'}:
            bpy.ops.qiimport_image.to_plane(filepath=self.filepath)
            bpy.ops.qi.place_asset()
        else:
            pass

        return {'FINISHED'}


class qi_OT_set_active_path(Operator, ImportHelper):
    """Set Active Path"""
    bl_idname = 'qi.set_active_path'
    bl_label = 'Set Active Path'

    directory: bpy.props.StringProperty(name="Directory",subtype='DIR_PATH')

    def draw(self, context):
        layout = self.layout

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = qi_utils.get_scene_props(context.scene)
        props.active_path = self.directory
        return {'FINISHED'}


class qi_OT_change_library_path(Operator):
    bl_idname = "qi.change_library_path"
    bl_label = "Change Library Path"
    bl_options = {'UNDO'}
    
    filepath: StringProperty(name='Library Name')

    def execute(self, context):
        props = qi_utils.get_scene_props(context.scene)
        props.active_path = self.filepath
        return {'FINISHED'}


class qi_OT_save_active_path(Operator):
    bl_idname = "qi.save_active_path"
    bl_label = "Create Previews"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        props = qi_utils.get_scene_props(context.scene)
        if os.path.exists(props.active_path):
            return True
        else:
            return False

    def execute(self, context):
        props = qi_utils.get_scene_props(context.scene)
        props.save_active_path(context)
        return {'FINISHED'}


class qi_OT_create_previews(Operator):
    bl_idname = "qi.create_previews"
    bl_label = "Create Previews"
    bl_options = {'UNDO'}
    
    filepath: StringProperty(name='Library Name')

    def execute(self, context):
        dir_path, filename = os.path.split(self.filepath)
        path, ext = os.path.splitext(self.filepath)

        #IMPORT EACH FILE IN dir_path
        #Create Render based on templates
        #Save to Same Directory In Previews Folder
        #Set file path to new directory

        return {'FINISHED'}


class qi_ImportGLTF2(Operator, ImportHelper):
    """Load a glTF 2.0 file"""
    bl_idname = 'qi.gltf'
    bl_label = 'Import glTF File'

    # filter_glob: StringProperty(default="*.glb;*.gltf", options={'HIDDEN'})

    # files: CollectionProperty(
    #     name="File Path",
    #     type=bpy.types.OperatorFileListElement,
    # )

    loglevel: IntProperty(
        name='Log Level',
        description="Log Level")

    import_pack_images: BoolProperty(
        name='Pack images',
        description='Pack all images into .blend file',
        default=True
    )

    import_shading: EnumProperty(
        name="Shading",
        items=(("NORMALS", "Use Normal Data", ""),
               ("FLAT", "Flat Shading", ""),
               ("SMOOTH", "Smooth Shading", "")),
        description="How normals are computed during import",
        default="NORMALS")

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'import_pack_images')
        layout.prop(self, 'import_shading')

    def execute(self, context):
        return self.import_gltf2(context)

    def import_gltf2(self, context):
        import os

        # bpy.ops.object.select_all(action='SELECT')
        # bpy.ops.object.delete()

        self.set_debug_log()
        import_settings = self.as_keywords()

        self.unit_import(self.filepath, import_settings)
        # bpy.ops.object.select_all(action='SELECT')
        # bpy.ops.transform.resize(value=(.0254,.0254,.0254))
        # bpy.ops.view3d.view_selected(use_all_regions=False)
        # bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}

    def unit_import(self, filename, import_settings):
        import time
        from .io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
        from .io_scene_gltf2.blender.imp.gltf2_blender_gltf import BlenderGlTF

        self.gltf_importer = glTFImporter(filename, import_settings)
        success, txt = self.gltf_importer.read()
        if not success:
            self.report({'ERROR'}, txt)
            return {'CANCELLED'}
        success, txt = self.gltf_importer.checks()
        if not success:
            self.report({'ERROR'}, txt)
            return {'CANCELLED'}
        self.gltf_importer.log.critical("Data are loaded, start creating Blender stuff")
        start_time = time.time()
        BlenderGlTF.create(self.gltf_importer)
        elapsed_s = "{:.2f}s".format(time.time() - start_time)
        self.gltf_importer.log.critical("glTF import finished in " + elapsed_s)
        self.gltf_importer.log.removeHandler(self.gltf_importer.log_handler)

    def set_debug_log(self):
        import logging
        if bpy.app.debug_value == 0:
            self.loglevel = logging.CRITICAL
        elif bpy.app.debug_value == 1:
            self.loglevel = logging.ERROR
        elif bpy.app.debug_value == 2:
            self.loglevel = logging.WARNING
        elif bpy.app.debug_value == 3:
            self.loglevel = logging.INFO
        else:
            self.loglevel = logging.NOTSET


def event_is_place_asset(event):
    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        return True
    elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
        return True
    elif event.type == 'RET' and event.value == 'PRESS':
        return True
    else:
        return False

def event_is_cancel_command(event):
    if event.type in {'RIGHTMOUSE', 'ESC'}:
        return True
    else:
        return False

def event_is_pass_through(event):
    if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
        return True
    else:
        return False

class qi_OT_place_asset(bpy.types.Operator):
    bl_idname = "qi.place_asset"
    bl_label = "QI Place Asset"
    bl_description = "This enters into a placement mode"

    drawing_plane = None
    obj = None
    
    def execute(self, context):
        self.obj = context.object
        self.create_drawing_plane(context)
        
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def create_drawing_plane(self,context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0,0,0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100,100,1)

    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        selected_point, selected_obj = pc_utils.get_selection_point(context,event,exclude_objects=[self.obj])

        if event.ctrl:
            if event.mouse_y > event.mouse_prev_y:
                self.obj.rotation_euler.z += .1
            else:
                self.obj.rotation_euler.z -= .1
        else:
            self.position_object(selected_point,selected_obj)

        if event_is_place_asset(event):
            return self.finish(context)

        if event_is_cancel_command(event):
            return self.cancel_drop(context)
        
        if event_is_pass_through(event):
            return {'PASS_THROUGH'}        
        
        return {'RUNNING_MODAL'}

    def position_object(self,selected_point,selected_obj):
        self.obj.location = selected_point

    def cancel_drop(self,context):
        obj_list = []
        obj_list.append(self.drawing_plane)
        obj_list.append(self.obj)
        pc_utils.delete_obj_list(obj_list)
        return {'CANCELLED'}
    
    def finish(self,context):
        context.window.cursor_set('DEFAULT')
        if self.drawing_plane:
            pc_utils.delete_obj_list([self.drawing_plane])
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(True)  
        context.view_layer.objects.active = self.obj 
        context.area.tag_redraw()
        return {'FINISHED'}

classes = (
    qi_OT_activate,
    qi_OT_drop,
    qi_OT_set_active_path,
    qi_OT_change_library_path,
    qi_OT_save_active_path,
    qi_OT_create_previews,
    qi_ImportGLTF2,
    qi_OT_place_asset,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
