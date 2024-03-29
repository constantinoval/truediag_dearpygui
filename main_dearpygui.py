import dearpygui.dearpygui as dpg
from libs.dpgfiledialog import dpgDirFileDialog
from libs.lsmesh_lib import boundBox, lsdyna_model
import os
from constants import *
from libs.diag_calculator import TrueDiagrammCalculator
from libs.mesh_drawer import MeshDrawer
import threading
from libs.base_model_lib import BaseLSmodel, ShellType
from get_db_data_dialog import GetDBdataDialog

calculator = TrueDiagrammCalculator()
running = True


# DPG widgets callbacks
def set_model_text_callback(file_name):
    if file_name:
        dpg.set_value(DPG_WIDGETS.MODEL_PATH_TEXT, file_name)
        calculator.assign_model(file_name)
        md.model = calculator.model
        model_info = repr(calculator.model) + repr(calculator.model_bbox)
        dpg.set_value(DPG_WIDGETS.MODEL_INFO_TEXT, model_info)


def chose_model_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(extensions=['k', 'dyn'], height=600, callback=set_model_text_callback)
    fd.show()


def chose_expdata_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(extensions=['txt', 'csv'], height=600, callback=load_experimental_curves)
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
    fd = dpgDirFileDialog(extensions=['exe'], callback=set_solver_path, height=590)
    fd.show()


def set_workingdir(file_name):
    if not file_name:
        return
    if not os.path.exists(file_name):
        return
    calculator.working_dir = file_name
    dpg.set_value(DPG_WIDGETS.WORK_DIR, file_name)


def choose_workingdir_btn_callback(sender, app_data, user_data):
    fd = dpgDirFileDialog(dir_mode=True, callback=set_workingdir, height=590)
    fd.show()


def solve_btn_callback(sender, app_data, user_data):
    iterations_count = 1 if user_data is None else user_data
    dpg.set_value(DPG_WIDGETS.SOLUTION_PROGRESS, 0)
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
        if calculator.iteration != 0:
            calculator.correct_material_diagramm()
            dpg.configure_item(DPG_WIDGETS.LINE_DIAG, x=calculator.diag_0[0], y=calculator.diag_0[1])
            dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_X)
            dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_Y)

        dpg.configure_item(DPG_WIDGETS.LINE_DIAG, x=calculator.strain, y=calculator.stress)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DIAG_Y)
        calculator.save_variable_part()
        calculator.run_calculation(ncpus=dpg.get_value(DPG_WIDGETS.NUM_CPUS_INPUT))
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
        dpg.configure_item(
            DPG_WIDGETS.LINE_DEP,
            x=calculator.dump_t[:-1],
            y=[
                (calculator.solution_results[0][i] - calculator.solution_results[0][i - 1]) /
                (calculator.dump_t[i] - calculator.dump_t[i - 1])
                for i in range(1, calculator.n_points)
            ]
        )
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_MAXEP_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_MAXEP_Y)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_DEP_Y)
        calculator.iteration = calculator.iteration + 1
        dpg.set_value(DPG_WIDGETS.ITERATIONS_COUNT_TEXT,
                      f'Выполнено {calculator.iteration} итераций')
        data = dpg.get_value(DPG_WIDGETS.LINE_CONVERGENCE)
        dpg.configure_item(DPG_WIDGETS.LINE_CONVERGENCE,
                           x=data[0] + [calculator.iteration],
                           y=data[1] + [calculator.max_force_error]
                           )
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_CONVERGENCE_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_CONVERGENCE_Y)
        dpg.set_value(DPG_WIDGETS.SOLUTION_PROGRESS, (j + 1) / iterations_count)


def run_solution_until_converged():
    crit = dpg.get_value(DPG_WIDGETS.CONVERGENCE_CRIT_INPUT)
    while running:
        error = calculator.max_force_error
        if error and error <= crit:
            return
        solve_btn_callback(None, None, 1)


def run_until_converged(sender, app_data, user_data):
    global running
    running = True
    t = threading.Thread(target=run_solution_until_converged, args=(), daemon=True)
    t.start()


def iteration_count_changed(sender, app_data, user_data):
    dpg.configure_item(DPG_WIDGETS.RUN_N_ITERATIONS_BTN, label=f'Выполнить {app_data} итераций')
    dpg.set_item_user_data(DPG_WIDGETS.RUN_N_ITERATIONS_BTN, app_data)


def reset_btn_callback(sender, app_data, user_data):
    dpg.set_value(DPG_WIDGETS.ITERATIONS_COUNT_TEXT,
                  'Выполнено итераций: 0')
    calculator.iteration = 0
    dpg.configure_item(DPG_WIDGETS.LINE_COMPARE_FORCE_CALC, x=[], y=[])
    dpg.configure_item(DPG_WIDGETS.LINE_MAXEP, x=[], y=[])
    dpg.configure_item(DPG_WIDGETS.LINE_CONVERGENCE, x=[], y=[])
    dpg.configure_item(DPG_WIDGETS.LINE_DEP, x=[], y=[])


def stop_button_callback(sender, app_data, user_data):
    global running
    running = False


# end DPG widgets callbasks


def create_model_callback(sender, app_data, user_data):
    w = dpg.get_value(DPG_WIDGETS.SAMPLE_WIDTH)
    h = dpg.get_value(DPG_WIDGETS.SAMPLE_HEIGHT)
    nx = dpg.get_value(DPG_WIDGETS.SAMPLE_NX)
    ny = dpg.get_value(DPG_WIDGETS.SAMPLE_NY)
    match dpg.get_value(DPG_WIDGETS.TASK_TYPE):
        case 'Плоское напряжение':
            task_type = ShellType.plane_stress
        case 'Плоская деформация':
            task_type = ShellType.plane_strain
        case 'Осесимм. (по площади)':
            task_type = ShellType.axisymmetric_area
        case _:
            task_type = ShellType.axisymmetric_volume
    model = BaseLSmodel(etype=task_type)
    model.create_mesh(width=w, height=h, nx=nx, ny=ny)
    calculator.model = model
    calculator.model_path = ''
    dr.model = model

def set_get_data_mode(sender, app_data, user_data):
    dpg.configure_item('main', show=False)
    dpg.set_primary_window('main', False)
    dpg.configure_item(get_data_dialog, show=True)
    dpg.set_primary_window(get_data_dialog, True)

def get_data_result(result: dict):
    dpg.configure_item('main', show=True)
    dpg.set_primary_window('main', True)
    dpg.configure_item(get_data_dialog, show=False)
    dpg.set_primary_window(get_data_dialog, False)
    if result:
        dpg.set_value(DPG_WIDGETS.SAMPLE_WIDTH, result['r'])
        dpg.set_value(DPG_WIDGETS.SAMPLE_HEIGHT, result['l'])
        dpg.set_value(DPG_WIDGETS.SAMPLE_NX, 10)
        dpg.set_value(DPG_WIDGETS.SAMPLE_NY, int(result['l']/(result['r']/10)))
        create_model_callback(None, None, None)
        dpg.configure_item(DPG_WIDGETS.EXP_V_PLOT, x=result['t'], y=result['v'])
        dpg.configure_item(DPG_WIDGETS.EXP_F_PLOT, x=result['t'], y=result['f'])
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_V_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_V_Y)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_F_X)
        dpg.fit_axis_data(DPG_WIDGETS.PLOT_EXP_F_Y)
        calculator.exp_curves = [result['t'], result['v'], result['f']]


dpg.create_context()
dpg.create_viewport(title="Numerical true stress strain diagramm determination",
                    width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
dpg.setup_dearpygui()

# ГПИ приложения
with dpg.window(label="Example Window", width=600, height=600, tag='main'):
    # Основное меню
    with dpg.menu_bar():
        with dpg.menu(label="Файл"):
            dpg.add_menu_item(label='Сохранить проект')
            dpg.add_menu_item(label='Загрузить проект')
            dpg.add_separator()
            dpg.add_menu_item(label='Выход', callback=dpg.stop_dearpygui)
        with dpg.menu(label='Данные'):
            dpg.add_menu_item(
                label='Получить из БД',
                callback=set_get_data_mode,
            )
    with dpg.tab_bar():
        # Блок виджетов выбора базовой модели
        with dpg.tab(label="Базовая модель"):
            with dpg.tab_bar():
                with dpg.tab(label='Создать'):
                    with dpg.child_window(height=-1):
                        with dpg.group(horizontal=True):
                            with dpg.group():
                                with dpg.table(row_background=True, width=300):
                                    dpg.add_table_column(label='Параметр')
                                    dpg.add_table_column(label='Значение')
                                    with dpg.table_row():
                                        dpg.add_text('ширина')
                                        dpg.add_input_float(default_value=2.5, step=0, width=-1,
                                                            tag=DPG_WIDGETS.SAMPLE_WIDTH)
                                    with dpg.table_row():
                                        dpg.add_text('высота')
                                        dpg.add_input_float(default_value=5, step=0, width=-1,
                                                            tag=DPG_WIDGETS.SAMPLE_HEIGHT)
                                    with dpg.table_row():
                                        dpg.add_text('элементов по X')
                                        dpg.add_input_int(
                                            default_value=10, step=0,
                                            min_value=1, min_clamped=True,
                                            width=-1,
                                            tag=DPG_WIDGETS.SAMPLE_NX,
                                        )
                                    with dpg.table_row():
                                        dpg.add_text('элементов по Y')
                                        dpg.add_input_int(
                                            default_value=10, step=0,
                                            min_value=1, min_clamped=True,
                                            width=-1,
                                            tag=DPG_WIDGETS.SAMPLE_NY,
                                        )
                                dpg.add_button(label='Создать', callback=create_model_callback)
                                with dpg.child_window(width=300):
                                    dpg.add_text('Тип задачи:')
                                    dpg.add_radio_button(
                                        items=[
                                            'Плоское напряжение',
                                            'Плоская деформация',
                                            'Осесимм. (по площади)',
                                            'Осесимм. (по объему)',
                                        ],
                                        horizontal=False,
                                        tag=DPG_WIDGETS.TASK_TYPE,
                                        default_value='Осесимм. (по объему)',
                                    )
                            cw = dpg.add_child_window()
                            dr = MeshDrawer(width=MESH_DRAW_AREA_WIDTH, height=MESH_DRAW_AREA_HEIGH,
                                            bg_color=(255, 255, 255))
                            dr.submit(cw)
                with dpg.tab(label='Открыть'):
                    with dpg.child_window(height=-1):
                        with dpg.child_window(height=130):
                            dpg.add_text("""Описание требований к расчетной модели""")
                        with dpg.child_window(height=60):
                            with dpg.group(horizontal=True):
                                dpg.add_text("Путь к файлу модели:")
                                dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.MODEL_PATH_TEXT, width=-110)
                                dpg.add_button(label="Открыть", width=100, callback=chose_model_btn_callback)
                        with dpg.group(horizontal=True):
                            with dpg.child_window(height=-1, width=MESH_DRAW_AREA_WIDTH + 2) as cw:
                                md = MeshDrawer(MESH_DRAW_AREA_WIDTH, MESH_DRAW_AREA_HEIGH)
                                md.submit(cw)
                            with dpg.child_window(height=-1):
                                dpg.add_text("", tag=DPG_WIDGETS.MODEL_INFO_TEXT)

        # Блок работы с экспериментальными кривыми
        with dpg.tab(label='Экспериментальные кривые'):
            with dpg.child_window(height=-1):
                with dpg.child_window(height=130):
                    dpg.add_text("""Описание требований к файлу с экспериментальными кривыми""")
                with dpg.child_window(height=60):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Путь к файлу данных:")
                        dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.EXP_DATA_PATH, width=-110)
                        dpg.add_button(label="Открыть", width=100, callback=chose_expdata_btn_callback)
                # with dpg.child_window(height=310):
                with dpg.subplots(1, 2, width=-1, height=-1, link_all_x=True):
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_EXP_V_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='скорость', tag=DPG_WIDGETS.PLOT_EXP_V_Y)
                        dpg.add_line_series([0, 100], [0, 0], tag=DPG_WIDGETS.EXP_V_PLOT,
                                            parent=DPG_WIDGETS.PLOT_EXP_V_Y)
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_EXP_F_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='сила', tag=DPG_WIDGETS.PLOT_EXP_F_Y)
                        dpg.add_line_series([0, 100], [0, 0], tag=DPG_WIDGETS.EXP_F_PLOT,
                                            parent=DPG_WIDGETS.PLOT_EXP_F_Y)

        # Блок настройки решения
        with dpg.tab(label='Настройки решения'):
            with dpg.child_window(height=-1):
                with dpg.child_window(height=100):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Путь к решателю:")
                        dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.SOLVER_PATH, width=-110,
                                           default_value='run_dyna')
                        dpg.add_button(label="Открыть", width=100, callback=choose_solver_btn_callback)
                    with dpg.group(horizontal=True):
                        dpg.add_text("Число параллельных потоков: ")
                        dpg.add_input_int(tag=DPG_WIDGETS.NUM_CPUS_INPUT, default_value=4, width=150, min_value=1,
                                          min_clamped=True)
                with dpg.child_window(height=60):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Рабочая директория:")
                        dpg.add_input_text(readonly=True, tag=DPG_WIDGETS.WORK_DIR, width=-110)
                        dpg.add_button(label="Открыть", width=100, callback=choose_workingdir_btn_callback)
                with dpg.child_window(height=190):
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
                                                tag=DPG_WIDGETS.MAT_E_INPUT)
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
                with dpg.child_window(height=60):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Число точек на кривой деформирования:")
                        dpg.add_input_int(default_value=50, tag=DPG_WIDGETS.NUM_POINTS_INPUT, width=-1,
                                          min_value=10, max_value=1000)

        # Блок настройки решения
        with dpg.tab(label='Решение'):
            with dpg.child_window(height=-1):
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
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Считать до совпадения с точностью', callback=run_until_converged)
                    dpg.add_input_int(label='%', default_value=5, width=150, tag=DPG_WIDGETS.CONVERGENCE_CRIT_INPUT)
                    dpg.add_button(label='Стоп', user_data=False, tag=DPG_WIDGETS.STOP_BUTTON,
                                   callback=stop_button_callback)
                    dpg.add_spacer(width=50)
                    dpg.add_button(label='Сохранить диаграмму')
                dpg.add_progress_bar(tag=DPG_WIDGETS.SOLUTION_PROGRESS, width=-1, height=20)
                # with dpg.child_window(height=610):
                with dpg.subplots(2, 2, width=-1, height=-1):
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='ep', tag=DPG_WIDGETS.PLOT_DIAG_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='s', tag=DPG_WIDGETS.PLOT_DIAG_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_DIAG,
                                            parent=DPG_WIDGETS.PLOT_DIAG_Y)
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_COMPARE_FORCE_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='сила', tag=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                        dpg.add_line_series(label='calc', x=[], y=[], tag=DPG_WIDGETS.LINE_COMPARE_FORCE_CALC,
                                            parent=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                        dpg.add_line_series(label='exp', x=[], y=[], tag=DPG_WIDGETS.LINE_COMPARE_FORCE_EXP,
                                            parent=DPG_WIDGETS.PLOT_COMPARE_FORCE_Y)
                        dpg.add_plot_legend()
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='время', tag=DPG_WIDGETS.PLOT_MAXEP_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='maxep', tag=DPG_WIDGETS.PLOT_MAXEP_Y)
                        dpg.add_plot_axis(dpg.mvYAxis, label='dep', tag=DPG_WIDGETS.PLOT_DEP_Y, no_gridlines=True)
                        dpg.add_line_series(x=[], y=[], label='strain', tag=DPG_WIDGETS.LINE_MAXEP,
                                            parent=DPG_WIDGETS.PLOT_MAXEP_Y)
                        dpg.add_line_series(x=[], y=[], label='strain rate', tag=DPG_WIDGETS.LINE_DEP,
                                            parent=DPG_WIDGETS.PLOT_DEP_Y)
                        dpg.add_plot_legend()
                    with dpg.plot(anti_aliased=True):
                        dpg.add_plot_axis(dpg.mvXAxis, label='iteration', tag=DPG_WIDGETS.PLOT_CONVERGENCE_X)
                        dpg.add_plot_axis(dpg.mvYAxis, label='max force error, %', tag=DPG_WIDGETS.PLOT_CONVERGENCE_Y)
                        dpg.add_line_series([], [], tag=DPG_WIDGETS.LINE_CONVERGENCE,
                                            parent=DPG_WIDGETS.PLOT_CONVERGENCE_Y)

with dpg.window(show=False) as get_data_dialog:
    gd = GetDBdataDialog(callback=get_data_result, width=-1, height=-1)
    gd.submit(parent=get_data_dialog)

# Настройка кириллического шрифта
with dpg.font_registry():
    with dpg.font(file="./XO_Caliburn_Nu.ttf", size=18) as font1:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
dpg.bind_font(font1)

# Применение стилей и цветов
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvMenuItem):
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, y=10)
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, x=20, y=10)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, x=5)
    #     with dpg.theme_component(dpg.mvAll):
    #         dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (100, 100, 100))
    #         dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (120, 100, 100))
    with dpg.theme_component(dpg.mvPlot):
        dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, x=10, y=10, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2, category=dpg.mvThemeCat_Plots)
        # dpg.add_theme_style(dpg.mv)

#         dpg.add_theme_color(dpg.mvPlotCol_PlotBg, (255, 255, 255), category=dpg.mvThemeCat_Plots)
#         dpg.add_theme_color(dpg.mvPlotCol_XAxisGrid, (0, 0, 0), category=dpg.mvThemeCat_Plots)
#         dpg.add_theme_color(dpg.mvPlotCol_YAxisGrid, (0, 0, 0), category=dpg.mvThemeCat_Plots)

with dpg.theme() as line_with_markers:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Diamond, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 7, category=dpg.mvThemeCat_Plots)
#
dpg.bind_theme(global_theme)
dpg.bind_item_theme(DPG_WIDGETS.LINE_CONVERGENCE, line_with_markers)
#
# dpg.show_style_editor()
# dpg.show_debug()
dpg.show_viewport()
dpg.set_primary_window('main', True)
dpg.start_dearpygui()
dpg.destroy_context()
