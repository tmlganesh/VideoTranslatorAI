"""
Training entrypoint wrapper.

Usage:
    python backend/training/train.py --dataset-dir ./Datasets/en_te --output-dir ./backend/training/models/mt5-en-te --direction en-te
"""

from train_mt5_en_te import main


if __name__ == "__main__":
    main()
