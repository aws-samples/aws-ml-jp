import os
import json
import boto3
import logging
from strands import Agent, tool
from typing import Dict, Any, List
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.session import MemorySessionManager
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.memory.constants import StrategyType, ConversationalMessage, MessageRole

# logging の設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("event-agent")

# AgentCore App を初期化
app = BedrockAgentCoreApp()

# 各種環境変数を設定
MODEL_ID = os.getenv('MODEL_ID')
MEMORY_ID = os.getenv('MEMORY_ID')
REGION = os.getenv('AWS_REGION')
KB_ID = os.getenv('KB_ID')

agent = None
bedrock_agent_runtime = None

# Strands Agents が提供する HookProvider クラスを継承し
# MemoryHookProvider クラスを作成
class MemoryHookProvider(HookProvider):
    """AgentCore Memory と統合するためのカスタムフックプロバイダークラス"""
    
    def __init__(self):
        logger.info(f"Initializing MemoryHookProvider")
        self.memory_session_manager = MemorySessionManager(MEMORY_ID, REGION)
    
    # エージェント初期化時に長期メモリから User Preferences を検索
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load user preferences when agent starts"""
        logger.info("🎯 Agent initialization - loading preferences")

        # actor_id を取得        
        actor_id = event.agent.state.get("actor_id")
        
        if not actor_id:
            logger.warning("Missing actor_id")
            return
        
        try:
            # 長期メモリからユーザーの好みを取得
            preferences = self.memory_session_manager.search_long_term_memories(
                namespace_prefix=f"/users/{actor_id}/preferences",
                # 「ユーザーの設定・興味・背景」を問い合わせるクエリをハードコード
                query="What are the user's preferences, interests, and background?",
                # 類似情報を最大 5 件取得してメッセージに追加
                top_k=5
            )
            
            # User Preferences が取得できた場合
            if preferences:
                logger.info(f"✅ Loaded {len(preferences)} preferences")
                pref_messages = []
                # 取得した User Preferences のデータを整形
                for pref in preferences:
                    pref_text = pref.get('content', {}).get('text', '')
                    if pref_text:
                        try:
                            pref_json = json.loads(pref_text)
                            pref_messages.append(f"- {pref_json.get('preference', pref_text)}")
                        except:
                            pref_messages.append(f"- {pref_text}")
                
                if pref_messages:
                    context = "\n".join(pref_messages)

                    # User Preferences をメッセージに追加
                    # これによりエージェントはユーザーの好みに関するコンテキストを
                    # 持った状態で会話を開始できる
                    event.agent.system_prompt += f"\n\n**User Preferences:**\n{context}"
                    logger.info("✅ Added preferences to system prompt")
            else:
                logger.info("ℹ️ No preferences found yet")
                
        except Exception as e:
            logger.error(f"❌ Error loading preferences: {e}")
    
    # 新しいメッセージが追加される度に発火する
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory"""
        logger.info("💬 Message added - storing in memory")
        
        # actor_idを取得
        actor_id = event.agent.state.get("actor_id")
        # session_idを取得
        session_id = event.agent.state.get("session_id")
        
        if not all([actor_id, session_id]):
            logger.warning("Missing required state values")
            return
        
        try:
            messages = event.agent.messages
            # 最後のメッセージからコンテンツとロールを取得し、
            # AgentCore Memory のセッションマネージャーへ会話メッセージとして送信
            last_message = messages[-1]
            message_content = str(last_message.get("content", ""))
            if last_message["role"] == "user":
                message_role = MessageRole.USER
            elif last_message["role"] == "assistant":
                message_role = MessageRole.ASSISTANT
            
            # actor_id と session_id を指定して
            # 短期メモリにメッセージを送信
            # これにより論理的なデータ分離が実現
            self.memory_session_manager.add_turns(
                actor_id=actor_id,
                session_id=session_id,
                messages=[ConversationalMessage(message_content, message_role)]
            )
            logger.info("✅ Message stored")
            
        except Exception as e:
            logger.error(f"❌ Error storing message: {e}")

    # 作成した hooks を hook registory に登録
    # これによりエージェントは初期化時やメッセージ追加時に実行すべきコールバックを認識    
    def register_hooks(self, registry: HookRegistry):
        """Register hooks with the agent"""
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)

# @tool デコレータをつけた関数はエージェントによってツールとして認識される
@tool
def search_summit_session(query: str) -> List[Dict[str, Any]]:
    # エージェントは docustring を読んで、ツールを実行するかどうかの判断を行う
    """
    セマンティック検索を使用して、ナレッジベースからAWS Summitのセッションを検索します。

    ユーザーがAWS Summitのセッションに関する推奨情報を求めた場合や、
    ユーザーの興味に基づいて関連するセッションを見つけたい場合に、このツールをご利用ください。

    Args:
        query: どのようなセッションを検索するかを指定する検索クエリ
        max_results: 返却するセッションの最大結果数 (default: 5, max: 10)

    Returns:
        関連するAWS Summit セッションの詳細が書かれたリスト
    """
    global bedrock_agent_runtime, KB_ID
    
    try:
        if not bedrock_agent_runtime:
            bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)
        
        # ナレッジベース検索APIの呼び出し
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        # 結果の抽出とフォーマット
        results = []
        for idx, item in enumerate(response.get('retrievalResults', []), 1):
            result = {
                'rank': idx,
                'content': item.get('content', {}).get('text', ''),
                'score': item.get('score', 0.0)
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        return [{"error": str(e)}]

def initialize_agent(actor_id, session_id):
    """エージェントの初期化"""
    global agent
    
    # Bedrock モデルの初期化
    model = BedrockModel(model_id=MODEL_ID)
    # MemoryHookProvider の初期化
    memory_hook = MemoryHookProvider()
    
    agent = Agent(
        model=model,
        hooks=[memory_hook],
        tools=[search_summit_session],
        system_prompt="""あなたは、長期記憶と知識検索機能を備えたインテリジェントなイベントアシスタントです。
        search_summit_session を使用してセッション情報を検索してください。
        最初の検索で十分な情報が得られた場合は、追加のツール呼び出しを行わないでください。
        ユーザーの設定を記憶し、パーソナライズされたおすすめ情報を提供してください。
        """,
        state={
            "actor_id": actor_id,
            "session_id": session_id
        }
    )

# @app.entrypoit デコレータをつけた関数が
# Amazon Bedrock AgentCore Runtime から最初に呼ばれる
@app.entrypoint
def runtime_agent(payload, context):
    """
    AgentCore Runtime から呼び出されるメインのエントリーポイント
    """
    global agent
    
    user_input = payload.get("prompt")
    actor_id = payload.get("actor_id")
    session_id = context.session_id
    
    if not user_input:
        return "Error: Missing 'prompt' field"
    
    # 最初のリクエストが来たらエージェントを初期化
    if agent is None:
        initialize_agent(actor_id, session_id)
            
    # エージェントの呼び出し
    response = agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
