# model/predict.py - 修正版
import torch
import re
import time
import os
from transformers import BertTokenizer, BertForSequenceClassification
from typing import List, Dict

class SentimentPredictor:
    def __init__(self, model_path=None):
        self.device = torch.device('cpu')
        
        # 如果模型不存在，使用预训练模型
        if model_path and os.path.exists(model_path) and os.path.exists(os.path.join(model_path, 'config.json')):
            self.tokenizer = BertTokenizer.from_pretrained(model_path)
            self.model = BertForSequenceClassification.from_pretrained(model_path)
        else:
            print("⚠️ 未找到微调模型，使用预训练模型（需要联网下载）")
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
            self.model = BertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=2)
        
        self.model.to(self.device)
        self.model.eval()
        self.max_length = 128
    
    def clean_text(self, text):
        if not text or not isinstance(text, str):
            return ""
        # 简单清洗
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+', '', text)
        text = re.sub(r'www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}', '', text)
        text = re.sub(r'[^a-zA-Z\u4e00-\u9fa5\d\s\.\?,;:!！？，。、]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def predict_single(self, text: str) -> Dict:
        clean_text = self.clean_text(text)
        
        if not clean_text:
            return {'label': -1, 'sentiment': 'unknown', 'confidence': 0.0, 
                    'strength': 0.0, 'clean_text': '', 'error': '文本为空'}
        
        encoding = self.tokenizer(clean_text, truncation=True, padding='max_length',
                                 max_length=self.max_length, return_tensors='pt')
        
        with torch.no_grad():
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)
            pred_label = torch.argmax(outputs.logits, dim=1).item()
            confidence = torch.max(probs, dim=1).values.item()
        
        if pred_label == 1:
            strength = confidence * 10
            sentiment = 'positive'
        else:
            strength = (1 - confidence) * 10
            sentiment = 'negative'
        
        return {
            'label': pred_label,
            'sentiment': sentiment,
            'confidence': confidence,
            'strength': round(strength, 2),
            'clean_text': clean_text,
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        return [self.predict_single(text) for text in texts]

_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        # 尝试加载微调模型，如果不存在则使用预训练
        model_path = 'model/weights/best_model'
        if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, 'config.json')):
            _predictor = SentimentPredictor(model_path)
        else:
            _predictor = SentimentPredictor()  # 使用预训练
    return _predictor

def predict_sentiment(text: str) -> Dict:
    return get_predictor().predict_single(text)

def predict_batch(texts: List[str]) -> List[Dict]:
    return get_predictor().predict_batch(texts)

if __name__ == "__main__":
    # 测试
    test_texts = [
        "这个商品质量非常好，物流也很快，强烈推荐！",
        "垃圾产品，用了两天就坏了，售后态度也很差。",
        "价格实惠，物有所值。",
        "一般般吧。"
    ]
    predictor = get_predictor()
    print("=" * 50)
    print("情感分析测试")
    print("=" * 50)
    for text in test_texts:
        result = predictor.predict_single(text)
        print(f"\n原文: {text}")
        print(f"  情感: {result['sentiment']}")
        print(f"  置信度: {result['confidence']:.4f}")
        print(f"  强度: {result['strength']:.2f}/10")