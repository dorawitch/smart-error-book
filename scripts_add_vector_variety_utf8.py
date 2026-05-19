# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta

from models.models import get_session, ErrorQuestion

random.seed(20260320)


def t1():
    a, b, c, d = [random.randint(-8, 8) for _ in range(4)]
    return f"已知向量 a=({a},{b})、b=({c},{d})，学生在计算 a·b 时把乘法和写错，请给出正确数量积。", "向量", "计算错误"


def t2():
    a, b, c, d = [random.randint(-8, 8) for _ in range(4)]
    return f"判断向量 a=({a},{b}) 与 b=({c},{d}) 的夹角范围时，学生把锐角和钝角判断反了，请纠正。", "向量", "概念错误"


def t3():
    x, y = random.randint(1, 6), random.randint(1, 6)
    return f"已知向量 a=({x},{y})，学生求其模长时写成 |a|={x}+{y}，请改正并计算。", "向量", "公式误用"


def t4():
    a, b = random.randint(-6, 6), random.randint(-6, 6)
    t = random.randint(-4, 4)
    return f"设向量 a=({a},{b})，求 λ 使 a+λ(1,{t}) 与 (1,0) 垂直。学生漏列垂直条件，请补全。", "向量", "步骤缺失"


def t5():
    a, b, c, d = [random.randint(-9, 9) for _ in range(4)]
    return f"学生用一个分量判断向量 a=({a},{b}) 与 b=({c},{d}) 共线，请给出完整共线判定过程。", "向量", "判断不完整"


def t6():
    a, b = random.randint(-8, 8), random.randint(-8, 8)
    return f"平移向量坐标时，学生把向量 ({a},{b}) 误当成点坐标直接代入，请指出模型错误并更正。", "向量", "模型错误"


def t7():
    a, b, c, d = [random.randint(-7, 7) for _ in range(4)]
    return f"已知 |a|=√({a*a+b*b})、|b|=√({c*c+d*d})，学生在夹角公式中分母少写一个模长，请改正。", "向量", "公式误用"


def t8():
    x1, y1, x2, y2 = [random.randint(-6, 6) for _ in range(4)]
    return f"在坐标运算中，学生把向量 ({x1},{y1})-({x2},{y2}) 算成逐项相加，请重新计算并解释。", "向量", "计算错误"


def t9():
    x1, y1, x2, y2 = [random.randint(-6, 6) for _ in range(4)]
    return f"向量投影题中，学生把 a 在 b 上的投影长度写成 |a|/|b|，已知 a=({x1},{y1}), b=({x2},{y2})，请纠正。", "向量", "公式误用"


def t10():
    m = random.randint(-5, 5)
    n = random.randint(-5, 5)
    return f"已知向量 a=(m,2), b=(3,n) 满足 a⊥b，学生列方程时漏乘系数。令 m={m}, n={n} 情况下说明正确列式方法。", "向量", "步骤缺失"


templates = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]
answers = [
    "先写向量定义，再列公式，最后代入并复核符号。",
    "建议先判断题型：模长、数量积、共线、垂直或投影。",
    "把坐标运算与几何意义分开写，能减少混淆。",
]

s = get_session()
try:
    existing = set(row[0] for row in s.query(ErrorQuestion.question).all())
    now = datetime.utcnow()
    new_rows = []

    while len(new_rows) < 180:
        q, kp, et = random.choice(templates)()
        if q in existing:
            continue
        existing.add(q)
        new_rows.append(
            ErrorQuestion(
                question=q,
                answer=random.choice(answers),
                knowledge_point=kp,
                error_type=et,
                image_path=None,
                created_at=now - timedelta(days=random.randint(0, 220), minutes=random.randint(0, 1440)),
            )
        )

    s.add_all(new_rows)
    s.commit()

    print({"inserted": len(new_rows)})
finally:
    s.close()
