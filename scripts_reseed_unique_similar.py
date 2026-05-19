# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import func

from models.models import ErrorQuestion, get_session

random.seed(20260320)


def pick(seq):
    return random.choice(seq)


def gen_function_calc(i):
    b = random.randint(-16, 16)
    c = random.randint(-20, 20)
    wrong = random.randint(-12, 12)
    return f"已知二次函数 f(x)=x^2{b:+d}x{c:+d}，学生求顶点横坐标时把 -b/2a 误算成 {wrong}，请纠正并给出最小值。"


def gen_function_domain(i):
    a = random.randint(1, 9)
    b = random.randint(-12, 12)
    wrong = random.randint(-12, 12)
    return f"函数 y=1/({a}x{b:+d}) 的定义域中，学生把禁取值写成 x={wrong}，请指出错误并写出正确结论。"


def gen_quadratic_formula(i):
    a = random.randint(1, 5)
    b = random.randint(-20, 20)
    c = random.randint(-20, 20)
    return f"解方程 {a}x^2{b:+d}x{c:+d}=0 时，学生把判别式 b^2-4ac 的符号写错，请完整给出正确求根过程。"


def gen_quadratic_factor(i):
    p = random.randint(1, 15)
    q = random.randint(1, 15)
    s = p + q
    t = p * q
    return f"方程 x^2-{s}x+{t}=0，学生因式分解写成 (x-{p-1})(x-{q+1})=0，请找出错误并给出正确分解。"


def gen_trig_identity(i):
    k = random.randint(2, 9)
    return f"化简表达式 sin^2x+cos^2x+{k}sinxcosx，学生把前两项化成 2sinxcosx，请说明错误并化简。"


def gen_trig_solution(i):
    n = random.randint(2, 6)
    return f"解方程 sinx=1/{n} 时，学生只写出主值解，遗漏通解，请补全 [0,2π] 与通解形式。"


def gen_derivative_chain(i):
    a = random.randint(2, 9)
    b = random.randint(1, 9)
    return f"求导 y=ln({a}x^2+{b})，学生写成 y'=1/({a}x^2+{b})，请指出链式法则遗漏并改正。"


def gen_derivative_monotonic(i):
    p = random.randint(1, 6)
    q = random.randint(-10, 10)
    return f"函数 f(x)=x^3{p:+d}x^2{q:+d} 的单调性判断中，学生只看导数零点不验区间符号，请重新分析。"


def gen_geometry_line_slope(i):
    x1 = random.randint(-8, 3)
    y1 = random.randint(-8, 8)
    x2 = random.randint(4, 12)
    y2 = random.randint(-8, 8)
    return f"已知点 A({x1},{y1})、B({x2},{y2})，学生把斜率公式写成 (x2-x1)/(y2-y1)，请改正并求直线方程。"


def gen_geometry_distance(i):
    a = random.randint(1, 6)
    b = random.randint(1, 6)
    c = random.randint(-12, 12)
    x0 = random.randint(-5, 5)
    y0 = random.randint(-5, 5)
    return f"点 P({x0},{y0}) 到直线 {a}x+{b}y{c:+d}=0 的距离计算中，学生漏写绝对值，请给出规范解。"


def gen_sequence_sum(i):
    a1 = random.randint(1, 8)
    d = random.randint(1, 6)
    n = random.randint(8, 25)
    return f"等差数列首项 {a1}、公差 {d}，求前 {n} 项和时学生漏写乘以 n，请写出正确公式并计算。"


def gen_sequence_recursive(i):
    a1 = random.randint(1, 8)
    p = random.randint(2, 5)
    return f"递推数列 a1={a1}, an+1={p}an+1，学生直接给通项未验证首项，请补全推导与检验步骤。"


def gen_probability_conditional(i):
    pa = random.choice([0.2, 0.3, 0.4, 0.5])
    pb = random.choice([0.3, 0.4, 0.6, 0.7])
    pab = round(min(pa, pb) * random.choice([0.4, 0.5, 0.6, 0.7]), 2)
    return f"已知 P(A)={pa}, P(B)={pb}, P(A∩B)={pab}，学生把 P(A|B) 分母写成 P(A)，请改正并计算。"


def gen_probability_model(i):
    n = random.randint(4, 10)
    k = random.randint(2, min(5, n-1))
    return f"从 {n} 个元素中抽取 {k} 个，学生把有放回抽样按无放回模型处理，请判断并重算概率。"


def gen_inequality_sign(i):
    a = random.randint(2, 9)
    b = random.randint(-20, 20)
    return f"解不等式 -{a}x{b:+d}>0 时，学生移项后未改变不等号方向，请给出正确解集。"


def gen_inequality_abs(i):
    a = random.randint(1, 8)
    b = random.randint(-10, 10)
    c = random.randint(2, 12)
    return f"解绝对值不等式 |{a}x{b:+d}|<{c} 时，学生分类讨论漏掉一段区间，请补全。"


def gen_vector_dot(i):
    x1, y1 = random.randint(-5, 5), random.randint(-5, 5)
    x2, y2 = random.randint(-5, 5), random.randint(-5, 5)
    return f"向量 a=({x1},{y1}), b=({x2},{y2}) 的数量积计算中，学生误把 cosθ 写成 sinθ，请纠正并求 a·b。"


def gen_vector_collinear(i):
    x1, y1 = random.randint(1, 6), random.randint(1, 6)
    t = random.randint(2, 5)
    x2, y2 = x1 * t, y1 * t + random.choice([-1, 0, 1])
    return f"判断向量 a=({x1},{y1}) 与 b=({x2},{y2}) 是否共线时，学生只比较一个分量，请给出完整判定。"


CONCEPTS = [
    ("函数", "计算错误", gen_function_calc),
    ("函数", "概念错误", gen_function_domain),
    ("二次方程", "公式误用", gen_quadratic_formula),
    ("二次方程", "因式分解错误", gen_quadratic_factor),
    ("三角函数", "恒等式误用", gen_trig_identity),
    ("三角函数", "通解遗漏", gen_trig_solution),
    ("导数", "链式法则错误", gen_derivative_chain),
    ("导数", "逻辑错误", gen_derivative_monotonic),
    ("解析几何", "公式误用", gen_geometry_line_slope),
    ("解析几何", "步骤缺失", gen_geometry_distance),
    ("数列", "公式误用", gen_sequence_sum),
    ("数列", "步骤缺失", gen_sequence_recursive),
    ("概率统计", "概念错误", gen_probability_conditional),
    ("概率统计", "模型错误", gen_probability_model),
    ("不等式", "规则错误", gen_inequality_sign),
    ("不等式", "分类讨论缺失", gen_inequality_abs),
    ("向量", "公式误用", gen_vector_dot),
    ("向量", "判断不完整", gen_vector_collinear),
]

SUGGESTIONS = [
    "先写题型对应公式，再代入，最后做符号复核。",
    "把中间变形分步骤写出，避免一步跳算造成错误。",
    "分类讨论先列全情况，再分别求解并验算。",
    "建议最后代入原式检查结果是否满足条件。",
    "先判断模型再计算，避免套错公式。",
]

session = get_session()

try:
    before_total = session.query(func.count(ErrorQuestion.id)).scalar() or 0

    # 1) 删除我之前批量加的数据（image_path 为空）
    deleted = session.query(ErrorQuestion).filter(ErrorQuestion.image_path.is_(None)).delete(synchronize_session=False)
    session.commit()

    # 2) 重新添加“类似但不相同”的样本
    target = 540
    question_set = set()
    generated = []
    attempt = 0
    while len(generated) < target and attempt < target * 30:
        attempt += 1
        kp, et, fn = random.choice(CONCEPTS)
        q = fn(attempt)
        if q in question_set:
            continue
        question_set.add(q)
        generated.append(
            ErrorQuestion(
                question=q,
                answer=pick(SUGGESTIONS),
                knowledge_point=kp,
                error_type=et,
                image_path=None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365), minutes=random.randint(0, 1440)),
            )
        )

    session.add_all(generated)
    session.commit()

    # 3) 校验重复题干
    dup_count = 0
    dup_groups = session.query(
        ErrorQuestion.question,
        func.count(ErrorQuestion.id).label("c")
    ).group_by(ErrorQuestion.question).having(func.count(ErrorQuestion.id) > 1).count()
    dup_count = dup_groups

    after_total = session.query(func.count(ErrorQuestion.id)).scalar() or 0

    # 同知识点同错误类型数量，用于推荐相似题
    cluster = defaultdict(int)
    rows = session.query(ErrorQuestion.knowledge_point, ErrorQuestion.error_type).all()
    for kp, et in rows:
        cluster[(kp, et)] += 1

    print({
        "before_total": before_total,
        "deleted_seed": int(deleted),
        "inserted_new": len(generated),
        "after_total": after_total,
        "duplicate_question_groups": int(dup_count),
        "cluster_examples": dict(list(cluster.items())[:6])
    })
finally:
    session.close()
