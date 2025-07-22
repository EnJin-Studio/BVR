import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 初始化模型（自动下载预训练模型）
model = SentenceTransformer('DMetaSoul/sbert-chinese-general-v2')

# 待测试的标签列表
#tags = ["alicesoft", "兰斯", "a社", "rance"]
tags = ["高松灯", "Mygo", "tomorin", "企鹅","哈哈哈"]

# 计算每个标签的嵌入向量
embeddings = model.encode(tags)

# 计算标签间的余弦相似度矩阵
sim_matrix = cosine_similarity(embeddings)

# 将相似度矩阵转换为DataFrame并打印
sim_df = pd.DataFrame(
    np.round(sim_matrix, 4),  # 保留4位小数
    columns=tags,
    index=tags
)

print("标签语义相似度矩阵:")
print(sim_df)

# 可选：输出原始相似度数值（未四舍五入）
print("\n原始相似度矩阵:")
print(sim_matrix)