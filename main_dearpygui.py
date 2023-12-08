import dearpygui.dearpygui as dpg
from libs.dpgfiledialog import dpgDirFileDialog
from libs.lsmesh_lib import boundBox, lsdyna_model
import os
from constants import *
from libs.diag_calculator import TrueDiagrammCalculator

calculator = TrueDiagrammCalculator()

# DPG widgets callbacks
def draw_mesh(calculator: TrueDiagrammCalculator, dpg_draw_layer_tag: str):
    k = 0.9 * min(MESH_DRAW_AREA_WIDTH / calculator.model_bbox.a,
                  MESH_DRAW_AREA_HEIGH / calculator.model_bbox.b)
    x_draw = lambda x: 0.05 * MESH_DRAW_AREA_WIDTH + k * (x - calculator.model_bbox.xmin)
    y_draw = lambda y: 0.95 * MESH_DRAW_AREA_HEIGH - k * (y - calculator.model_bbox.ymin)
    dpg.delete_item(dpg_draw_layer_tag, children_only=True)
    for part in calculator.model.shells:
        for sh in calculator.model.shells[part].values():
            pnts = [
                (x_draw(calculator.model.nodes[n].x), y_draw(calculator.model.nodes[n].y)) for n in sh.nodes
            ]
            pnts.append(pnts[0])
            dpg.draw_polygon(pnts, fill=(255, 0, 0), color=(0, 0, 0), thickness=1, parent=dpg_draw_layer_tag)
    if 1 in calculator.model.nodesets:
        for n in calculator.model.nodesets[1]:
            dpg.draw_circle(
                center=(
                    x_draw(calculator.model.nodes[n].x),
                    y_draw(calculator.model.nodes[n].y),
                ),
                radius=3,
                fill=(0, 255, 0),
                color=(0, 0, 0),
                thickness=1,
                parent=dpg_draw_layer_tag
            )
    if 2 in calculator.model.nodesets:
        for n in calculator.model.nodesets[2]:
            x = x_draw(calculator.model.nodes[n].x)
            y = y_draw(calculator.model.nodes[n].y)
            dpg.draw_arrow(
                p1=(x, y - 10),
                p2=(x, y),
                color=(0, 0, 255),
                thickness=1,
                parent=dpg_draw_layer_tag
            )

def set_model_text_callback(file_name):
    if file_name:
        dpg.set_value(DPG_WIDGETS.MODEL_PATH_TEXT, file_name)
        calculator.assign_model(file_name)
        draw_mesh(calculator, DPG_WIDGETS.MESH_DRAW_LAYER)
        model_info = repr(calculator.model) + repr(calculator.model_bbox)
        dpg.set_value(DPG_WIDGETS.MODEL_INFO_TEXT, model_info)


def chose_model_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(extensions=['k', 'dyn'], height=510, callback=set_model_text_callback)
    fd.show()


def chose_expdata_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(extensions=['txt', 'csv'], height=510, callback=load_experimental_curves)
    fd.show()


def load_experimental_curves(file_name):
    if file_name:
        dpg.set_value(DPG_WIDGETS.EXP_DATA_PATH, file_name)
        try:
            calculator.read_exp_curves(file_name)
        except:
            return
        dpg.configure_item(DPG_WIDGETS.EXP_V_PLOT, x=calculator.exp_curves[0], y=calculator.exp_curves[1])
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_V_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_V_Y)
        dpg.configure_item(DPG_WIDGETS.EXP_F_PLOT, x=calculator.exp_curves[0], y=calculator.exp_curves[2])
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_F_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_F_Y)


def set_solver_path(file_name):
    if not file_name:
        return
    if not os.path.exists(file_name):
        return
    calculator.solver_path = file_name
    dpg.set_value(DPG_WIDGETS.SOLVER_PATH, file_name)


def choose_solver_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(extensions=['exe'], callback=set_solver_path, height=510)
    fd.show()

def set_workingdir(file_name):
    if not file_name:
        return
    if not os.path.exists(file_name):
        return
    calculator.working_dir = file_name
    dpg.set_value(DPG_WIDGETS.WORK_DIR, file_name)

def choose_workingdir_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(dir_mode=True, callback=set_workingdir, height=510)
    fd.show()

def solve_btn_callback(sender, app_data, user_data):
    iterations_count = 1 if user_data is None else user_data
    for j in range(iterations_count):
        if calculator.iteration == 0:
            calculator.working_dir = dpg.get_value(DPG_WIDGETS.WORK_DIR)
            calculator.n_points = dpg.get_value(DPG_WIDGETS.NUM_POINTS_INPUT)
            calculator.solver_path = dpg.get_value(DPG_WIDGETS.SOLVER_PATH)
            E = dpg.get_value(DPG_WIDGETS.MAT_E_INPUT)
            Et = dpg.get_value(DPG_WIDGETS.MAT_ET_INPUT)
            rho = dpg.get_value(DPG_WIDGETS.MAT_RHO_INPUT)
            s0 = dpg.get_value(DPG_WIDGETS.MAT_S0_INPUT)
            nu = dpg.get_value(DPG_WIDGETS.MAT_NU_INPUT)
            calculator.assign_material_props(
                rho=rho, E=E, nu=nu, s0=s0, Et=Et
            )
            calculator.save_base_model()
            calculator.save_constant_part()
            dpg.configure_item(
                DPG_WIDGETS.LINE_COMPARE_FORCE_EXP,
                x=calculator.exp_curves[0],
                y=calculator.exp_curves[2],
            )
            dpg.fit_axis_data(DPG_WIDGETS.PLOT_COMPARE_FORCE_X)
            dpg.fit_axis_data(DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)

        dpg.configure_item(DPG_WIDGETS.LINE_DIAG, x=calculator.diag_0[0], y=calculator.diag_0[1])
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_Y)
        calculator.save_variable_part()
        calculator.run_calculation()
        calculator.proc_solution_results()
        dpg.configure_item(
            DPG_WIDGETS.LINE_COMPARE_FORCE_CALC,
            x=calculator.dump_t,
            y=calculator.solution_results[1],
        )
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_COMPARE_FORCE_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
        dpg.configure_item(
            DPG_WIDGETS.LINE_MAXEP,
            x=calculator.dump_t,
            y=calculator.solution_results[0],
        )
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_MAXEP_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_MAXEP_Y)
        calculator.iteration = calculator.iteration + 1
        calculator.correct_material_diagramm()
        dpg.configure_item(DPG_WIDGETS.LINE_DIAG, x=calculator.diag_0[0], y=calculator.diag_0[1])
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_Y)
        dpg.set_value(DPG_WIDGETS.ITERATIONS_COUNT_TEXT,
                      f'Выполнено {calculator.iteration} итераций')
        data = dpg.get_value(DPG_WIDGETS.LINE_CONVERGENCE)
        dpg.configure_item(DPG_WIDGETS.LINE_CONVERGENCE,
                           x = data[0] + [calculator.iteration],
                           y = data[1] + [calculator.max_force_deflection]
                           )
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_CONVERGENCE_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_CONVERGENCE_Y)

def iteration_count_changed(sender, app_data, user_data):
    dpg.configure_item(DPG_WIDGETS.RUN_N_ITERATIONS_BTN, label=f'Выполнить {app_data} итераций')
    dpg.set_item_user_data(DPG_WIDGETS.RUN_N_ITERATIONS_BTN, app_data)

def reset_btn_callback(sender, app_data, user_data):
    dpg.set_value(DPG_WIDGETS.ITERATIONS_COUNT_TEXT,
                  'Выполнено итераций: 0')
    calculator.iteration = 0
    dpg.configure_item(DPG_WIDGETS.LINE_COMPARE_FORCE_CALC, x=[], y=[])
    dpg.configure_item(DPG_WIDGETS.LINE_MAXEP, x=[], y=[])

# end DPG widgets callbasks

# Настройка кириллического шрифта
dpg.create_context()
with dpg.font_registry():
    with dpg.font(file="./XO_Caliburn_Nu.ttf", size=18) as font1:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
dpg.bind_font(font1)
dpg.create_viewport(title="Numerical true stress strain diagramm determination",
                    width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
dpg.setup_dearpygui()

# ГПИ приложения
with dpg.window(label="Example Window", width=600, height=600, tag='main'):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label='Save')
    # Блок виджетов выбора базовой модели
    with dpg.collapsing_header(label="Базовая модель"):
        with dpg.child_window(height=490):
            with dpg.child_window(height=130):
                dpg.add_text("""Описание требований к расчетной модели""")
            with dpg.child_window(height=40):
                with dpg.group(horizontal=True):
                    dpg.add_text("Путь к файлу модели:")
                    dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.MODEL_PATH_TEXT, width=-100)
                    dpg.add_button(label="Открыть", width=100, callback=chose_model_btn_callback)
            with dpg.group(horizontal=True):
                with dpg.drawlist(width=MESH_DRAW_AREA_WIDTH, height=MESH_DRAW_AREA_HEIGH):
                    with dpg.draw_layer(tag=DPG_WIDGETS.MESH_DRAW_BACKGROUND):
                        dpg.draw_rectangle(
                            pmin=(0, 0),
                            pmax=(MESH_DRAW_AREA_WIDTH, MESH_DRAW_AREA_HEIGH),
                            fill=(255, 255, 255)
                        )
                    with dpg.draw_layer(tag=DPG_WIDGETS.MESH_DRAW_LAYER):
                        pass
                with dpg.child_window():
                    dpg.add_text("", tag=DPG_WIDGETS.MODEL_INFO_TEXT)
                    
    # Блок работы с экспериментальными кривыми
    with dpg.collapsing_header(label='Экспериментальные кривые'):
        with dpg.child_window(height=510):
            with dpg.child_window(height=130):
                dpg.add_text("""Описание требований к файлу с экспериментальными кривыми""")
            with dpg.child_window(height=40):
                with dpg.group(horizontal=True):
                    dpg.add_text("Путь к файлу данных:")
                    dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.EXP_DATA_PATH, width=-100)
                    dpg.add_button(label="Открыть", width=100, callback=chose_expdata_btn_callback)
            with dpg.child_window(height=310):
                with dpg.subplots(1, 2, width=-1, height=-1, link_all_x=True):
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_EXP_V_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='скорость', tag=DPG_WIDGETS.PLOT_EXP_V_Y)
                        dpg.add_line_series([0, 100], [0, 0], tag=DPG_WIDGETS.EXP_V_PLOT,
                                            parent=DPG_WIDGETS.PLOT_EXP_V_Y)
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_EXP_F_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='сила', tag=DPG_WIDGETS.PLOT_EXP_F_Y)
                        dpg.add_line_series([0, 100], [0, 0], tag=DPG_WIDGETS.EXP_F_PLOT,
                                            parent=DPG_WIDGETS.PLOT_EXP_F_Y)
                        
    # Блок настройки решения
    with dpg.collapsing_header(label='Настройки решения'):
        with dpg.child_window(height=370):
            with dpg.child_window(height=40):
                with dpg.group(horizontal=True):
                    dpg.add_text("Путь к решателю:")
                    dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.SOLVER_PATH, width=-100,
                                       default_value='run_dyna')
                    dpg.add_button(label="Открыть", width=100, callback=choose_solver_btn_callback)
            with dpg.child_window(height=40):
                with dpg.group(horizontal=True):
                    dpg.add_text("Рабочая директория:")
                    dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.WORK_DIR, width=-100)
                    dpg.add_button(label="Открыть", width=100, callback=choose_workingdir_btn_callback)
            with dpg.child_window(height=130):
                dpg.add_text("Начальное приближение модели")
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()
                    with dpg.table_row():
                        dpg.add_text("плотность")
                        dpg.add_input_float(default_value=7e-3, width=-1,
                                            tag=DPG_WIDGETS.MAT_RHO_INPUT)
                    with dpg.table_row():
                        dpg.add_text("модуль Юнга")
                        dpg.add_input_float(default_value=200000, width=-1,
                                            tag = DPG_WIDGETS.MAT_E_INPUT)
                        dpg.add_text("коэффициент Пуассона")
                        dpg.add_input_float(default_value=0.28, width=-1,
                                            tag=DPG_WIDGETS.MAT_NU_INPUT)
                    with dpg.table_row():
                        dpg.add_text("предел текучести")
                        dpg.add_input_float(default_value=200, width=-1,
                                            tag=DPG_WIDGETS.MAT_S0_INPUT)
                        dpg.add_text("касательный модуль")
                        dpg.add_input_float(default_value=1000, width=-1,
                                            tag=DPG_WIDGETS.MAT_ET_INPUT)
            with dpg.child_window(height=40):
                with dpg.group(horizontal=True):
                    dpg.add_text("Число точек на кривой деформирования:")
                    dpg.add_input_int(default_value=50, tag=DPG_WIDGETS.NUM_POINTS_INPUT, width=-1,
                                       min_value=10, max_value=1000)
            with dpg.child_window(height=80):
                dpg.add_text('Тип задачи:')
                dpg.add_radio_button(
                    items=['Осесимметричная', 'Плоская', 'Трехмерная'],
                    horizontal=True,
                    tag=DPG_WIDGETS.TASK_TYPE,
                )

    # Блок настройки решения
    with dpg.collapsing_header(label='Решение'):
        with dpg.child_window(height=680):
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_text(default_value='Выполено итераций: 0', tag=DPG_WIDGETS.ITERATIONS_COUNT_TEXT)
                    dpg.add_button(label="Выполнить 1 итераций", user_data=1, callback=solve_btn_callback,
                                   tag=DPG_WIDGETS.RUN_N_ITERATIONS_BTN, width=-1)
                    dpg.add_input_int(label='N', default_value=1, tag=DPG_WIDGETS.ITERATIONS_COUNT_INPUT,
                                      callback=iteration_count_changed, width=-1)
                    dpg.add_button(label="Сброс", callback=reset_btn_callback, width=-1)
            with dpg.child_window(height=610):
                with dpg.subplots(2, 2, width=-1, height=-1):
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='ep', tag=DPG_WIDGETS.PLOT_DIAG_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='s', tag=DPG_WIDGETS.PLOT_DIAG_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_DIAG,
                                            parent=DPG_WIDGETS.PLOT_DIAG_Y)
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_COMPARE_FORCE_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='сила', tag=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_COMPARE_FORCE_CALC,
                                            parent=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_COMPARE_FORCE_EXP,
                                            parent=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_MAXEP_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='maxep', tag=DPG_WIDGETS.PLOT_MAXEP_Y)
                        dpg.add_plot_axis(dpg.mvYAxis, label='dep', tag=DPG_WIDGETS.PLOT_DEP_Y, no_gridlines=True)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_MAXEP,
                                            parent=DPG_WIDGETS.PLOT_MAXEP_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_DEP,
                                            parent=DPG_WIDGETS.PLOT_DEP_Y)
                    with dpg.plot():
                        dpg.add_plot_axis(dpg.mvXAxis, label='iteration', tag=DPG_WIDGETS.PLOT_CONVERGENCE_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='max force error, %', tag=DPG_WIDGETS.PLOT_CONVERGENCE_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_CONVERGENCE,
                                            parent=DPG_WIDGETS.PLOT_CONVERGENCE_Y)


# Применение стилей и цветов
with dpg.theme() as global_theme:
    #     with dpg.theme_component(dpg.mvAll):
    #         dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (100, 100, 100))
    #         dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (120, 100, 100))
    with dpg.theme_component(dpg.mvPlot):
        dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, x=10, y=10, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2, category=dpg.mvThemeCat_Plots)
#         dpg.add_theme_color(dpg.mvPlotCol_PlotBg, (255, 255, 255), category=dpg.mvThemeCat_Plots)
#         dpg.add_theme_color(dpg.mvPlotCol_XAxisGrid, (0, 0, 0), category=dpg.mvThemeCat_Plots)
#         dpg.add_theme_color(dpg.mvPlotCol_YAxisGrid, (0, 0, 0), category=dpg.mvThemeCat_Plots)
#
dpg.bind_theme(global_theme)
#
# dpg.show_style_editor()

dpg.show_viewport()
dpg.set_primary_window('main', True)
dpg.start_dearpygui()
dpg.destroy_context()