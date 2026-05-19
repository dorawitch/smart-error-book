# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta

from models.models import ErrorQuestion, get_session

prefixes = ["【高一】", "【高二】", "【高三】", "【月考】", "【期中】", "【模拟卷】"]

knowledge_templates = {
    "函数": [
        ("已知函数 f(x)=x^2-4x+3，求最小值。学生把顶点坐标算错。", "计算错误"),
        ("函数 y=1/(x-2) 的定义域，学生误写为 x!=1。", "概念错误"),
        ("判断函数奇偶性时，f(-x) 展开符号写错。", "符号错误"),
        ("求分段函数在 x=0 处极限时只算了右极限。", "审题错误"),
    ],
    "二次方程": [
        ("解方程 x^2-5x+6=0，学生因式分解错误。", "因式分解错误"),
        ("使用求根公式时把 b^2-4ac 算成 b^2+4ac。", "公式误用"),
        ("含参数方程根的讨论遗漏判别式等于0情形。", "分类讨论缺失"),
    ],
    "三角函数": [
        ("化简 sin^2x+cos^2x 时结果写错。", "恒等式误用"),
        ("求 tan(2x) 时公式分母符号写错。", "公式误用"),
        ("解 sinx=1/2 只写了一个解，遗漏通解。", "通解遗漏"),
    ],
    "解析几何": [
        ("求直线斜率时把分子分母位置写反。", "公式误用"),
        ("圆与直线位置关系判别式符号判断错误。", "符号错误"),
        ("椭圆离心率计算中参数关系写错。", "概念错误"),
    ],
    "导数": [
        ("求导 ln(x^2+1) 时遗漏链式法则。", "链式法则错误"),
        ("切线方程计算中常数项符号写反。", "符号错误"),
        ("判断单调区间只看导数零点，未看区间符号。", "逻辑错误"),
    ],
    "概率统计": [
        ("条件概率 P(A|B) 的分母写错。", "概念错误"),
        ("排列组合题把有放回当成无放回。", "模型错误"),
        ("方差公式计算漏掉平方项。", "公式误用"),
    ],
    "数列": [
        ("等差数列求和公式中漏写 n。", "公式误用"),
        ("递推求通项后未验证首项。", "步骤缺失"),
        ("等比数列公比为负时误判单调性。", "结论误用"),
    ],
    "不等式": [
        ("两边同乘负数后忘记改变不等号方向。", "规则错误"),
        ("绝对值不等式分类讨论漏区间。", "分类讨论缺失"),
        ("均值不等式应用时忽略正数条件。", "条件遗漏"),
    ],
    "立体几何": [
        ("异面直线所成角与平面角混淆。", "概念错误"),
        ("点到平面距离误用线段长度。", "模型错误"),
        ("体积计算中底面积与高单位不统一。", "单位错误"),
    ],
    "向量": [
        ("向量数量积公式中把 cos 写成 sin。", "公式误用"),
        ("向量共线判定只比较一个分量。", "判断不完整"),
        ("坐标运算中减法写成加法。", "计算错误"),
    ],
}

answers = [
    "先写已知与所求，再列关键公式，最后代入并检查符号。",
    "建议按题型先选模型，再检查条件是否齐全。",
    "把中间式分步写清，可有效避免符号和运算错误。",
    "分类讨论题先列全情况，再逐一求解和验算。",
    "最后用代入或图像法进行结果复核。",
]

s = get_session()
try:
    # Remove previously generated broken rows (no image path)
    broken_rows = s.query(ErrorQuestion).filter(ErrorQuestion.image_path.is_(None)).all()
    removed = len(broken_rows)
    for r in broken_rows:
        s.delete(r)
    s.commit()

    random.seed(20260320)
    now = datetime.utcnow()
    topic_names = list(knowledge_templates.keys())

    rows = []
    target_count = 320
    for i in range(target_count):
        kp = random.choice(topic_names)
        q_tpl, err_type = random.choice(knowledge_templates[kp])
        prefix = random.choice(prefixes)
        idx = random.randint(100, 9999)
        question = f"{prefix} 错题样本#{idx}：{q_tpl}"
        answer = random.choice(answers)
        created_at = now - timedelta(days=random.randint(0, 240), minutes=random.randint(0, 1439))

        rows.append(
            ErrorQuestion(
                question=question,
                answer=answer,
                knowledge_point=kp,
                error_type=err_type,
                image_path=None,
                created_at=created_at,
            )
        )

    s.add_all(rows)
    s.commit()

    total = s.query(ErrorQuestion).count()
    qmark = s.query(ErrorQuestion).filter(ErrorQuestion.question.like('%?%')).count()
    print({"removed": removed, "inserted": len(rows), "total": total, "with_qmark": qmark})
finally:
    s.close()
