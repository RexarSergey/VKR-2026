
import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences

class MapGeneratorPrefs(AddonPreferences):
    bl_idname = __package__

    # Путь к главному файлу конфигурации
    config_path: StringProperty(
        name="Config File Path",
        description="Path to the map_config.json file",
        subtype='FILE_PATH',
        default="C:/Users/Sergey/Desktop/todo/test/map_config.json" # Укажите свой путь по умолчанию
    )

def register():
    bpy.utils.register_class(MapGeneratorPrefs)

def unregister():
    bpy.utils.unregister_class(MapGeneratorPrefs)