
# Welcome to Chococones Project!

1. 仮想環境作成

    ```
    $ python3 -m venv .venv
    ```

2. 仮想環境起動

    Linux or Mac
    ```
    $ source .venv/bin/activate
    ```

    Win

    ```
    % .venv\Scripts\activate.bat
    ```

3. 依存ライブラリインストール

    ```
    $ pip install -r requirements.txt
    ```

4. (そのリージョンでやったことがなければ)
   ```
   $ cdk bootstrap
   ```


5. デプロイ

    ```
    $ cdk deploy
    ```

