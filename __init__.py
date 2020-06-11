import bpy
from .pc_lib import pc_utils
from . import qi_ops
from . import qi_props
from . import qi_ui
from . import io_import_images_as_planes
from bpy.app.handlers import persistent

#Standard bl_info for Blender Add-ons
bl_info = {
    "name": "Quick Importer",
    "author": "Andrew Peel",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "Asset Library",
    "description": "This is a library that automates the process of importing models",
    "warning": "",
    "wiki_url": "",
    "category": "Asset Library",
}

@persistent
def load_library_on_file_load(scene=None):
    pc_utils.register_library(name="Quick Importer",
                              activate_id='qi.activate',
                              drop_id='qi.drop',
                              icon='IMPORT')

#Standard register/unregister Function for Blender Add-ons
def register():
    qi_ops.register()
    qi_props.register()
    qi_ui.register()
    io_import_images_as_planes.register()

    bpy.app.handlers.load_post.append(load_library_on_file_load)

def unregister():
    qi_ops.unregister()
    qi_props.unregister()
    qi_ui.unregister()
    io_import_images_as_planes.unregister()

    bpy.app.handlers.load_post.remove(load_library_on_file_load)  

    pc_utils.unregister_library("Quick Importer")

