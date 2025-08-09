import os
os.environ["WANDB_DISABLED"] = "true"  # отключить wandb

import argparse
from dataclasses import dataclass
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

SYSTEM_PROMPT = (
    "You are LingMate, a friendly, evidence-based language coach. "
    "Teach using short, clear steps, examples from real-life media, and spaced repetition hints. "
    "Adapt to the learner's level and never overwhelm."
)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--data_path', type=str, required=True)
    p.add_argument('--base_model', type=str, default='Qwen/Qwen2.5-3B-Instruct')
    p.add_argument('--output_dir', type=str, default='checkpoints/qwen2p5-3b-lingmate')
    p.add_argument('--max_len', type=int, default=512)
    p.add_argument('--epochs', type=int, default=1)
    p.add_argument('--lr', type=float, default=2e-4)
    p.add_argument('--batch', type=int, default=1)
    p.add_argument('--grad_accum', type=int, default=32)
    p.add_argument('--warmup_ratio', type=float, default=0.03)
    p.add_argument('--lora_r', type=int, default=16)
    p.add_argument('--lora_alpha', type=int, default=32)
    p.add_argument('--lora_dropout', type=float, default=0.05)
    p.add_argument('--no_4bit', action='store_true')
    return p.parse_args()

from dataclasses import dataclass
@dataclass
class Rec:
    lang: str
    source: str
    segment_type: str
    content: str

def make_chat(tokenizer, rec: Rec):
    user = (
        f"Learner language: {rec.lang}. Source={rec.source}, type={rec.segment_type}.\\n"
        f"Please teach me using a short, kind explanation (+ 1-2 examples)."
    )
    assistant = rec.content.strip()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
        {"role": "assistant", "content": assistant},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

def main():
    args = parse_args()
    compute_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    bnb_config = None
    if not args.no_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=compute_dtype,
        device_map='auto',
        quantization_config=bnb_config,
    )

    if bnb_config is not None:
        model = prepare_model_for_kbit_training(model)
        if hasattr(model, 'gradient_checkpointing_enable'):
            try:
                model.gradient_checkpointing_enable()
            except Exception:
                pass

    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias='none',
        task_type='CAUSAL_LM',
        target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],
    )
    model = get_peft_model(model, lora)

    raw = load_dataset('json', data_files=args.data_path, split='train')

    def map_to_text(batch):
        texts = []
        for lang, source, stype, content in zip(
            batch['lang'], batch['source'], batch['segment_type'], batch['content']
        ):
            rec = Rec(lang, source, stype, content)
            texts.append(make_chat(tokenizer, rec))
        return {'text': texts}

    ds = raw.map(map_to_text, batched=True, remove_columns=raw.column_names)

    def format_batch(example):
        return example["text"]

    config = SFTConfig(
        output_dir=args.output_dir,
        do_train=True,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type='cosine',
        warmup_ratio=args.warmup_ratio,
        logging_steps=10,
        save_steps=200,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=ds,
        processing_class=tokenizer,
        formatting_func=format_batch,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

if __name__ == '__main__':
    main()
