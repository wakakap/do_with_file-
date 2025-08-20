import json
import sys

def find_duplicate_keys(file_path):
    """
    检查JSON文件的第一层是否有重复的键。

    参数:
    file_path (str): 需要检查的JSON文件路径。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 定义一个自定义的object_pairs_hook函数来捕获重复项
            seen_keys = set()
            duplicates = set()

            def duplicate_check_hook(pairs):
                """在解析时检查重复键的钩子函数。"""
                for key, value in pairs:
                    if key in seen_keys:
                        duplicates.add(key)
                    else:
                        seen_keys.add(key)
                # 这个hook必须返回一个字典，但我们只是用它来检查，
                # 所以我们只返回原始的键值对构成的字典。
                return dict(pairs)

            # 使用 object_pairs_hook 加载 JSON
            json.load(f, object_pairs_hook=duplicate_check_hook)

            # 检查是否有重复项被发现
            if duplicates:
                print("在JSON文件的第一层中发现以下重复的项目：")
                for key in duplicates:
                    print(f"- {key}")
            else:
                print("JSON文件的第一层中没有发现重复的项目。")

    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 未找到。")
    except json.JSONDecodeError as e:
        print(f"错误：解析JSON文件时出错。请确保文件格式正确。错误信息: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    json_file_path = "H:\BROWSER\\tags.json"
    find_duplicate_keys(json_file_path)