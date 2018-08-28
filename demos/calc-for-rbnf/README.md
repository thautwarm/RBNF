
普通计算器(建议时间10分钟)
=============================

- 整数和浮点数: `-1, 2.0, 3`
- 二元运算:`+, -, *, /, ^, %`
- 嵌套表达式`(1 + 2) * 3`

```
calc> (1 + 1) * 2 ^ 3
=> 16

```

HowTo
---------------

```

python 3.6
pip install -U Redy rbnf
python repl.py

```

如何让parser成为解释器
-------------------------

查看`calc-immediately.rbnf`是怎么做到的。
然后直接运行它:
```
rbnf run calc-immediately.rbnf
```