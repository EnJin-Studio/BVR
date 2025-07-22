import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import re

# 配置参数
THRESHOLD = 0.7  # 语义相似度阈值
#MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'  # 中文多语言模型
MODEL_NAME = 'DMetaSoul/sbert-chinese-general-v2'  # 社交媒体强化
csv_path = "test.csv"   # CSV包含列: video_name, generated_tags, ground_truth_tags

# 加载预训练模型 (首次使用会自动下载)
model = SentenceTransformer(MODEL_NAME)


def preprocess_tags(tag_str):
    """清洗和分割标签字符串"""
    if not isinstance(tag_str, str):
        return []
    tags = re.split(r'[,，;；|]', tag_str)
    return [tag.strip() for tag in tags if tag.strip()]

def calculate_video_metrics(pred_tags, ref_tags, threshold=THRESHOLD):
    """计算单个视频的语义指标"""
    # 空值
    if not pred_tags or not ref_tags:
        print("Warning: Empty tags detected.")
        return {'sP': 0, 'sR': 0, 'sF1': 0}
    # 计算embedding
    pred_embeddings = model.encode(pred_tags)
    ref_embeddings = model.encode(ref_tags)
    
    # 计算余弦相似度矩阵
    sim_matrix = cosine_similarity(pred_embeddings, ref_embeddings)
    
    # sP: 生成中正确的
    matched_pred = 0
    for i in range(len(pred_tags)):
        max_sim = np.max(sim_matrix[i])
        if max_sim >= threshold:
            matched_pred += 1
    sP = matched_pred / len(pred_tags) if pred_tags else 0
    
    # sR: 参考中正确的
    matched_ref = 0
    for j in range(len(ref_tags)):
        max_sim = np.max(sim_matrix[:, j])
        if max_sim >= threshold:
            matched_ref += 1
    sR = matched_ref / len(ref_tags) if ref_tags else 0
    
    # sF1: F1分数
    sF1 = 2 * (sP * sR) / (sP + sR) if (sP + sR) > 0 else 0
    
    return {'sP': sP, 'sR': sR, 'sF1': sF1}

def evaluate_tag_generation(csv_path):
    """主评估函数"""
    df = pd.read_csv(csv_path)
    # 初始化结果存储
    results = []
    all_metrics = {'sP': [], 'sR': [], 'sF1': []}
    
    # 遍历每个视频
    for _, row in df.iterrows():
        # 预处理标签
        pred_tags = preprocess_tags(row['generated_tags'])
        ref_tags = preprocess_tags(row['ground_truth_tags'])
        # 计算指标
        metrics = calculate_video_metrics(pred_tags, ref_tags)
        
        # 存储结果
        video_result = {
            'video_name': row['video_name'],
            'num_pred': len(pred_tags),
            'num_ref': len(ref_tags),
            **metrics
        }
        results.append(video_result)
        
        # 聚合指标
        for key in all_metrics:
            all_metrics[key].append(metrics[key])
    
    # 计算全局平均值
    final_metrics = {f'avg_{k}': np.mean(v) for k, v in all_metrics.items()}
    final_metrics['avg_num_pred'] = np.mean([r['num_pred'] for r in results])
    final_metrics['avg_num_ref'] = np.mean([r['num_ref'] for r in results])
    
    # 创建结果DataFrame
    result_df = pd.DataFrame(results)
    summary_df = pd.DataFrame([final_metrics])
    
    return result_df, summary_df

# 使用示例
if __name__ == "__main__":
    video_results, summary = evaluate_tag_generation(csv_path)
    video_results.to_csv("video_level_results.csv", index=False)
    summary.to_csv("summary_metrics.csv", index=False)
    print("评估结果摘要:")
    print(summary)