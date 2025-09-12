import pandas as pd

def compare_csv(file1, file2, key_column="bvid"):
    """
    比较两个 CSV 文件在指定列上的差异
    :param file1: 第一份 CSV 文件路径
    :param file2: 第二份 CSV 文件路径
    :param key_column: 用于比较的唯一标识列名（默认 bvid）
    """
    # 读取 CSV
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # 获取 key 列的唯一值集合
    set1 = set(df1[key_column].dropna())
    set2 = set(df2[key_column].dropna())

    # 计算差异
    same_items = set1 & set2
    new_items = set2 - set1
    disappeared_items = set1 - set2

    # 打印结果
    print(f"比较文件：\n  第一份：{file1}\n  第二份：{file2}")
    print(f"相同 {key_column} 数量: {len(same_items)}")
    print(f"新增 {key_column} 数量: {len(new_items)}")
    print(f"消失 {key_column} 数量: {len(disappeared_items)}")

    return {
        "same_count": len(same_items),
        "new_count": len(new_items),
        "disappeared_count": len(disappeared_items),
        "new_items": new_items,
        "disappeared_items": disappeared_items
    }

# 示例调用
if __name__ == "__main__":
    file_a = "C:/Projects/BVR/files/main_page_data/data_batch_20250806_164815.csv"
    file_b = "C:/Projects/BVR/files/main_page_data/data_batch_20250807_164825.csv"
    compare_csv(file_a, file_b)
