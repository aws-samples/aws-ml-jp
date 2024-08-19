# SageMaker での日本語 LLM の分散学習

こちらのサンプルコードは [SageMaker Model Parallel Library](https://docs.aws.amazon.com/sagemaker/latest/dg/model-parallel.html) を使用して SageMaker 上で日本語大規模言語モデルの Pretraining、Fine-Tuning、Instruction-Tuning が行うサンプルコードです。

## Notebooks

- smp-train-jp-gpt-neox-sharded-data-parallel.ipynb
  - 日本語 GPT Neox の Pretraining
- smp-finetune-jp-gpt-neox-sharded-data-parallel.ipynb
  - 日本語 GPT Neox (Rinna 3.6B) の Fine Tuning
- smp-instruct-jp-gpt-neox-sharded-data-parallel.ipynb
  - 日本語 GPT Neox (Rinna 3.6B) の Instruction Tuning
- smp-train-gpt-neox-sharded-data-parallel.ipynb
  - GPT NeoX の Pretraining（元のノートブックを少し改変したもの）
- convert-hf.ipynb
  - 分散学習スクリプトで保存した Model を HuggingFace 形式に変換して保存するコード
- data-preprocess.ipynb
  - 事前学習用にデータセットを前処理して FSx for Lustre に保存するサンプルコード

## 元サンプルコードからの変更点

このサンプルノートブックは [SageMaker の分散学習での GPT NeoX の Pretraining サンプル](https://github.com/aws/amazon-sagemaker-examples/tree/main/training/distributed_training/pytorch/model_parallel/gpt-neox) を元に日本語対応および Fine-tuning、Instruction Tuning 対応などを追加しています。

主な変更点は以下になります。

- 日本語対応
- Finetuning、Instruction Tuning ノートブックの追加
- Padding Collator の実装
  - Pretraining であればテキストをチャンク化するためバッチ内でのトークン長が一致しているため問題にならないが Instruction Tuning の際には Instruction ごとにトークン長が異なるため Padding が必要になる。[Transformers の Collator](https://github.com/huggingface/transformers/blob/main/src/transformers/data/data_collator.py#L402) の実装を元にバッチに Left Padding を施す変更を加えた。元々トークン長が一致している Pretraining には影響しない。
- その他、試行錯誤しやすいように細かな変更をいくつか追加しています

## おすすめのリソース

- [大規模言語モデルを Amazon SageMaker 上で学習する際のベストプラクティス](https://aws.amazon.com/jp/blogs/news/training-large-language-models-on-amazon-sagemaker-best-practices/)
- [SageMaker 分散モデル並列処理のベストプラクティス](https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/model-parallel-best-practices.html)
- [GPT-J の分散学習についての AWS ブログ](https://aws.amazon.com/blogs/machine-learning/fine-tune-gpt-j-using-an-amazon-sagemaker-hugging-face-estimator-and-the-model-parallel-library/)
- [Amazon SageMaker 分散学習ドキュメント](https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/distributed-training.html)
