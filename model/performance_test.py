# model/performance_test.py
"""
第二阶段 C2-07：模型性能复测
记录 Accuracy、F1、响应时间
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from model.predict import predict_sentiment


def test_model_performance():
    """完整的模型性能测试"""
    print("=" * 70)
    print("📊 第二阶段 C2-07：模型性能复测")
    print("=" * 70)
    
    # 1. 加载测试数据
    test_path = 'data/processed/test.csv'
    if not os.path.exists(test_path):
        print("❌ 测试数据不存在，请先运行: python model/data_preprocess.py")
        return None
    
    test_df = pd.read_csv(test_path)
    texts = test_df['clean_content'].tolist()
    true_labels = test_df['label'].tolist()
    
    print(f"\n📁 测试样本数: {len(texts)}")
    
    if len(texts) == 0:
        print("❌ 测试集为空")
        return None
    
    # 2. 推理并计时
    print("\n⏳ 正在推理...")
    pred_labels = []
    confidences = []
    times = []
    
    for i, text in enumerate(texts):
        start = time.time()
        result = predict_sentiment(text)
        elapsed = time.time() - start
        
        pred_labels.append(result['label'])
        confidences.append(result.get('confidence', 0))
        times.append(elapsed)
        
        if (i + 1) % 10 == 0 or i == len(texts) - 1:
            print(f"  进度: {i+1}/{len(texts)}")
    
    # 3. 计算指标
    print("\n📊 计算评估指标...")
    
    acc = accuracy_score(true_labels, pred_labels)
    
    if len(set(true_labels)) > 1 and len(set(pred_labels)) > 1:
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='binary'
        )
    else:
        precision = recall = f1 = 0.0
        print("⚠️ 注意：测试集中只有一种类别，无法计算二分类指标")
    
    # 4. 混淆矩阵
    cm = confusion_matrix(true_labels, pred_labels)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    
    # 5. 性能统计
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    sorted_times = sorted(times)
    p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0
    p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0
    
    # 6. 输出结果
    print("\n" + "=" * 70)
    print("📈 模型指标")
    print("=" * 70)
    print(f"  准确率 (Accuracy):     {acc:.4f}")
    print(f"  精确率 (Precision):    {precision:.4f}")
    print(f"  召回率 (Recall):       {recall:.4f}")
    print(f"  F1分数:                {f1:.4f}")
    print()
    print(f"  混淆矩阵:")
    print(f"    TN={tn}, FP={fp}")
    print(f"    FN={fn}, TP={tp}")
    
    print("\n" + "=" * 70)
    print("⚡ 性能统计")
    print("=" * 70)
    print(f"  平均响应时间:          {avg_time*1000:.2f} ms")
    print(f"  最小响应时间:          {min_time*1000:.2f} ms")
    print(f"  最大响应时间:          {max_time*1000:.2f} ms")
    print(f"  P95响应时间:           {p95*1000:.2f} ms")
    print(f"  P99响应时间:           {p99*1000:.2f} ms")
    print(f"  总耗时:                {sum(times):.2f} s")
    print(f"  吞吐量:                {len(texts)/sum(times):.2f} 条/秒")
    
    # 7. 保存结果
    results = {
        'test_info': {
            'total_samples': len(texts),
            'positive_samples': int(sum(true_labels)),
            'negative_samples': int(len(true_labels) - sum(true_labels))
        },
        'metrics': {
            'accuracy': round(acc, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}
        },
        'performance': {
            'avg_ms': round(avg_time * 1000, 2),
            'min_ms': round(min_time * 1000, 2),
            'max_ms': round(max_time * 1000, 2),
            'p95_ms': round(p95 * 1000, 2),
            'p99_ms': round(p99 * 1000, 2),
            'total_seconds': round(sum(times), 2),
            'throughput_per_sec': round(len(texts)/sum(times), 2)
        },
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 保存 JSON
    os.makedirs('reports', exist_ok=True)
    with open('reports/model_performance_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 保存 Markdown
    md_path = 'reports/model_performance_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 模型性能复测报告\n\n")
        f.write(f"**测试时间**: {results['timestamp']}\n\n")
        f.write("## 1. 测试信息\n\n")
        f.write(f"| 项目 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 测试样本数 | {results['test_info']['total_samples']} |\n")
        f.write(f"| 正向样本 | {results['test_info']['positive_samples']} |\n")
        f.write(f"| 负向样本 | {results['test_info']['negative_samples']} |\n\n")
        f.write("## 2. 模型指标\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 准确率 | {results['metrics']['accuracy']:.4f} |\n")
        f.write(f"| 精确率 | {results['metrics']['precision']:.4f} |\n")
        f.write(f"| 召回率 | {results['metrics']['recall']:.4f} |\n")
        f.write(f"| F1分数 | {results['metrics']['f1']:.4f} |\n\n")
        f.write("## 3. 性能统计\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 平均响应时间 | {results['performance']['avg_ms']} ms |\n")
        f.write(f"| 最小响应时间 | {results['performance']['min_ms']} ms |\n")
        f.write(f"| 最大响应时间 | {results['performance']['max_ms']} ms |\n")
        f.write(f"| P95响应时间 | {results['performance']['p95_ms']} ms |\n")
        f.write(f"| P99响应时间 | {results['performance']['p99_ms']} ms |\n")
        f.write(f"| 吞吐量 | {results['performance']['throughput_per_sec']} 条/秒 |\n")
    
    print(f"\n✅ 报告已保存:")
    print(f"   JSON: reports/model_performance_report.json")
    print(f"   Markdown: {md_path}")
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    
    return results


def main():
    results = test_model_performance()
    if results:
        print(f"\n✅ C2-07 模型性能复测完成！")


if __name__ == "__main__":
    main()