import bpy
import json
import os
from . import generation_logic # Импортируем нашу логику

class SCENE_OT_add_layer_to_config(bpy.types.Operator):
    """Добавляет новый слой в конфигурацию и сохраняет в JSON"""
    bl_idname = "scene.add_layer_to_config"
    bl_label = "Add Layer to Config"
    
    def execute(self, context):
        scene_props = context.scene.generator_props
        prefs = context.preferences.addons[__package__].preferences
        
        # Создаем новый элемент в коллекции слоев
        new_layer = scene_props.layers.add()
        new_layer.name = f"Layer {len(scene_props.layers)}"
        # ... (здесь можно добавить копирование значений из "шаблона", если он будет) ...

        # Сохраняем всю конфигурацию в JSON файл
        save_config_to_json(scene_props, scene_props.map_save_path + "map_config.json")
        
        self.report({'INFO'}, f"Layer '{new_layer.name}' added and config saved.")
        return {'FINISHED'}

class SCENE_OT_generate_all(bpy.types.Operator):
    """Запускает генерацию всех слоев из текущей конфигурации"""
    bl_idname = "scene.generate_all"
    bl_label = "Generate All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene_props = context.scene.generator_props
        
        if not scene_props.layers:
            self.report({'ERROR'}, "No layers defined in the configuration.")
            return {'CANCELLED'}
            
        generation_logic.clear_scene()
        test = generation_logic.generate_all_layers_from_props(scene_props)
        if test != "Все збс":
            self.report({'ERROR'}, test)
            return {'CANCELLED'}
        
        self.report({'INFO'}, "Generation complete!")
        return {'FINISHED'}

# Вспомогательная функция для сохранения
def save_config_to_json(props, filepath):
    config_data = {
        "global_settings": {
            "map_size": props.map_size,
            "random_rotation": props.random_rotation,
            "master_mask_path": props.master_mask_path,
        },
        "layers": []
    }
    for layer in props.layers:
        layer_dict = {
            "type": layer.type,
            "name": layer.name,
            "target_color": [int(c * 255) for c in layer.target_color], # Конвертация 0-1 -> 0-255
            "color_tolerance": layer.color_tolerance,
        }
        if layer.type == 'scatter':
            layer_dict.update({
                "models_directory": layer.models_directory,
                "target_height": layer.target_height,
                "density": layer.density,
                "min_distance": layer.min_distance,
                "random_scale_min": layer.random_scale_min,
                "random_scale_max": layer.random_scale_max,
            })
        elif layer.type == 'surface':
            layer_dict.update({
                "subdivision_level": layer.subdivision_level,
            })
        config_data["layers"].append(layer_dict)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)


def register():
    bpy.utils.register_class(SCENE_OT_add_layer_to_config)
    bpy.utils.register_class(SCENE_OT_generate_all)

def unregister():
    bpy.utils.unregister_class(SCENE_OT_add_layer_to_config)
    bpy.utils.unregister_class(SCENE_OT_generate_all)