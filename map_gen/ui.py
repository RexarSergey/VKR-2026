# ====================================================================================
# --- ФАЙЛ: ui.py ---
# --- НАЗНАЧЕНИЕ: Создает пользовательский интерфейс для аддона в 3D-виде. ---
# ====================================================================================

import bpy
from bpy.types import Panel, UIList

# ====================================================================================
# --- СПИСОК СЛОЕВ (UIList) ---
# ====================================================================================

class SCENE_UL_layers_list(UIList):
    """Кастомный список для отображения слоев конфигурации."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Отображаем имя слоя в списке
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

# ====================================================================================
# --- ОСНОВНАЯ ПАНЕЛЬ АДДОНА ---
# ====================================================================================

class VIEW3D_PT_map_generator(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Generator"
    bl_label = "Map Generator"

    def draw(self, context):
        layout = self.layout

        # --- БЛОК ПРОВЕРКИ НА УСТОЙЧИВОСТЬ ---
        # Эта проверка нужна, чтобы аддон не "падал" с ошибкой,
        # если его свойства по какой-то причине не были зарегистрированы.
        if not hasattr(context.scene, 'generator_props'):
            layout.label(text="Error: Add-on state is corrupted.", icon='ERROR')
            layout.label(text="Please restart Blender.", icon='HELP')
            return
        # --- КОНЕЦ БЛОКА ПРОВЕРКИ ---

        # Если все в порядке, получаем доступ к данным
        scene_props = context.scene.generator_props
        prefs = context.preferences.addons[__package__].preferences

        # --- РАЗДЕЛ ГЛОБАЛЬНЫХ НАСТРОЕК ---
        box = layout.box()
        box.label(text="Global Settings", icon='WORLD')
        box.prop(scene_props, "map_save_path")
        box.prop(scene_props, "master_mask_path")
        box.prop(scene_props, "map_size")
        box.prop(scene_props, "random_rotation")

        # --- РАЗДЕЛ КОНФИГУРАЦИИ СЛОЕВ ---
        box = layout.box()
        box.label(text="Layers Configuration", icon='MODIFIER')
        
        # Создаем шаблон для отображения списка слоев
        row = box.row()
        row.template_list("SCENE_UL_layers_list", "", scene_props, "layers", scene_props, "layers_index", rows=3)
        
        # Колонка с кнопками для управления списком
        col = row.column(align=True)
        col.operator("scene.add_layer_to_config", icon='ADD', text="")
        # TODO: В будущем можно добавить кнопки удаления и перемещения слоев

        # --- РАЗДЕЛ РЕДАКТИРОВАНИЯ АКТИВНОГО СЛОЯ ---
        # Показываем свойства только если какой-то слой выбран в списке
        if scene_props.layers_index >= 0 and scene_props.layers_index < len(scene_props.layers):
            active_layer = scene_props.layers[scene_props.layers_index]
            box = layout.box()
            box.label(text=f"Edit: {active_layer.name}", icon='SETTINGS')
            box.prop(active_layer, "name")
            box.prop(active_layer, "type")
            
            # Показываем разные свойства в зависимости от типа слоя
            if active_layer.type == 'scatter':
                box.prop(active_layer, "models_directory")
                box.prop(active_layer, "target_color")
                box.prop(active_layer, "color_tolerance")
                box.prop(active_layer, "target_height")
                box.prop(active_layer, "density")
                box.prop(active_layer, "min_distance")
                col = box.column(align=True)
                col.prop(active_layer, "random_scale_min")
                col.prop(active_layer, "random_scale_max")
            elif active_layer.type == 'surface':
                box.prop(active_layer, "target_color")
                box.prop(active_layer, "color_tolerance")
                box.prop(active_layer, "subdivision_level")

        # --- КНОПКА ЗАПУСКА ГЕНЕРАЦИИ ---
        layout.separator()
        layout.operator("scene.generate_all", icon='PLAY')

# ====================================================================================
# --- РЕГИСТРАЦИЯ КЛАССОВ ---
# ====================================================================================

def register():
    bpy.utils.register_class(SCENE_UL_layers_list)
    bpy.utils.register_class(VIEW3D_PT_map_generator)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_map_generator)
    bpy.utils.unregister_class(SCENE_UL_layers_list)