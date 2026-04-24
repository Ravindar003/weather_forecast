"""
Transformer Neural Network (TNN) model for temperature prediction.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from typing import Tuple, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from src.preprocess import load_and_clean, engineer_features, create_sequences, split_and_scale


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for Transformer."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                             (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1), :]


class PosEncoder(nn.Module):
    """Positional encoder (matches saved model naming)."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PosEncoder, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                             (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1), :]


class TemperatureTransformer(nn.Module):
    """Transformer model for temperature prediction."""
    
    def __init__(self, n_features: int, d_model: int = 128, nhead: int = 4, 
                 num_layers: int = 4, dim_feedforward: int = 512, 
                 dropout: float = 0.1):
        super(TemperatureTransformer, self).__init__()
        
        self.embedding = nn.Linear(n_features, d_model)
        self.layer_norm_input = nn.LayerNorm(d_model)
        self.pos_encoder = PosEncoder(d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
            norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, 
                                                 num_layers=num_layers)
        
        # Head
        self.head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, n_features)
        x = self.embedding(x)
        x = self.layer_norm_input(x)
        x = self.pos_encoder(x)
        
        x = self.transformer(x)
        
        # Pool across time dimension
        x_avg = x.mean(dim=1)
        x_max = x.max(dim=1)[0]
        x = x_avg + x_max
        
        x = self.head(x)
        return x




def train_epoch(model: nn.Module, train_loader: DataLoader, 
                criterion: nn.Module, optimizer: optim.Optimizer, 
                device: str) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch.unsqueeze(1))
        
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(train_loader)


def validate(model: nn.Module, val_loader: DataLoader, 
             criterion: nn.Module, device: str) -> float:
    """Validate model on validation set."""
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch.unsqueeze(1))
            total_loss += loss.item()
    
    return total_loss / len(val_loader)


def train_tnn():
    """Main training function for Transformer model."""
    print("\n" + "="*70)
    print("🚀 TRANSFORMER NEURAL NETWORK (TNN) TRAINING")
    print("="*70 + "\n")
    
    # Set device
    device = torch.device(config.DEVICE)
    print(f"Using device: {device}\n")
    
    # Load and preprocess data
    print("📊 Loading and preprocessing data...")
    df = load_and_clean(config.DATA_PATH)
    df, feature_cols = engineer_features(df)
    
    X = df[feature_cols].values
    y = df[config.TARGET].values
    
    print(f"Data shape: X={X.shape}, y={y.shape}")
    print(f"Number of features: {len(feature_cols)}\n")
    
    # Create sequences
    print(f"Creating sequences with length {config.SEQ_LEN_TNN}...")
    X_seq, y_seq = create_sequences(X, y, config.SEQ_LEN_TNN)
    print(f"Sequence shape: X={X_seq.shape}, y={y_seq.shape}\n")
    
    # Split and scale
    (X_train, X_val, X_test, y_train, y_val, y_test,
     scaler_X, scaler_y) = split_and_scale(X_seq, y_seq, 
                                           config.TNN_SCALER_X, 
                                           config.TNN_SCALER_Y)
    
    # Convert to PyTorch tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train)
    X_val_t = torch.FloatTensor(X_val)
    y_val_t = torch.FloatTensor(y_val)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.FloatTensor(y_test)
    
    # Create dataloaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, 
                             shuffle=False)
    
    val_dataset = TensorDataset(X_val_t, y_val_t)
    val_loader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE, 
                           shuffle=False)
    
    # Build model
    print("🏗️  Building Transformer model...")
    model = TemperatureTransformer(
        n_features=len(feature_cols),
        d_model=128,
        nhead=4,
        num_layers=4,
        dim_feedforward=512,
        dropout=0.1
    )
    model = model.to(device)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}\n")
    
    # Loss and optimizer
    criterion = nn.HuberLoss(delta=1.5)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', 
                                                      factor=0.5, patience=5)
    
    # Training loop
    print("📈 Training...\n")
    print("Epoch | Train Loss | Val Loss | LR")
    print("-" * 45)
    
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(config.EPOCHS_TNN):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = validate(model, val_loader, criterion, device)
        
        # Get current learning rate
        current_lr = optimizer.param_groups[0]['lr']
        
        print(f"{epoch+1:4d}  | {train_loss:9.6f} | {val_loss:7.6f} | {current_lr:.2e}")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), config.TNN_MODEL_PATH)
            print(f"           ✅ Best model saved (val_loss: {val_loss:.6f})")
        else:
            patience_counter += 1
            if patience_counter >= config.PATIENCE:
                print(f"\n⏹️  Early stopping at epoch {epoch+1}")
                break
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE")
    print("="*70 + "\n")
    
    # Test evaluation
    print("🔍 Evaluating on test set...")
    model.load_state_dict(torch.load(config.TNN_MODEL_PATH, 
                                     map_location=device))
    model.eval()
    
    with torch.no_grad():
        y_test_t = y_test_t.to(device)
        X_test_t = X_test_t.to(device)
        y_pred = model(X_test_t)
        test_loss = criterion(y_pred, y_test_t.unsqueeze(1))
    
    print(f"Test Loss: {test_loss.item():.6f}")
    
    # Compute metrics
    y_pred_np = y_pred.cpu().numpy().ravel()
    y_test_np = y_test_t.cpu().numpy()
    
    mae = np.mean(np.abs(y_pred_np - y_test_np))
    rmse = np.sqrt(np.mean((y_pred_np - y_test_np) ** 2))
    ss_res = np.sum((y_test_np - y_pred_np) ** 2)
    ss_tot = np.sum((y_test_np - np.mean(y_test_np)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    print(f"MAE: {mae:.6f}")
    print(f"RMSE: {rmse:.6f}")
    print(f"R²: {r2:.6f}\n")
    
    print(f"📦 Model saved to: {config.TNN_MODEL_PATH}")
    print(f"📦 Scalers saved to: {config.TNN_SCALER_X}, {config.TNN_SCALER_Y}\n")


if __name__ == "__main__":
    train_tnn()
