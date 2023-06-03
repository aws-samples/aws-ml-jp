## Solutions

SageMaker と他のサービスを組み合わせ、業務プロセスの効率化や差別化を行うためのソリューションを格納/紹介します。

* [Simple Lex Kendra JP](https://github.com/aws-samples/simple-lex-kendra-jp)
  * 情報システム部門のヘルプデスクへの問い合わせ件数を削減するため、問い合わせを受け付けるチャットボットを設置するソリューションです。社内文書の検索を行う `Amazon Kendra` と問い合わせを受け付けるチャットボットの `Amazon Lex v2` を組み合わせて実装しています。 `AWS CDK` で構成されているため、シンプルにデプロイ可能です。
* [Review Analysis Dashboard](./review_analysis_dashboard/)
  * 自然言語処理でレビューを分析した結果を `Amazon Quicksight` でダッシュボードとして表示するソリューションです。オープンソースの形態素解析ツールである [GiNZA](https://megagonlabs.github.io/ginza/) を用いて時系列のレビュー数に加え頻出単語・係り受け関係を参照できます。[ブログ記事](https://aws.amazon.com/jp/blogs/news/amazon-sagemaker-amazon-quicksight-nlp-dashboard/)では、評価の低い DVD に対し 「まだ」「届く」の発生が多いことから発送遅延が原因ではないかといった分析例を示しています。
