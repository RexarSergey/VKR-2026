bl_info = {
    "name": "Map Generator",
    "author": "You",
    "version": (1, 0, 4),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Map Generator",
    "category": "3D View",
    "description": "Generates scenes based on a color mask and configuration",
}

def register():
    # Порядок важен!
    from . import preferences
    from . import properties
    from . import operators
    from . import ui
    
    preferences.register()
    properties.register()
    operators.register()
    ui.register()

def unregister():
    # В обратном порядке
    from . import ui
    from . import operators
    from . import properties
    from . import preferences
    
    ui.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()