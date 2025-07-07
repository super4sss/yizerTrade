from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import List, Union
from decimal import Decimal
import random
import numpy as np
import gc
import warnings

# 屏蔽RuntimeWarning
warnings.simplefilter('ignore', category=RuntimeWarning)

from deap import algorithms, base, creator, tools
from pyecharts.commons.utils import JsCode
from pyecharts import options as opts
from pyecharts.charts import Bar, Page
from colorama import init, Fore
# 初始化 colorama
init(autoreset=True)
from vnpy.app.portfolio_strategy.backtesting import BacktestingEngine, Interval
from vnpy.app.portfolio_strategy.strategies.ib_exit_trend_strategy import (
    IbExitTrendStrategy
)
from vnpy.trader.utility import (
    GetFilePath,
    get_price_ticks,
)
# 涨跌颜色设置
long_color = "#C70E0E"
short_color = "#008000"
purple_color = "#9B12AF"
# js颜色，涨为long_color，跌为short_color
js_color=JsCode(
        """
    function(params) {
        if (params.value >= 0) {
            return '#C70E0E';
        } else {
            return '#008000';
        }
    }
"""
    )
# 定义格式化函数和富文本样式
formatter = JsCode("""
function(params) {
    if (params.value >= 0) {
        return '{red|' + params.value + '}';
    } else {
        return '{green|' + params.value + '}';
    }
}
""")
# 设置图形样式选项，包括颜色
# color：使用js_color函数动态设置颜色
itemstyle_opts=opts.ItemStyleOpts(
    color=js_color
)
# 设置工具箱配置项，包括字体样式和功能
title_textstyle_opts=opts.TextStyleOpts(font_family="方正韵动中黑简体", font_size=14)
# 配置工具箱选项，包括数据缩放功能
toolbox_opts = opts.ToolboxOpts(
        is_show=True,
        pos_left = None,
        pos_right = "0px",
        pos_bottom= "0px",
        feature=opts.ToolBoxFeatureOpts(
            data_zoom=opts.ToolBoxFeatureDataZoomOpts(
                xaxis_index=None,
                yaxis_index=None,
            )
        ),
    )
# 设置数据缩放选项，定义缩放范围
datazoom_opts = opts.DataZoomOpts(range_start=0, range_end=100)
# 设置提示框的位置，使其悬停在屏幕底部
# position：自定义位置函数，计算提示框的位置
# size.viewSize[1] / 2 - dom.clientHeight / 2         垂直位置调整到屏幕中部，size.viewSize[1] - dom.clientHeight - 10        // 垂直位置调整到屏幕底部（距离底部10px）
tooltip_opts=opts.TooltipOpts(
    position=JsCode(
        """
    function (point, params, dom, rect, size) {
        return [
        size.viewSize[0] / 2 - dom.clientWidth / 2, 
        size.viewSize[1] - dom.clientHeight - 10
        ];
    }
    """
    )
)
# 设置鼠标悬停高亮
emphasis_opts=opts.EmphasisOpts(
    focus = "self",
    # 悬停文字样式
    label_opts = opts.LabelOpts(
        position='top',
        formatter=formatter,
        rich={
            'red': {'color': long_color},
            'green': {'color': short_color}
        },
        font_family="方正韵动中黑简体",
        font_size=18
    ),
    # 鼠标悬停放大图形
    itemstyle_opts = opts.ItemStyleOpts(
        color = js_color,
        border_color = long_color,
        border_width=10,
    )
    )
# 隐藏数据点的标签
label_opts=opts.LabelOpts(is_show=False)

STRATEGY = IbExitTrendStrategy

########################################################################
# 1) 参数信息
param_info = [
    {"name": "buffer_size",                   "start": 30,     "end": 80,     "step": 1},
    {"name": "trade_window",                  "start": 1,      "end": 24,     "step": 1},
    {"name": "entry_window",                  "start": 10,     "end": 50,     "step": 1},
    {"name": "exit_window",                   "start": 3,      "end": 30,     "step": 1},
]
# 优化参数与优化目标变量名称
params_list = [params["name"] for params in param_info]
targets = ["sortino_value","tail_value"]

########################################################################
def build_discrete_values(info: dict) -> List[Union[int, float]]:
    """
    根据单个参数的 (start, end, step) 生成一个离散值列表。
    例如:
        start=0.1, end=0.4, step=0.1  --> [0.1, 0.2, 0.3]
        start=1,   end=5,   step=1    --> [1, 2, 3, 4]
    """
    start = Decimal(str(info["start"]))
    end   = Decimal(str(info["end"]))
    step  = Decimal(str(info["step"]))

    values = []
    val = start
    # 小心浮点边界，循环到 "end + step/2" 避免浮点不精确问题
    while val <= end + step/Decimal("0.9999999"):
        # 根据 start/step 类型，判断最终保留 int 还是 float
        if (float(val) % 1 == 0) and (float(step) % 1 == 0):
            values.append(int(val))
        else:
            values.append(float(val))
        val += step

    return values

# 预先生成所有参数的离散值集合，减少重复计算
all_discrete_values = []
for item in param_info:
    discrete_vals = build_discrete_values(item)
    all_discrete_values.append(discrete_vals)


########################################################################
def parameter_generate() -> List[Union[int, float]]:
    """
    从每个参数可选的离散值集合中，随机选出一个值，构成最终的 19 维参数向量。
    """
    individual = []
    for discrete_vals in all_discrete_values:
        rnd = random.choice(discrete_vals)
        individual.append(rnd)
    return individual


########################################################################
def object_func(strategy_avg: List[Union[int, float]]):
    """
    优化目标函数：根据 19 个策略参数，运行回测后返回 (sortino_value, tail_value)。
    """
    # 创建回测引擎对象
    engine = BacktestingEngine()
    engine.clear_data()

    # 设置回测参数
    vt_symbols = [
        "NQINDEX-USD-FUT_GLOBEX/IB",
        "ESINDEX-USD-FUT_GLOBEX/IB"
    ]
    price_ticks = {
        "NQINDEX-USD-FUT_GLOBEX/IB":0.25,
        "ESINDEX-USD-FUT_GLOBEX/IB":0.25,
    }

    rates     = {}
    slippages = {}
    sizes     = {}
    for vt_symbol in vt_symbols:
        rates[vt_symbol]     = 4 / 10000
        slippages[vt_symbol] = price_ticks[vt_symbol] * 2
        sizes[vt_symbol]     = 2

    engine.set_parameters(
        start=datetime(2012, 1, 1),
        end=datetime(2022, 1, 1),
        vt_symbols=vt_symbols,
        rates=rates,
        price_ticks=price_ticks,
        slippages=slippages,
        sizes=sizes,
        capital=float(len(vt_symbols) * 5e5),
        interval=Interval.MINUTE,
    )

    # 将 19 个参数组合进 setting
    setting = dict(zip(params_list,strategy_avg))

    engine.add_strategy(STRATEGY, setting)
    engine.load_data(concurrent=False)
    engine.run_backtesting()

    daily_df = engine.calculate_result()
    statistics = engine.calculate_statistics(daily_df, output_statistics=False)

    # 取出 sortino_value 和 tail_value
    try:
        sortino_value = round(statistics[targets[0]], 3)
        tail_value    = round(statistics[targets[1]], 3)
    except:
        sortino_value = 0
        tail_value    = 0

    # 释放资源
    del daily_df
    del engine
    gc.collect()

    return sortino_value, tail_value


########################################################################
# 2) 自定义变异函数：根据参数是 int 还是 float，重新在对应集合中随机选一个值
#    并确保变异概率 mutpb
def mutate_param(individual, mutpb=0.3):
    """
    对个体进行变异，让变异后的取值可达到原 all_discrete_values[i]["end"] 最大值的 2 倍。
    即从 [param_info[i]["start"], param_info[i]["end"]] 扩展到 2 * param_info[i]["end"]。
    """
    for i in range(len(individual)):
        # 以 mutpb 的概率决定是否对第 i 个基因(参数)进行变异
        if random.random() < mutpb:
            # 取出该参数的原始离散值集合、最大值、以及对应 (start, end, step)
            discrete_vals = all_discrete_values[i]  # 原离散值
            info          = param_info[i]

            # 计算扩展后新的上界(2 倍)
            extended_max = 2 * info["end"]

            # 如果 param_info[i]["end"] 本身就是 float，需要保持步长也为 float
            step_decimal  = Decimal(str(info["step"]))
            start_decimal = Decimal(str(info["end"])) + step_decimal
            end_decimal   = Decimal(str(extended_max))

            # 先将原有离散值拷贝到扩展集合中
            extended_vals = set(discrete_vals)

            # 在 [end+step, 2*end] 区间内继续按同样步长生成值
            val = start_decimal
            while val <= end_decimal + step_decimal / Decimal("1000000"):
                # 根据 step 和当前 val 判断用 int 还是 float
                if (float(val) % 1 == 0) and (float(step_decimal) % 1 == 0):
                    extended_vals.add(int(val))
                else:
                    extended_vals.add(float(val))
                val += step_decimal

            # 排序之后再随机挑选
            extended_vals_list = sorted(list(extended_vals))
            individual[i] = random.choice(extended_vals_list)

    return (individual,)


########################################################################
# 3) 定义多目标：需要最大化 Sortino 和 Tail Ratio
creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0))
creator.create("Individual", list, fitness=creator.FitnessMulti)


########################################################################
# === 新增：自定义的进化过程（包含精英策略及收敛检测）函数 ===
def eaMuPlusLambdaWithConvergence(
    population, toolbox, mu, lambda_, cxpb, mutpb, ngen,
    stats=None, halloffame=None, verbose=True,
    converge_threshold=0.01,   # 收敛阈值
    converge_rounds=3          # 连续多少代满足阈值则判定收敛
):
    """
    自定义进化过程，结合了：
        1) 精英策略 (selNSGA2 自身为精英方法)
        2) 收敛性检测
    """
    logbook = tools.Logbook()
    logbook.header = ['gen', 'evals'] + (stats.fields if stats else [])

    # 初始种群评估
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # 收敛检测辅助计数
    converge_count = 0

    # 迭代进化
    for gen in range(1, ngen + 1):
        # 产生子代(包含交叉与变异)
        offspring = algorithms.varOr(population, toolbox, lambda_, cxpb, mutpb)

        # 评估子代
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # 与上一代合并，然后选出下一代
        population = toolbox.select(population + offspring, mu)

        if halloffame is not None:
            halloffame.update(population)

        # 记录统计量
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

        # === 收敛性检测 ===
        # 这里简单以两个目标 (Sortino、Tail) 的 (max-min) 之和小于一定阈值来做示例
        fitness_vals = [ind.fitness.values for ind in population]
        max_vals = np.max(fitness_vals, axis=0)
        min_vals = np.min(fitness_vals, axis=0)
        diff_sum = np.sum(max_vals - min_vals)  # sortino 与 tail 的差异和

        if diff_sum < converge_threshold:
            converge_count += 1
        else:
            converge_count = 0

        # 如果连续多代满足收敛，则提前退出
        if converge_count >= converge_rounds:
            if verbose:
                print(f"===> 收敛检测：已连续 {converge_rounds} 代满足阈值，提前退出进化 at Gen {gen}.")
            break

    return population, logbook


########################################################################
def optimize():
    """
    执行遗传算法优化参数
    """
    toolbox = base.Toolbox()

    # 注册个体/种群生成
    toolbox.register("individual", tools.initIterate, creator.Individual, parameter_generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # 交叉操作使用 cxUniform（可根据需要替换为其他，例如 cxTwoPoint 等）
    toolbox.register("mate", tools.cxUniform, indpb=0.6)

    # 变异操作用我们自定义的 mutate_param
    toolbox.register("mutate", mutate_param, mutpb=0.3)

    # NSGA2 用于多目标选择（自带精英策略）
    toolbox.register("evaluate", object_func)
    toolbox.register("select", tools.selNSGA2)

    # 多进程加速
    pool = ProcessPoolExecutor(max_workers=20)

    # 2. 注册带小块调度的 map
    def map_with_chunks(fn, iterable):
        # executor.map 本身已支持 chunksize
        return pool.map(fn, iterable, chunksize=1)

    toolbox.register("map", map_with_chunks)

    # 遗传算法参数
    mu = 40            # 每一代选出的个体数
    lamb = 100         # 每一代产生的子代数
    pop_size = 50      # 初始种群大小
    cxpb, mutpb = 0.6, 0.3
    n_gen = 30         # 进化轮数

    # 初始化种群
    pop = toolbox.population(n=pop_size)
    hof = tools.ParetoFront()

    # 统计信息
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    np.set_printoptions(suppress=True)
    stats.register("mean", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    # 使用自定义带收敛检测的算法
    pop, logbook = eaMuPlusLambdaWithConvergence(
        population=pop,
        toolbox=toolbox,
        mu=mu,
        lambda_=lamb,
        cxpb=cxpb,
        mutpb=mutpb,
        ngen=n_gen,
        stats=stats,
        halloffame=hof,
        verbose=True,
        converge_threshold=0.01,
        converge_rounds=3
    )

    return pop, hof

def split_params_dict(params_dict: str, max_length=50):
    """
    将参数字典字符串分成多行，确保每行长度不超过max_length个字符。
    """
    # 将字符串按逗号分割，这里为了更便于识别，以逗号为拆分标志
    words = params_dict.split(',')
    lines = []
    current_line = []

    # 遍历每个分割后的内容，确保每行的总长度不超过max_length
    for word in words:
        # 如果当前行加上这个内容后，超出最大长度，则换行
        if len(''.join(current_line) + word) > max_length:
            lines.append(' '.join(current_line))  # 将当前行加入结果
            current_line = [word]  # 新起一行
        else:
            current_line.append(word)

    # 将最后一行也加入
    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)


########################################################################
if __name__ == "__main__":
    strategy_name = STRATEGY.__name__.replace("Strategy", "")

    # 执行优化
    pop, hof = optimize()

    # ============================================================
    # 过滤重复的最优个体，避免输出相同参数
    # ============================================================
    # 这里示例：从最后一代种群中选取前 50 名最优的个体（基于多目标适应度）
    best_individuals = tools.selBest(pop, 50)

    # 准备一个列表保存不重复的个体
    unique_individuals = []
    # 用 set 来检测重复的参数组合
    seen_params_set = set()

    for ind in best_individuals:
        # 将个体所对应的参数字典转成字符串，用于去重
        params_str = str(dict(zip(params_list, ind)))
        if params_str not in seen_params_set:
            seen_params_set.add(params_str)
            unique_individuals.append(ind)

    # 下面开始正式输出并做可视化
    optimize_param = []
    sortino_value_list = []
    tail_value_list = []

    # 打印不重复的最优个体
    for index, individual in enumerate(unique_individuals, start=1):
        param_dict = dict(zip(params_list, individual))
        fitness_values = dict(zip(targets, individual.fitness.values))

        # 美化打印
        params_str = str(param_dict)
        print(
            Fore.CYAN
            + f"最优参数{index}: {params_str}, "
            + f"目标值(索提诺, 尾部比率) = {fitness_values}"
        )

        # 格式化字典字符串（分行）
        #formatted_params_str = split_params_dict(params_str)

        optimize_param.append(params_str)
        sortino_value_list.append(individual.fitness.values[0])
        tail_value_list.append(individual.fitness.values[1])

    # 画图并保存为 HTML
    get_file_path = GetFilePath()
    opt_path = str(
        get_file_path.opt_path(f"ga_{strategy_name}")
    ).replace("cta_strategy", "portfolio_strategy")

    bar_1 = Bar()
    bar_1.add_xaxis(optimize_param)
    bar_1.add_yaxis(
        f"{strategy_name}\n\n索提诺比率优化分布图",
        sortino_value_list,
        color=js_color,
        itemstyle_opts=itemstyle_opts,
        emphasis_opts=emphasis_opts
    )
    bar_1.set_global_opts(
        opts.TitleOpts(title="sortino_value", title_textstyle_opts=title_textstyle_opts),
        toolbox_opts=toolbox_opts,
        datazoom_opts=datazoom_opts,
        tooltip_opts=tooltip_opts,
    )
    bar_1.set_series_opts(label_opts=label_opts)

    bar_2 = Bar()
    bar_2.add_xaxis(optimize_param)
    bar_2.add_yaxis(
        "尾部比率优化分布图",
        tail_value_list,
        color=js_color,
        itemstyle_opts=itemstyle_opts,
        emphasis_opts=emphasis_opts
    )
    bar_2.set_global_opts(
        opts.TitleOpts(title="tail_value", title_textstyle_opts=title_textstyle_opts),
        toolbox_opts=toolbox_opts,
        datazoom_opts=datazoom_opts,
        tooltip_opts=tooltip_opts,
    )
    bar_2.set_series_opts(label_opts=label_opts)

    page = Page(layout=Page.SimplePageLayout)
    for bar in [bar_1, bar_2]:
        bar.width = "100%"
        page.add(bar)

    page.render(opt_path)