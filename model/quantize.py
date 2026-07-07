# model/quantize.py
import torch
import time
import logging
import json
from transformers import BertTokenizer, BertForSequenceClassification
from model.predict import SentimentPredictor
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelQuantizer:
    def __init__(self, model_path='model/weights/best_model'):
        self.model_path = model_path
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        
    def quantize_dynamic(self):
        """动态量化"""
        logger.info("开始动态量化...")
        
        quantized_model = torch.quantization.quantize_dynamic(
            self.model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        
        # 保存量化模型
        save_path = 'model/weights/quantized_model'
        os.makedirs(save_path, exist_ok=True)
        quantized_model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        
        logger.info(f"量化模型已保存: {save_path}")
        return quantized_model
    
    def compare_performance(self, test_texts):
        """对比原版和量化版性能"""
        logger.info("=" * 60)
        logger.info("性能对比测试")
        logger.info("=" * 60)
        
        # 原版模型
        original_predictor = SentimentPredictor(self.model_path)
        
        # 量化模型
        quantized_predictor = SentimentPredictor('model/weights/quantized_model')
        
        results = {
            'original': {'times': [], 'predictions': []},
            'quantized': {'times': [], 'predictions': []}
        }
        
        for text in test_texts:
            # 原版
            start = time.time()
            orig_result = original_predictor.predict_single(text)
            orig_time = time.time() - start
            
            # 量化版
            start = time.time()
            quant_result = quantized_predictor.predict_single(text)
            quant_time = time.time() - start
            
            results['original']['times'].append(orig_time)
            results['original']['predictions'].append(orig_result)
            results['quantized']['times'].append(quant_time)
            results['quantized']['predictions'].append(quant_result)
        
        # 统计
        avg_orig = sum(results['original']['times']) / len(results['original']['times'])
        avg_quant = sum(results['quantized']['times']) / len(results['quantized']['times'])
        
        logger.info(f"\n原版模型平均耗时: {avg_orig*1000:.2f}ms")
        logger.info(f"量化模型平均耗时: {avg_quant*1000:.2f}ms")
        logger.info(f"加速比: {avg_orig/avg_quant:.2f}x")
        logger.info(f"性能提升: {(1 - avg_quant/avg_orig)*100:.1f}%")
        
        # 检查一致性
        match_count = 0
        for orig, quant in zip(
            results['original']['predictions'],
            results['quantized']['predictions']
        ):
            if orig['label'] == quant['label']:
                match_count += 1
        
        accuracy = match_count / len(test_texts)
        logger.info(f"预测一致性: {accuracy*100:.1f}%")
        
        # 保存结果
        summary = {
            'original_avg_ms': avg_orig * 1000,
            'quantized_avg_ms': avg_quant * 1000,
            'speedup': avg_orig / avg_quant,
            'consistency': accuracy
        }
        
        with open('reports/quantization_results.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return results

def main():
    test_texts = [
        "这个商品质量非常好，物流也很快",
        "垃圾产品，用了两天就坏了",
        "价格实惠，物有所值",
        "发货速度慢，包装破损",
        "一般般吧，没有想象中好",
        "非常满意的一次购物体验",
        "质量太差了，不会再买",
        "客服态度很好，问题解决了"
    ] * 5  # 重复以增加测试数据
    
    quantizer = ModelQuantizer()
    quantizer.quantize_dynamic()
    quantizer.compare_performance(test_texts)

if __name__ == "__main__":
    main()
