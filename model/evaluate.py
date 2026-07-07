# model/evaluate.py - 修正版
import torch
import pandas as pd
import numpy as np
import json
import os
import logging
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvaluationDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        encoding = self.tokenizer(text, truncation=True, padding='max_length', 
                                 max_length=self.max_length, return_tensors='pt')
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def evaluate_model():
    """评估模型"""
    model_path = 'model/weights/best_model'
    
    # 检查模型是否存在
    if not os.path.exists(model_path) or not os.path.exists(os.path.join(model_path, 'config.json')):
        logger.error(f"模型不存在: {model_path}，请先训练模型")
        logger.info("尝试使用预训练模型进行评估...")
        model_path = 'bert-base-chinese'
    
    device = torch.device('cpu')
    logger.info(f"使用设备: {device}")
    
    # 加载模型
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path).to(device)
    model.eval()
    
    # 加载测试数据
    test_path = 'data/processed/test.csv'
    if not os.path.exists(test_path):
        logger.error(f"测试数据不存在: {test_path}")
        return
    
    df = pd.read_csv(test_path)
    logger.info(f"加载测试数据: {len(df)} 条")
    
    dataset = EvaluationDataset(df['clean_content'].values, df['label'].values, tokenizer)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False)
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="评估中"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # 计算指标
    acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='binary')
    cm = confusion_matrix(all_labels, all_preds)
    
    results = {
        'accuracy': float(acc),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'confusion_matrix': cm.tolist()
    }
    
    logger.info(f"\n{'='*50}")
    logger.info(f"准确率: {acc:.4f}")
    logger.info(f"精确率: {precision:.4f}")
    logger.info(f"召回率: {recall:.4f}")
    logger.info(f"F1分数: {f1:.4f}")
    logger.info(f"混淆矩阵:\n{cm}")
    logger.info(f"{'='*50}")
    
    # 保存结果
    os.makedirs('reports', exist_ok=True)
    with open('reports/evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

if __name__ == "__main__":
    evaluate_model()