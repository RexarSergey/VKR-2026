# ====================================================================================
# --- ФАЙЛ: generation_logic.py ---
# --- НАЗНАЧЕНИЕ: Содержит всю логику генерации сцены. ---
# --- Этот модуль не зависит от UI, он только выполняет вычисления. ---
# ====================================================================================

import bpy
import random
import math
import mathutils
import os
from collections import deque

# ====================================================================================
# --- 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (скопированы из generator.txt) ---
# ====================================================================================

def clear_scene():
    """Полностью очищает сцену от сгенерированных объектов."""
    print("--- Шаг 1: Полная очистка сцены...")
    # Удаляем коллекции, созданные аддоном
    collections_to_delete = [col for col in bpy.data.collections if "Generated_" in col.name]
    for col in collections_to_delete:
        # Сначала удаляем все объекты из коллекции
        for obj in col.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        # Затем удаляем саму коллекцию
        bpy.data.collections.remove(col)
        
    # Удаляем все остальные объекты (на случай, если что-то осталось)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Очищаем "сирот" (данные, которые не используются)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for material in bpy.data.materials:
        if material.users == 0:
            bpy.data.materials.remove(material)
    print("Сцена полностью очищена.")

def normalize_model_scale(obj, target_height):
    """Масштабирует модель до заданной высоты."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    current_height = obj.dimensions.z
    if current_height == 0: return
    scale_factor = target_height / current_height
    obj.scale = (scale_factor, scale_factor, scale_factor)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def load_and_normalize_models(directory_path, target_height):
    """Загружает все FBX модели из подпапок и нормализует их."""
    # if not os.path.isdir(directory_path): return []
    imported_models = []
    # try:
    #     all_items = os.listdir(directory_path)
    # except FileNotFoundError:
    #     return []
    # for item_name in all_items:
    #     item_path = os.path.join(directory_path, item_name)
    #     if os.path.isdir(item_path):
    #         fbx_filename = f"{item_name}.fbx"
    #         fbx_path = os.path.join(item_path, fbx_filename)
            # if os.path.isfile(fbx_path):
    fbx_path = 'C:\\Users\\Sergey\\Downloads\\grass1.fbx'
    if os.path.isfile(fbx_path):
        bpy.ops.object.select_all(action='DESELECT')
        try:
            bpy.ops.import_scene.fbx(filepath=fbx_path)
        except Exception:
            # continue
            return imported_models
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                normalize_model_scale(obj, target_height)
                obj.name = f"Template_"
                obj.hide_viewport = True
                obj.hide_render = True
                imported_models.append(obj)
                break
    return imported_models

def create_instance(source_obj, location, target_collection):
    """Создает экземпляр объекта в указанной коллекции."""
    new_obj = source_obj.copy()
    new_obj.data = source_obj.data.copy()
    new_obj.location = location
    target_collection.objects.link(new_obj)
    new_obj.hide_viewport = False
    new_obj.hide_set(False)
    return new_obj

def check_collision(new_loc, existing_locations, min_dist_sq):
    """Проверяет, не пересекается ли новая точка с существующими."""
    for loc in existing_locations:
        if (new_loc - loc).length_squared < min_dist_sq:
            return True
    return False

def load_mask_image(image_path):
    """Загружает изображение маски."""
    if not os.path.isfile(image_path): return None
    try:
        return bpy.data.images.load(image_path, check_existing=True)
    except Exception:
        return None

# ====================================================================================
# --- 2. ФУНКЦИИ ДЛЯ РАБОТЫ С ЦВЕТОМ НА МАСТЕР-МАСКЕ ---
# ====================================================================================

def is_point_on_color_mask(world_x, world_y, mask_image, map_size, target_color, tolerance):
    """Проверяет, находится ли мировая координата на пикселе нужного цвета."""
    rel_x = (world_x + map_size / 2) / map_size
    rel_y = (world_y + map_size / 2) / map_size
    img_x = int(rel_x * mask_image.size[0])
    img_y = int(rel_y * mask_image.size[1])
    if not (0 <= img_x < mask_image.size[0] and 0 <= img_y < mask_image.size[1]): return False
    
    pixel_index = (img_y * mask_image.size[0] + img_x) * 4
    pixel_color = (
        mask_image.pixels[pixel_index],
        mask_image.pixels[pixel_index + 1],
        mask_image.pixels[pixel_index + 2]
    )
    
    color_distance_sq = (pixel_color[0] - target_color[0])**2 + \
                        (pixel_color[1] - target_color[1])**2 + \
                        (pixel_color[2] - target_color[2])**2
    
    return color_distance_sq < tolerance**2

def create_surface_from_mask(mask_image, map_size, target_color, tolerance):
    """Создает геометрию поверхности на основе маски."""
    img_w, img_h = mask_image.size
    map_offset = -map_size / 2
    vertices, faces, vertex_map = [], [], {}
    
    for y in range(img_h):
        for x in range(img_w):
            pixel_index = (y * img_w + x) * 4
            pixel_color = (mask_image.pixels[pixel_index], mask_image.pixels[pixel_index+1], mask_image.pixels[pixel_index+2])
            color_distance_sq = (pixel_color[0] - target_color[0])**2 + (pixel_color[1] - target_color[1])**2 + (pixel_color[2] - target_color[2])**2
            
            if color_distance_sq < tolerance**2:
                world_x = (x / img_w) * map_size + map_offset
                world_y = (y / img_h) * map_size + map_offset
                vertex_map[(x, y)] = len(vertices)
                vertices.append(mathutils.Vector((world_x, world_y, 0.0)))

    for y in range(img_h - 1):
        for x in range(img_w - 1):
            if (x, y) in vertex_map and (x+1, y) in vertex_map and (x+1, y+1) in vertex_map and (x, y+1) in vertex_map:
                idx1 = vertex_map[(x, y)]
                idx2 = vertex_map[(x+1, y)]
                idx3 = vertex_map[(x+1, y+1)]
                idx4 = vertex_map[(x, y+1)]
                faces.append((idx1, idx2, idx3, idx4))
    
    return vertices, faces

# ====================================================================================
# --- 3. ФУНКЦИИ ГЕНЕРАЦИИ СЛОЕВ ---
# ====================================================================================

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

def generate_scatter_layer(layer_config, global_settings, global_placed_locations, master_mask):
    """Генерирует слой-рассеивания."""
    print(f"--- Начало генерации слоя-рассеивания: {layer_config['name']} ---")
    available_models = load_and_normalize_models(layer_config["models_directory"], layer_config["target_height"])
    if not available_models:
        print(f"!!! Слой '{layer_config['name']}' пропущен: модели не найдены. !!!")
        return "Слой попущен"
    
    collection_name = f"Generated_{layer_config['name']}"
    map_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(map_collection)
    
    objects_created_count = 0
    min_dist_sq = layer_config["min_distance"] ** 2
    map_offset = -global_settings["map_size"] / 2
    
    for i in range(layer_config["density"]):
        for j in range(layer_config["density"]):
            rand_x = random.uniform(map_offset, -map_offset)
            rand_y = random.uniform(map_offset, -map_offset)
            if is_point_on_color_mask(rand_x, rand_y, master_mask, global_settings["map_size"], layer_config["target_color_normalized"], layer_config["color_tolerance"]):
                new_location = mathutils.Vector((rand_x, rand_y, 0.0))
                if not check_collision(new_location, global_placed_locations, min_dist_sq):
                    source_model = random.choice(available_models)
                    new_instance = create_instance(source_model, new_location, map_collection)
                    scale_factor = random.uniform(layer_config["random_scale_min"], layer_config["random_scale_max"])
                    new_instance.scale = (scale_factor, scale_factor, scale_factor)
                    if global_settings["random_rotation"]:
                        new_instance.rotation_euler.z = random.uniform(0, 2 * math.pi)
                    global_placed_locations.append(new_instance.location)
                    objects_created_count += 1
    print(f"!!! Генерация слоя '{layer_config['name']}' завершена. Создано объектов: {objects_created_count} !!!")
    return "Все ок"


def generate_surface_layer(layer_config, global_settings, global_placed_locations, master_mask):
    """Генерирует слой-поверхности."""
    print(f"--- Начало генерации слоя-поверхности: {layer_config['name']} ---")
    collection_name = f"Generated_{layer_config['name']}"
    map_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(map_collection)
    
    vertices, faces = create_surface_from_mask(master_mask, global_settings["map_size"], layer_config["target_color_normalized"], layer_config["color_tolerance"])
    
    if not vertices:
        print(f"!!! Слой '{layer_config['name']}' пропущен: цвет не найден на маске. !!!")
        return

    mesh = bpy.data.meshes.new(f"{layer_config['name']}_Mesh")
    obj = bpy.data.objects.new(f"{layer_config['name']}_Object", mesh)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    map_collection.objects.link(obj)
    
    if layer_config.get("subdivision_level", 0) > 0:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='SUBSURF')
        obj.modifiers["Subdivision"].levels = layer_config["subdivision_level"]
        obj.modifiers["Subdivision"].render_levels = layer_config["subdivision_level"]
    
    print(f"!!! Генерация слоя-поверхности '{layer_config['name']}' завершена. !!!")


# ====================================================================================
# --- 4. ОСНОВНАЯ ЛОГИКА ГЕНЕРАЦИИ (АДАПТИРОВАНА ДЛЯ АДДОНА) ---
# ====================================================================================

def generate_all_layers_from_props(config_props):
    """
    Главная функция, которая управляет генерацией всех слоев.
    Принимает данные из PropertyGroup аддона.
    """
    # 1. Извлекаем глобальные настройки из PropertyGroup в словарь
    global_settings = {
        "map_size": config_props.map_size,
        "random_rotation": config_props.random_rotation,
        "master_mask_path": config_props.master_mask_path,
    }
    
    # 2. Загружаем мастер-маску
    master_mask = load_mask_image(global_settings["master_mask_path"])
    if not master_mask:
        print("ОШИБКА: Мастер-маска не найдена. Генерация отменена.")
        return "Маска херни"
        
    global_placed_locations = deque()
    
    # 3. Конвертируем слои из Blender PropertyGroup в список словарей
    layers_list = []
    for layer_prop in config_props.layers:
        layer_dict = {
            "type": layer_prop.type,
            "name": layer_prop.name,
            # Цвет в FloatVectorProperty уже в диапазоне 0-1, что нам и нужно
            "target_color_normalized": layer_prop.target_color[:], 
            "color_tolerance": layer_prop.color_tolerance,
        }
        if layer_prop.type == 'scatter':
            layer_dict.update({
                "models_directory": layer_prop.models_directory,
                "target_height": layer_prop.target_height,
                "density": layer_prop.density,
                "min_distance": layer_prop.min_distance,
                "random_scale_min": layer_prop.random_scale_min,
                "random_scale_max": layer_prop.random_scale_max,
            })
        elif layer_prop.type == 'surface':
            layer_dict.update({
                "subdivision_level": layer_prop.subdivision_level,
            })
        layers_list.append(layer_dict)

    # 4. Последовательно генерируем каждый слой
    for layer_config in layers_list:
        if layer_config["type"] == "scatter":
            res = generate_scatter_layer(layer_config, global_settings, global_placed_locations, master_mask)
            return res
        elif layer_config["type"] == "surface":
            generate_surface_layer(layer_config, global_settings, global_placed_locations, master_mask)
            
    print(f"!!! ВСЕ СЛОИ ГЕНЕРИРОВАНЫ. !!!")
    return "Все збс"