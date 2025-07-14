# check_bcr.py
import inspect
import bar_chart_race

print("--- 正在检查已安装的 bar_chart_race 库 ---")

try:
    # 获取 bar_chart_race 函数的完整参数规格
    spec = inspect.getfullargspec(bar_chart_race.bar_chart_race)
    
    print("\n检查成功！")
    print(f"您安装的 bar_chart_race.bar_chart_race 函数支持以下参数：")
    print("--------------------------------------------------")
    for arg in spec.args:
        print(arg)
    print("--------------------------------------------------")
    
    if spec.varkw:
        print(f"\n它还支持任意关键字参数 (**{spec.varkw})。")

except AttributeError:
    print("\n错误：无法找到 bar_chart_race.bar_chart_race 函数。")
    print("请确认您已正确安装 'bar-chart-race' 库。")
except Exception as e:
    print(f"\n发生未知错误: {e}")

print("\n--- 检查完毕 ---")