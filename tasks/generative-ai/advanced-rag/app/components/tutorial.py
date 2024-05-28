import streamlit as st

def tutorial():
    st.markdown("## 使い方")
    st.write("サイドバーの Kendra Index ID をセットし、上のテキストボックスに質問を入力してください。")
    st.markdown("""
### 質問例
- Amazon Kendra を使って Web サイトのコンテンツを検索可能にしたいと考えています。クロールの対象とする URL を制限する方法はありますか?
- Knowledge Bases for Amazon Bedrock ではどういったベクトルデータベースを利用できますか？
- Kendra で使用できるデータソースを全部教えて
- Amazon Kendra がサポートしているユーザーアクセス制御の方法は？
- Amazon Kendra の検索分析のメトリクスには何がありますか？
- Amazon Bedrock で Claude 3 Sonnet の基盤モデルに関する情報を取得する Python コードを教えて
- ナレッジベースでの embedding モデルの選択肢は？
- Bedrock の agent 機能は東京リージョンでは使えますか？
- Amazon Kendraで検索結果のランキングロジックをカスタマイズできますか？
- Amazon Bedrock でモデルにアクセスするには何が必要ですか？

### 設定項目
- 「RAG の結果を表示」のボックスにチェックを入れると、Kendra Query API の応答だけでなく、Kendra Retrieve API の応答を利用した RAG の回答も表示されます。
- Pre-retrieval / Post-retrieval method でそれぞれの Advanced RAG の手法のオンオフを設定できます。""")
