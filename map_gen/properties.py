# ====================================================================================
# --- ФАЙЛ: properties.py ---
# --- НАЗНАЧЕНИЕ: Определяет структуры данных для хранения настроек аддона. ---
# ====================================================================================

import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    FloatVectorProperty,
    EnumProperty,
    CollectionProperty
)
from bpy.types import PropertyGroup

# ====================================================================================
# --- КЛАССЫ ДАННЫХ ---
# ====================================================================================

# Класс для хранения свойств ОДНОГО слоя
class LayerPropertyGroup(PropertyGroup):
    name: StringProperty(name="Layer Name")
    type: EnumProperty(
        name="Type",
        items=[
            ('scatter', "Scatter", "Place scattered objects"),
            ('surface', "Surface", "Create a surface mesh")
        ],
        default='scatter'
    )
    models_directory: StringProperty(name="Models Folder", subtype='DIR_PATH')
    target_color: FloatVectorProperty(
        name="Target Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.0, 0.6, 0.0)
    )
    color_tolerance: FloatProperty(name="Color Tolerance", default=0.2, min=0.01, max=1.0)
    target_height: FloatProperty(name="Target Height", default=5.0)
    density: IntProperty(name="Density", default=30, min=1)
    min_distance: FloatProperty(name="Min Distance", default=4.0)
    random_scale_min: FloatProperty(name="Scale Min", default=0.8)
    random_scale_max: FloatProperty(name="Scale Max", default=1.2)
    subdivision_level: IntProperty(name="Subdivision Level", default=0)

# Класс для хранения ГЛОБАЛЬНЫХ настроек и списка слоев
class SceneGeneratorProperties(PropertyGroup):
    map_size: FloatProperty(name="Map Size", default=100.0)
    random_rotation: BoolProperty(name="Random Rotation", default=True)
    master_mask_path: StringProperty(name="Master Mask", subtype='FILE_PATH')
    map_save_path: StringProperty(name="Map Save Dest", subtype='DIR_PATH')
    
    # Коллекция (список) всех слоев
    layers: CollectionProperty(type=LayerPropertyGroup)
    # ИНДЕКС активного элемента в коллекции layers. Обязательно для UIList!
    layers_index: IntProperty(name="Layer Index", default=0)


# ====================================================================================
# --- ФУНКЦИИ РЕГИСТРАЦИИ (УЛУЧШЕННЫЕ) ---
# ====================================================================================

def register():
    bpy.utils.register_class(LayerPropertyGroup)
    bpy.utils.register_class(SceneGeneratorProperties)
    bpy.types.Scene.generator_props = bpy.props.PointerProperty(type=SceneGeneratorProperties)

def unregister():
    # Сначала удаляем свойство со сцены, если оно было добавлено
    if hasattr(bpy.types.Scene, "generator_props"):
        del bpy.types.Scene.generator_props
        
    # Теперь безопасно разрегистрируем классы.
    # Используем try-except, чтобы избежать падения, если модуль был загружен с ошибкой.
    try:
        bpy.utils.unregister_class(SceneGeneratorProperties)
    except (NameError, RuntimeError):
        pass
        
    try:
        bpy.utils.unregister_class(LayerPropertyGroup)
    except (NameError, RuntimeError):
        pass