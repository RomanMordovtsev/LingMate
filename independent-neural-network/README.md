# LingMate — Independent Neural Network (Colab QLoRA prototype)

Этот раздел содержит рабочий прототип обучения локальной модели (Qwen2.5-3B-Instruct) с QLoRA на Colab.

## Состав
- `train_lora.py` — скрипт обучения, совместим с TRL ≥ 0.22 (новый API).
- `notebooks/LingMate_Colab_CLEAN.ipynb` — аккуратный ноутбук с шагами: GPU → Диск → Установка → Создание датасета → Обучение → Инференс.
- `data/processed/lingmate_sample.jsonl` — маленький демо-набор (опционально, для дымового прогона).

## Быстрый старт (Colab)
1. Подключить Google Drive, выбрать рабочую папку `/content/drive/MyDrive/LingMateColab`.
2. Установить зависимости:
   ```bash
   pip install --upgrade pip
   pip install "transformers>=4.43.3" "datasets>=2.20.0" "accelerate>=0.33.0" \
               "peft>=0.11.1" bitsandbytes sentencepiece evaluate tiktoken huggingface_hub
   pip install git+https://github.com/huggingface/trl.git
3. Записать/обновить train_lora.py, создать мини-датасет (см. ноутбук), запустить обучение:
   ```bash
   python train_lora.py \
    --data_path "/content/drive/MyDrive/LingMateColab/data/processed/lingmate_sample.jsonl" \
    --base_model Qwen/Qwen2.5-3B-Instruct \
    --output_dir "/content/drive/MyDrive/LingMateColab/checkpoints/qwen2p5-3b-lingmate" \
    --epochs 1 --lr 2e-4 --batch 1 --grad_accum 32 --max_len 512
4. Инференс — см. секцию «Быстрый инференс» в ноутбуке.

## Примечания
* На T4 держите --max_len 512, --batch 1, --grad_accum 32.
* Если отключён сэмплинг (do_sample=False), параметры temperature/top_p игнорируются.
* Временный пост-процесс (автоисправления испанских фраз) планируется добавить в следующем коммите.
