"""
Vanilla RNN model for temperature prediction.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from typing import Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from src.preprocess import load_and_clean, engineer_features, create_sequences, split_and_scale


class VanillaRNN(nn.Module):
    """Vanilla RNN model for temperature prediction."""
    
    def __init__(self, n_features: int, hidden_size: int = 128, 
                 num_layers: int = 2, dropout: float = 0.2):
        super(VanillaRNN, self).__init__()
        
        self.rnn = nn.RNN(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
            nonlinearity='tanh'
        )
        
        # FC head (using 'fc' name to match saved weights)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, n_features)
        _, hidden = self.rnn(x)
        # hidden shape: (num_layers, batch_size, hidden_size)
        # Take last layer's hidden state
        h = hidden[-1]  # (batch_size, hidden_size)
        
        x = self.fc(h)
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
             criterion: nn.Module, device: str) -> Tuple[float, float]:
    """Validate model on validation set."""
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch.unsqueeze(1))
            mae = torch.mean(torch.abs(y_pred - y_batch.unsqueeze(1)))
            
            total_loss += loss.item()
            total_mae += mae.item()
    
    return total_loss / len(val_loader), total_mae / len(val_loader)


def train_rnn():
    """Main training function for Vanilla RNN model."""
    print("\n" + "="*70)
    print("🚀 VANILLA RNN TRAINING")
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
    
    # Create sequences with shorter lookback for RNN
    print(f"Creating sequences with length {config.SEQ_LEN_RNN}...")
    X_seq, y_seq = create_sequences(X, y, config.SEQ_LEN_RNN)
    print(f"Sequence shape: X={X_seq.shape}, y={y_seq.shape}\n")
    
    # Split and scale
    (X_train, X_val, X_test, y_train, y_val, y_test,
     scaler_X, scaler_y) = split_and_scale(X_seq, y_seq, 
                                           config.RNN_SCALER_X, 
                                           config.RNN_SCALER_Y)
    
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
    print("🏗️  Building Vanilla RNN model...")
    model = VanillaRNN(
        n_features=len(feature_cols),
        hidden_size=128,
        num_layers=2,
        dropout=0.2
    )
    model = model.to(device)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}\n")
    
    # Loss and optimizer
    criterion = nn.HuberLoss(delta=1.5)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', 
                                                      factor=0.5, patience=3)
    
    # Training loop
    print("📈 Training...\n")
    print("Epoch | Train Loss | Val Loss | MAE | R²")
    print("-" * 50)
    
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(config.EPOCHS_RNN):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_mae = validate(model, val_loader, criterion, device)
        
        # Compute R² on validation
        with torch.no_grad():
            y_val_pred = []
            for X_batch, _ in val_loader:
                X_batch = X_batch.to(device)
                y_pred = model(X_batch)
                y_val_pred.append(y_pred.cpu().numpy())
            
            y_val_pred = np.concatenate(y_val_pred, axis=0).ravel()
            ss_res = np.sum((y_val_t.numpy() - y_val_pred) ** 2)
            ss_tot = np.sum((y_val_t.numpy() - np.mean(y_val_t.numpy())) ** 2)
            r2 = 1 - (ss_res / ss_tot)
        
        print(f"{epoch+1:4d}  | {train_loss:9.6f} | {val_loss:7.6f} | {val_mae:.6f} | {r2:.6f}")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), config.RNN_MODEL_PATH)
            print(f"           ✅ Best model saved (val_loss: {val_loss:.6f})")
        else:
            patience_counter += 1
            if patience_counter >= 10:  # RNN patience
                print(f"\n⏹️  Early stopping at epoch {epoch+1}")
                break
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE")
    print("="*70 + "\n")
    
    # Test evaluation
    print("🔍 Evaluating on test set...")
    model.load_state_dict(torch.load(config.RNN_MODEL_PATH, 
                                     map_location=device))
    model.eval()
    
    y_test_pred_list = []
    with torch.no_grad():
        for X_batch, _ in DataLoader(X_test_t, batch_size=config.BATCH_SIZE):
            X_batch = X_batch.to(device)
            y_pred = model(X_batch)
            y_test_pred_list.append(y_pred.cpu().numpy())
    
    y_test_pred = np.concatenate(y_test_pred_list, axis=0).ravel()
    
    # Compute metrics
    mae = np.mean(np.abs(y_test_pred - y_test_t.numpy()))
    rmse = np.sqrt(np.mean((y_test_pred - y_test_t.numpy()) ** 2))
    ss_res = np.sum((y_test_t.numpy() - y_test_pred) ** 2)
    ss_tot = np.sum((y_test_t.numpy() - np.mean(y_test_t.numpy())) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    print(f"MAE: {mae:.6f}")
    print(f"RMSE: {rmse:.6f}")
    print(f"R²: {r2:.6f}\n")
    
    print(f"📦 Model saved to: {config.RNN_MODEL_PATH}")
    print(f"📦 Scalers saved to: {config.RNN_SCALER_X}, {config.RNN_SCALER_Y}\n")




if __name__ == "__main__":
    train_rnn()
