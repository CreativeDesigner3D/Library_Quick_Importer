import bpy
import os
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        UIList,
        )
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        CollectionProperty,
        EnumProperty,
        )
from mathutils import Vector

def update_active_path(self,context):
    bpy.ops.qi.activate()

def update_library_view(self,context):
    for area in context.screen.areas:
        if area.type == 'FILE_BROWSER':
            for space in area.spaces:
                if space.type == 'FILE_BROWSER':
                    params = space.params
                    params.use_filter = False
                    params.display_type = self.library_view


class Directory(PropertyGroup):
    path: StringProperty(name="Path")


class Import_Images_As_Planes(PropertyGroup):
    force_reload: BoolProperty(
        name="Force Reload", default=False,
        description="Force reloading of the image if already opened elsewhere in Blender"
    )

    image_sequence: BoolProperty(
        name="Animate Image Sequences", default=False,
        description="Import sequentially numbered images as an animated "
                    "image sequence instead of separate planes"
    )

    # -------------------------------------
    # Properties - Position and Orientation
    axis_id_to_vector = {
        'X+': Vector(( 1,  0,  0)),
        'Y+': Vector(( 0,  1,  0)),
        'Z+': Vector(( 0,  0,  1)),
        'X-': Vector((-1,  0,  0)),
        'Y-': Vector(( 0, -1,  0)),
        'Z-': Vector(( 0,  0, -1)),
    }

    offset: BoolProperty(name="Offset Planes", default=True, description="Offset Planes From Each Other")

    OFFSET_MODES = (
        ('X+', "X+", "Side by Side to the Left"),
        ('Y+', "Y+", "Side by Side, Downward"),
        ('Z+', "Z+", "Stacked Above"),
        ('X-', "X-", "Side by Side to the Right"),
        ('Y-', "Y-", "Side by Side, Upward"),
        ('Z-', "Z-", "Stacked Below"),
    )
    offset_axis: EnumProperty(
        name="Orientation", default='X+', items=OFFSET_MODES,
        description="How planes are oriented relative to each others' local axis"
    )

    offset_amount: FloatProperty(
        name="Offset", soft_min=0, default=0.1, description="Space between planes",
        subtype='DISTANCE', unit='LENGTH'
    )

    AXIS_MODES = (
        ('X+', "X+", "Facing Positive X"),
        ('Y+', "Y+", "Facing Positive Y"),
        ('Z+', "Z+ (Up)", "Facing Positive Z"),
        ('X-', "X-", "Facing Negative X"),
        ('Y-', "Y-", "Facing Negative Y"),
        ('Z-', "Z- (Down)", "Facing Negative Z"),
        ('CAM', "Face Camera", "Facing Camera"),
        ('CAM_AX', "Main Axis", "Facing the Camera's dominant axis"),
    )
    align_axis: EnumProperty(
        name="Align", default='CAM_AX', items=AXIS_MODES,
        description="How to align the planes"
    )
    # prev_align_axis is used only by update_size_model
    prev_align_axis: EnumProperty(
        items=AXIS_MODES + (('NONE', '', ''),), default='NONE', options={'HIDDEN', 'SKIP_SAVE'})
    align_track: BoolProperty(
        name="Track Camera", default=False, description="Always face the camera"
    )

    # -----------------
    # Properties - Size
    def update_size_mode(self, context):
        """If sizing relative to the camera, always face the camera"""
        if self.size_mode == 'CAMERA':
            self.prev_align_axis = self.align_axis
            self.align_axis = 'CAM'
        else:
            # if a different alignment was set revert to that when
            # size mode is changed
            if self.prev_align_axis != 'NONE':
                self.align_axis = self.prev_align_axis
                self._prev_align_axis = 'NONE'

    SIZE_MODES = (
        ('ABSOLUTE', "Absolute", "Use absolute size"),
        ('CAMERA', "Camera Relative", "Scale to the camera frame"),
        ('DPI', "Dpi", "Use definition of the image as dots per inch"),
        ('DPBU', "Dots/BU", "Use definition of the image as dots per Blender Unit"),
    )
    size_mode: EnumProperty(
        name="Size Mode", default='ABSOLUTE', items=SIZE_MODES,
        update=update_size_mode,
        description="How the size of the plane is computed")

    FILL_MODES = (
        ('FILL', "Fill", "Fill camera frame, spilling outside the frame"),
        ('FIT', "Fit", "Fit entire image within the camera frame"),
    )
    fill_mode: EnumProperty(name="Scale", default='FILL', items=FILL_MODES,
                             description="How large in the camera frame is the plane")

    height: FloatProperty(name="Height", description="Height of the created plane",
                           default=1.0, min=0.001, soft_min=0.001, subtype='DISTANCE', unit='LENGTH')

    factor: FloatProperty(name="Definition", min=1.0, default=600.0,
                           description="Number of pixels per inch or Blender Unit")

    # ------------------------------
    # Properties - Material / Shader
    SHADERS = (
        ('PRINCIPLED',"Principled","Principled Shader"),
        ('SHADELESS', "Shadeless", "Only visible to camera and reflections"),
        ('EMISSION', "Emit", "Emission Shader"),
    )
    shader: EnumProperty(name="Shader", items=SHADERS, default='PRINCIPLED', description="Node shader to use")

    emit_strength: FloatProperty(
        name="Strength", min=0.0, default=1.0, soft_max=10.0,
        step=100, description="Brightness of Emission Texture")

    overwrite_material: BoolProperty(
        name="Overwrite Material", default=True,
        description="Overwrite existing Material (based on material name)")

    compositing_nodes: BoolProperty(
        name="Setup Corner Pin", default=False,
        description="Build Compositor Nodes to reference this image "
                    "without re-rendering")

    # ------------------
    # Properties - Image
    use_transparency: BoolProperty(
        name="Use Alpha", default=True,
        description="Use alpha channel for transparency")

    t = bpy.types.Image.bl_rna.properties["alpha_mode"]
    alpha_mode_items = tuple((e.identifier, e.name, e.description) for e in t.enum_items)
    alpha_mode: EnumProperty(
        name=t.name, items=alpha_mode_items, default=t.default,
        description=t.description)

    t = bpy.types.ImageUser.bl_rna.properties["use_auto_refresh"]
    use_auto_refresh: BoolProperty(name=t.name, default=True, description=t.description)

    relative: BoolProperty(name="Relative Paths", default=True, description="Use relative file paths")

    def draw_import_config(self, context, layout):
        # --- Import Options --- #
        box = layout.box()

        box.label(text="Import Options:", icon='IMPORT')
        row = box.row()
        row.active = bpy.data.is_saved
        row.prop(self, "relative")

        box.prop(self, "force_reload")
        box.prop(self, "image_sequence")

    def draw_material_config(self, context, layout):
        # --- Material / Rendering Properties --- #
        box = layout.box()

        box.label(text="Compositing Nodes:", icon='RENDERLAYERS')
        box.prop(self, "compositing_nodes")

        box.label(text="Material Settings:", icon='MATERIAL')

        row = box.row()
        row.prop(self, 'shader', expand=True)
        if self.shader == 'EMISSION':
            box.prop(self, "emit_strength")

        engine = context.scene.render.engine
        if engine not in ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
            box.label(text="%s is not supported" % engine, icon='ERROR')

        box.prop(self, "overwrite_material")

        box.label(text="Texture Settings:", icon='TEXTURE')
        row = box.row()
        row.prop(self, "use_transparency")
        sub = row.row()
        sub.active = self.use_transparency
        sub.prop(self, "alpha_mode", text="")
        box.prop(self, "use_auto_refresh")

    def draw_spatial_config(self, context, layout):
        # --- Spatial Properties: Position, Size and Orientation --- #
        box = layout.box()

        box.label(text="Position:", icon='SNAP_GRID')
        box.prop(self, "offset")
        col = box.column()
        row = col.row()
        row.prop(self, "offset_axis", expand=True)
        row = col.row()
        row.prop(self, "offset_amount")
        col.enabled = self.offset

        box.label(text="Plane dimensions:", icon='ARROW_LEFTRIGHT')
        row = box.row()
        row.prop(self, "size_mode", expand=True)
        if self.size_mode == 'ABSOLUTE':
            box.prop(self, "height")
        elif self.size_mode == 'CAMERA':
            row = box.row()
            row.prop(self, "fill_mode", expand=True)
        else:
            box.prop(self, "factor")

        box.label(text="Orientation:")
        row = box.row()
        row.enabled = 'CAM' not in self.size_mode
        row.prop(self, "align_axis")
        row = box.row()
        row.enabled = 'CAM' in self.align_axis
        row.alignment = 'RIGHT'
        row.prop(self, "align_track")

    def draw(self, context, layout):

        # Draw configuration sections
        self.draw_import_config(context,layout)
        self.draw_material_config(context,layout)
        self.draw_spatial_config(context,layout)


class qi_Scene_Props(PropertyGroup):
    active_path: StringProperty(name="Active Path",update=update_active_path)
    output_path: StringProperty(name="Output Path",subtype='DIR_PATH')

    import_images_as_planes: PointerProperty(name="Import Images As Places",type=Import_Images_As_Planes)

    saved_paths: CollectionProperty(name="Saved Paths",type=Directory)

    library_view: EnumProperty(name="Library View",
                               items=[('THUMBNAIL',"Thumbnail","Thumbnail View"),
                                      ('LIST_VERTICAL',"List","List View")],
                               default='THUMBNAIL',
                               update=update_library_view)

    library_tabs: EnumProperty(name="Library tabs",
                               items=[('GENERAL',"General","General"),
                                      ('IMAGES',"Images","Images as Planes"),
                                      ('OBJ',"OBJ","Obj"),
                                      ('FBX',"FBX","Fbx"),
                                      ('GLTF2',"GLTF2","Gltf2"),],
                               default='GENERAL')

    def save_active_path(self,context):
        directory = self.saved_paths.add()
        directory.path = self.active_path
        directory.name = os.path.basename(os.path.normpath(self.active_path))

    def draw_library_settings(self,layout,context):
        col = layout.column(align=True)

        row = col.row(align=True)
        row.scale_y = 1.3
        row.prop_enum(self, "library_tabs", 'GENERAL', icon='TOOL_SETTINGS', text="General") 
        row.prop_enum(self, "library_tabs", 'IMAGES', icon='TOOL_SETTINGS', text="Images") 
        row.prop_enum(self, "library_tabs", 'OBJ', icon='TOOL_SETTINGS', text="OBJ")    
        row.prop_enum(self, "library_tabs", 'FBX', icon='TOOL_SETTINGS', text="FBX")    
        row.prop_enum(self, "library_tabs", 'GLTF2', icon='TOOL_SETTINGS', text="GLTF2")    

        box = col.box()

        if self.library_tabs == 'GENERAL':
            row = box.row()
            row.prop(self,'library_view',expand=True)

        if self.library_tabs == 'IMAGES':
            self.import_images_as_planes.draw(context,box)     

        if self.library_tabs == 'OBJ':
            pass #TODO

    def draw(self,layout,context):
        row = layout.row()
        row.scale_y = 1.3
        row.label(text="Quick Importer V0.1")
        row.popover(panel="QI_PT_library_settings",text="",icon='SETTINGS')

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.prop(self,'active_path')
        row.operator('qi.set_active_path',text="",icon='FILE_FOLDER')

        if len(self.saved_paths) == 0:
            row = layout.row(align=True)
            row.scale_y = 1.3            
            row.operator('qi.save_active_path',text="Save Active Path",icon='ADD')
        else:
            row = layout.row(align=True)
            row.scale_y = 1.3
            row.menu('QI_MT_saved_paths',text="Select Saved Path",icon='FILEBROWSER') 
            row.operator('qi.save_active_path',text="",icon='ADD') 
            row.operator('qi.set_output_path',text="",icon='EXPORT') 

        # if os.path.exists(self.active_path):
        #     row = layout.row(align=True)
        #     row.scale_y = 1.3
        #     row.operator('qi.create_previews',text="Render Scenes",icon='FILE_IMAGE')
            
    @classmethod
    def register(cls):
        bpy.types.Scene.qi = PointerProperty(
            name="Quick Importer Props",
            description="Quick Importer Props",
            type=cls,
        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.qi

classes = (
    Directory,
    Import_Images_As_Planes,
    qi_Scene_Props,
)

register, unregister = bpy.utils.register_classes_factory(classes)        