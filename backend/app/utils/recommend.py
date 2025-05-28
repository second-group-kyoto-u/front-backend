from app.models.user import User, get_user_by_id
from app.models.thread import Thread, UserHeartThread # UserHeartThread を追加
from app.models import db
from app.models.event import Event, UserHeartEvent, UserMemberGroup, TagMaster, EventTagAssociation
from sqlalchemy import desc, func # func をインポート
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import unicodedata
import re
from datetime import datetime, timezone, timedelta
from janome.tokenizer import Tokenizer
# Analyzer, CharFilter, TokenFilter は直接使っていないのでコメントアウトしてもOK
# from janome.analyzer import Analyzer
# from janome.charfilter import UnicodeNormalizeCharFilter, RegexReplaceCharFilter
# from janome.tokenfilter import POSKeepFilter, LowerCaseFilter, ExtractAttributeFilter


# --- タイムゾーン定義 ---
JST = timezone(timedelta(hours=9))
CURRENT_TIME_JST = datetime.now(JST)
print(f"基準時刻 (JST): {CURRENT_TIME_JST}")


# --- Janome Tokenizerの初期化 ---
try:
    TOKENIZER = Tokenizer()
    print("Janome Tokenizerの初期化完了。")
except Exception as e:
    print(f"Janome Tokenizerの初期化に失敗しました: {e}")
    TOKENIZER = None

# --- ストップワードリストの準備 ---
# (前回と同様のDEFAULT_STOPWORDSをここに記述するか、ファイルから読み込む)
DEFAULT_STOPWORDS = {
    "の", "は", "が", "です", "ます", "こと", "もの", "それ", "あれ", "これ", "私", "あなた",
    "する", "いる", "なる", "思う", "いう", "できる", "ない", "ある", "いく", "くる",
    "とても", "すごく", "ちょっと", "たくさん", "いろいろ", "本当に", "あとで",
    "ため", "よう", "そう", "みたい", "みたいに", "なので", "そして", "また", "でも",
    "日", "月", "年", "時", "分", "秒", "さん", "ちゃん", "くん",
    "笑", "w", "ww", "www", "草",
    "!", "?", "。", "、", ".", ",", "(", ")", "「", "」", "『", "』", "【", "】",
    " ", "　"
}
STOPWORDS = DEFAULT_STOPWORDS
# try-exceptブロックでのファイル読み込みも良いですが、ここではシンプルにデフォルトを使用
if not STOPWORDS:
    print("[Warning] ストップワードが空です。")
else:
    print(f"ストップワードを {len(STOPWORDS)}語 準備しました。")


# --- ハイパーパラメータ ---
LAMBDA_DECAY = 0.01
ALPHA_PROFILE_WEIGHT = 0.7
NUM_RECOMMENDATIONS = 5
TFIDF_MAX_FEATURES = 5000 # TF-IDFで考慮する特徴語の最大数 (メモリと性能のバランス)


################################### データベースアクセス関数群 ###################################

# --- 初期推薦用関数 (get_popular_events, get_events_by_tags, get_initial_recommendations_for_user) ---
# (提供されたコードをそのまま利用、ただし UserUserTagAssociation は UserTagAssociation に修正)

def get_popular_events(limit=5, exclude_event_ids=None):
    if exclude_event_ids is None: exclude_event_ids = set()
    query = Event.query.filter(Event.is_deleted == False, Event.status != 'ended')
    heart_counts_subquery = db.session.query(
        UserHeartEvent.event_id, func.count(UserHeartEvent.user_id).label('heart_count')
    ).group_by(UserHeartEvent.event_id).subquery()
    query = query.outerjoin(heart_counts_subquery, Event.id == heart_counts_subquery.c.event_id)
    query = query.order_by(
        desc(heart_counts_subquery.c.heart_count), desc(Event.current_persons), desc(Event.published_at)
    )
    if exclude_event_ids: query = query.filter(Event.id.notin_(exclude_event_ids))
    return query.limit(limit).all()

def get_events_by_tags(tag_ids, limit=10, exclude_event_ids=None):
    if exclude_event_ids is None: exclude_event_ids = set()
    query = Event.query.join(EventTagAssociation).filter(
        Event.is_deleted == False, Event.status != 'ended', EventTagAssociation.tag_id.in_(tag_ids)
    )
    if exclude_event_ids: query = query.filter(Event.id.notin_(exclude_event_ids))
    return query.distinct().order_by(desc(Event.published_at)).limit(limit).all()

def get_initial_recommendations_for_user(user_id: str, num_popular=3, num_tag_matched=5):
    user = get_user_by_id(user_id)
    if not user: print(f"ユーザーが見つかりません: {user_id}"); return []
    recommendations = []; recommended_event_ids = set()
    interacted_event_ids = set()
    if hasattr(user, 'memberships'): interacted_event_ids.update([m.event_id for m in user.memberships])
    if hasattr(user, 'hearted_events'): interacted_event_ids.update([e.id for e in user.hearted_events])
    
    popular_events = get_popular_events(limit=num_popular, exclude_event_ids=interacted_event_ids)
    for event in popular_events:
        if event.id not in recommended_event_ids:
            recommendations.append({'id': event.id, 'title': event.title, 'reason': '人気'})
            recommended_event_ids.add(event.id)

    user_tag_ids = []
    # Userモデルのtagsリレーションは UserTagAssociation を指す想定 (event.py の UserTagAssociation)
    if hasattr(user, 'tags') and user.tags: # user.tags は UserTagAssociation のリスト
        try: user_tag_ids = [uta.tag_id for uta in user.tags]
        except Exception as e: print(f"ユーザーのタグID取得中にエラー: {e}")

    if user_tag_ids:
        exclude_ids_for_tags = recommended_event_ids.union(interacted_event_ids)
        tag_matched_events = get_events_by_tags(user_tag_ids, limit=num_tag_matched, exclude_event_ids=exclude_ids_for_tags)
        for event in tag_matched_events:
            if event.id not in recommended_event_ids:
                recommendations.append({'id': event.id, 'title': event.title, 'reason': 'タグ一致'})
                recommended_event_ids.add(event.id)
    else: print(f"ユーザー (ID: {user_id}) はタグを登録していません。")
    return recommendations

# --- コンテンツベース推薦用のデータ取得関数 ---
def get_db_user_recent_threads_data(user_id: str, limit: int = 100) -> list[tuple[str, str, datetime]]:
    """DBからユーザーの直近の投稿の(タイトル, メッセージ, 投稿日時)を取得"""
    try:
        threads = Thread.query.filter_by(author_id=user_id)\
                              .order_by(desc(Thread.published_at))\
                              .limit(limit)\
                              .all()
        return [(t.title or "", t.message or "", t.published_at) for t in threads]
    except Exception as e:
        print(f"[Error] DBからのユーザー投稿取得に失敗 (user_id: {user_id}): {e}")
        return []

def get_db_user_liked_threads_data(user_id: str, limit: int = 50) -> list[tuple[str, str]]:
    """DBからユーザーがいいねした投稿の(タイトル, メッセージ)を取得"""
    try:
        # UserHeartThread を介して Thread を取得
        liked_threads = db.session.query(Thread)\
                                  .join(UserHeartThread, UserHeartThread.thread_id == Thread.id)\
                                  .filter(UserHeartThread.user_id == user_id)\
                                  .order_by(desc(Thread.published_at)) \
                                  .limit(limit)\
                                  .all()
        return [(t.title or "", t.message or "") for t in liked_threads]
    except Exception as e:
        print(f"[Error] DBからのいいねした投稿取得に失敗 (user_id: {user_id}): {e}")
        return []

def get_db_all_active_events_data() -> list[tuple[str, str, str, list[str]]]:
    """DBから全てのアクティブなイベントの(ID, タイトル, 説明, タグ名リスト)を取得"""
    try:
        events = Event.query.filter(Event.is_deleted == False, Event.status != 'ended').all()
        events_data = []
        for e in events:
            tag_names = []
            if hasattr(e, 'tags') and e.tags: # e.tags は EventTagAssociation のリスト
                for eta in e.tags:
                    if hasattr(eta, 'tag') and eta.tag: # eta.tag は TagMaster オブジェクト
                        tag_names.append(eta.tag.tag_name)
            events_data.append((e.id, e.title or "", e.description or "", tag_names))
        return events_data
    except Exception as e:
        print(f"[Error] DBからのイベント情報取得に失敗: {e}")
        return []

print("データベースアクセス関数の準備完了。")

##################################### テキスト前処理関数 ############################################
# (前回提供の normalize_text, tokenize_and_filter, preprocess_text_pipeline をここに記述)
def normalize_text(text: str) -> str:
    if not text:
        return ""

    # Unicode正規化 (NFKCフォームを推奨: 全角カタカナ -> 半角カタカナ、全角英数 -> 半角英数など)
    text = unicodedata.normalize('NFKC', text)
    
    # アルファベットを小文字に統一
    text = text.lower()
    
    # URLやメンション、ハッシュタグなどを除去または特定のトークンに置換
    text = re.sub(r'https?://\S+', '', text)  # URL除去
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text) # メンション除去
    text = re.sub(r'#[^\s#]+', '', text)      # ハッシュタグ除去
    
    # 数字の扱い (例: 3桁以上の連続する数字を "<NUM>" トークンに置換)
    # text = re.sub(r'\d{3,}', '<NUM>', text) # 必要に応じて
    # または単純に数字を除去する場合
    # text = re.sub(r'\d+', '', text)

    # その他、不要と思われる記号の除去 (プロジェクトの性質に合わせて調整)
    # 半角記号をスペースに置換
    text = re.sub(r'[!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~]', ' ', text)
    # 全角記号 (一部) をスペースに置換
    text = re.sub(r'[「」『』【】（）]', ' ', text)
    # 連続する空白を一つにまとめる
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_and_filter(text: str, target_pos: list[str] = None, tokenizer: Tokenizer = None) -> list[str]:
    if not text: return []
    _tokenizer = tokenizer if tokenizer else TOKENIZER
    if _tokenizer is None: print("[Warning] Tokenizerが未初期化です。"); return []
    target_pos = target_pos if target_pos else ['名詞', '動詞', '形容詞', '副詞']
    tokens = _tokenizer.tokenize(text); processed_words = []
    for token in tokens:
        pos_major = token.part_of_speech.split(',')[0]
        if pos_major not in target_pos: continue
        word = token.base_form
        if word in STOPWORDS or len(word) == 0: continue
        if len(word) < 2 and not re.fullmatch(r'[ぁ-んァ-ヶー一-龠]+', word):
            if not word.isnumeric(): continue
        if word.isnumeric() and len(word) > 4: continue
        processed_words.append(word)
    return processed_words

def preprocess_text_pipeline(text_input: str | list[str], target_pos: list[str] = None, tokenizer: Tokenizer = None) -> list[str]:
    if not text_input: return []
    combined_text = " ".join(text_input) if isinstance(text_input, list) else text_input
    if not isinstance(combined_text, str): return []
    normalized_text = normalize_text(combined_text)
    return tokenize_and_filter(normalized_text, target_pos=target_pos, tokenizer=tokenizer)
print("テキスト前処理関数の準備完了。")

##################################### TF-IDFベクトル化 #############################################
TFIDF_VECTORIZER = None
TFIDF_VOCABULARY_FITTED = False

def fit_tfidf_vectorizer(corpus_texts: list[list[str]]):
    global TFIDF_VECTORIZER, TFIDF_VOCABULARY_FITTED
    if not corpus_texts:
        print("[Warning] TF-IDF学習用コーパスが空です。Vectorizerは学習されません。")
        TFIDF_VECTORIZER = None; TFIDF_VOCABULARY_FITTED = False
        return

    TFIDF_VECTORIZER = TfidfVectorizer(
        tokenizer=lambda x: x, preprocessor=lambda x: x, token_pattern=None, lowercase=False,
        max_features=TFIDF_MAX_FEATURES # 追加: 特徴語の最大数を制限
    )
    try:
        print(f"TF-IDF Vectorizerを学習中... コーパスサイズ: {len(corpus_texts)} ドキュメント")
        TFIDF_VECTORIZER.fit(corpus_texts); TFIDF_VOCABULARY_FITTED = True
        print(f"TF-IDF Vectorizerの学習完了。語彙数: {len(TFIDF_VECTORIZER.vocabulary_)}")
    except Exception as e:
        print(f"[Error] TF-IDF Vectorizerの学習に失敗: {e}"); TFIDF_VECTORIZER = None; TFIDF_VOCABULARY_FITTED = False

def get_tfidf_vector(processed_words: list[str]) -> np.ndarray | None:
    if not TFIDF_VOCABULARY_FITTED or TFIDF_VECTORIZER is None:
        print("[Warning] TF-IDF Vectorizerが学習されていません。ベクトル化をスキップします。")
        return None
    if not processed_words: return np.zeros(len(TFIDF_VECTORIZER.vocabulary_)) # 語彙数があればゼロベクトル
    try: return TFIDF_VECTORIZER.transform([processed_words]).toarray()[0]
    except Exception as e: print(f"[Error] TF-IDFベクトル生成失敗: {e}"); return None
print("TF-IDFベクトル化関数の準備完了。")


############################# 時間的重み付け & ユーザープロファイル構築 #############################
def calculate_time_decay_weight(post_time: datetime, current_time: datetime = CURRENT_TIME_JST, lambda_decay: float = LAMBDA_DECAY) -> float:
    if not isinstance(post_time, datetime) or not isinstance(current_time, datetime): return 0.1
    # タイムゾーンを強制的にJSTに合わせる (DBから取得したdatetimeオブジェクトの扱いによる)
    if post_time.tzinfo is None or post_time.tzinfo.utcoffset(post_time) is None:
        post_time = post_time.replace(tzinfo=JST) # ナイーブならJSTとみなす
    if current_time.tzinfo is None or current_time.tzinfo.utcoffset(current_time) is None:
        current_time = current_time.replace(tzinfo=JST)

    try:
        time_difference = current_time - post_time
        time_difference_hours = time_difference.total_seconds() / 3600.0
    except TypeError as e: # ナイーブとアウェアの比較などでエラーになる場合
        print(f"[Warning] 日時比較でエラー: {e}。post_time={post_time}, current_time={current_time}")
        return 0.1 # フォールバック

    if time_difference_hours < 0: return 0.01
    return np.exp(-lambda_decay * time_difference_hours)

def create_time_weighted_user_posts_profile(user_threads_vectors_with_time: list[tuple[np.ndarray, datetime]], lambda_decay: float = LAMBDA_DECAY) -> np.ndarray | None:
    if not user_threads_vectors_with_time: return None
    valid_vectors_with_time = [(vec, time) for vec, time in user_threads_vectors_with_time if vec is not None and isinstance(vec, np.ndarray)]
    if not valid_vectors_with_time: return None
    
    first_valid_vector_shape = valid_vectors_with_time[0][0].shape
    weighted_vectors_sum = np.zeros(first_valid_vector_shape); total_effective_weights = 0.0
    
    for vector, post_time in valid_vectors_with_time:
        weight = calculate_time_decay_weight(post_time, lambda_decay=lambda_decay)
        weighted_vectors_sum += vector * weight; total_effective_weights += weight
    return weighted_vectors_sum if total_effective_weights > 0 else np.zeros(first_valid_vector_shape) # 重みがなくてもゼロベクトルを返す

def create_liked_posts_profile(liked_threads_vectors: list[np.ndarray]) -> np.ndarray | None:
    if not liked_threads_vectors: return None
    valid_vectors = [vec for vec in liked_threads_vectors if vec is not None and isinstance(vec, np.ndarray)]
    if not valid_vectors: return None
    return np.mean(valid_vectors, axis=0)

def combine_user_profiles(user_posts_profile: np.ndarray | None, liked_posts_profile: np.ndarray | None, alpha: float = ALPHA_PROFILE_WEIGHT) -> np.ndarray | None:
    if user_posts_profile is None and liked_posts_profile is None: return None
    elif user_posts_profile is None: return liked_posts_profile
    elif liked_posts_profile is None: return user_posts_profile
    # 念のため、両プロファイルの形状が一致するか確認 (TF-IDF語彙が共通なら一致するはず)
    if user_posts_profile.shape != liked_posts_profile.shape:
        print(f"[Warning] 統合するプロファイルの形状が異なります: own={user_posts_profile.shape}, liked={liked_posts_profile.shape}")
        # この場合の戦略が必要 (例: どちらかを優先、エラー、など)
        # ここでは単純に user_posts_profile を優先する
        return user_posts_profile
    return alpha * user_posts_profile + (1 - alpha) * liked_posts_profile
print("時間的重み付け & プロファイル構築関数の準備完了。")

##################################### 類似度計算とランキング #######################################
def get_event_recommendations_for_user(user_id: str, num_recommendations: int = NUM_RECOMMENDATIONS) -> list[dict]:
    """
    指定されたユーザーIDに対して、コンテンツベースのイベント推薦を行います。
    """
    print(f"\n--- ユーザー ({user_id}) への推薦処理開始 ---")

    # 1. ユーザーの行動データをDBから取得
    user_threads_raw_data = get_db_user_recent_threads_data(user_id, limit=100)
    user_liked_threads_raw_data = get_db_user_liked_threads_data(user_id, limit=50)

    if not user_threads_raw_data and not user_liked_threads_raw_data:
        print(f"ユーザー ({user_id}) の投稿もいいねした投稿もありません。初期推薦を試みます。")
        return get_initial_recommendations_for_user(user_id) # フォールバック

    # 2. テキスト前処理とベクトル化の準備 (コーパスは全データから)
    #    本番環境では、TFIDF_VECTORIZERは学習済みでロードされる想定
    global TFIDF_VOCABULARY_FITTED
    if not TFIDF_VOCABULARY_FITTED:
        print("TF-IDF Vectorizerが未学習です。全データから学習を開始します...")
        corpus_for_tfidf = []
        # DBから全ユーザーの全投稿を取得してコーパスに追加 (非常に重い処理なので注意！)
        # ここではサンプル的に、現在のユーザーといいねした投稿、全イベントでコーパスを作る
        for title, message, _ in user_threads_raw_data:
            processed = preprocess_text_pipeline(f"{title} {message}")
            if processed: corpus_for_tfidf.append(processed)
        for title, message in user_liked_threads_raw_data:
            processed = preprocess_text_pipeline(f"{title} {message}")
            if processed: corpus_for_tfidf.append(processed)
        
        all_events_raw_data_for_corpus = get_db_all_active_events_data()
        for _, title, description, tags in all_events_raw_data_for_corpus:
            processed = preprocess_text_pipeline(" ".join(filter(None, [title, description] + tags)))
            if processed: corpus_for_tfidf.append(processed)
        
        if corpus_for_tfidf:
            fit_tfidf_vectorizer(corpus_for_tfidf)
        else:
            print("[Error] TF-IDF学習用コーパスが作成できませんでした。推薦を中止します。")
            return get_initial_recommendations_for_user(user_id) # フォールバック
    
    if not TFIDF_VOCABULARY_FITTED or TFIDF_VECTORIZER is None:
        print("[Error] TF-IDF Vectorizerの準備に失敗しました。初期推薦を試みます。")
        return get_initial_recommendations_for_user(user_id) # フォールバック

    # 3. ターゲットユーザーのプロファイル構築
    # 3a. ユーザー自身の投稿ベクトル (タイムスタンプ付き) を取得
    user_post_vectors_with_time = []
    for title, message, published_at in user_threads_raw_data:
        processed_words = preprocess_text_pipeline(f"{title} {message}")
        if processed_words:
            vec = get_tfidf_vector(processed_words)
            if vec is not None:
                user_post_vectors_with_time.append((vec, published_at))
    
    # 3b. ユーザーのいいねした投稿ベクトルを取得
    liked_post_vectors = []
    for title, message in user_liked_threads_raw_data:
        processed_words = preprocess_text_pipeline(f"{title} {message}")
        if processed_words:
            vec = get_tfidf_vector(processed_words)
            if vec is not None:
                liked_post_vectors.append(vec)

    # 3c. プロファイル構築
    user_own_profile = create_time_weighted_user_posts_profile(user_post_vectors_with_time)
    user_liked_profile = create_liked_posts_profile(liked_post_vectors)
    final_user_profile_vector = combine_user_profiles(user_own_profile, user_liked_profile)

    if final_user_profile_vector is None:
        print(f"ユーザー ({user_id}) の最終プロファイルベクトルは作成できませんでした。初期推薦を試みます。")
        return get_initial_recommendations_for_user(user_id) # フォールバック
    print(f"ユーザー ({user_id}) の最終プロファイルベクトル(一部): {final_user_profile_vector[:5]} (Shape: {final_user_profile_vector.shape})")

    # 4. イベントベクトルの準備
    all_events_raw_data = get_db_all_active_events_data()
    event_vectors_map = {} # {event_id: vector}
    event_titles_map = {} # {event_id: title}
    for event_id, title, description, tags in all_events_raw_data:
        processed_words = preprocess_text_pipeline(" ".join(filter(None, [title, description] + tags)))
        if processed_words:
            vec = get_tfidf_vector(processed_words)
            if vec is not None:
                event_vectors_map[event_id] = vec
                event_titles_map[event_id] = title
    
    if not event_vectors_map:
        print("[Warning] 推薦対象のイベントベクトルが準備できませんでした。初期推薦を試みます。")
        return get_initial_recommendations_for_user(user_id) # フォールバック

    # 5. 推薦の実行
    recommendations_with_score = []
    for event_id, event_vec in event_vectors_map.items():
        try:
            similarity = cosine_similarity(final_user_profile_vector.reshape(1, -1), event_vec.reshape(1, -1))[0][0]
            if np.isnan(similarity): similarity = 0.0
            recommendations_with_score.append({
                'id': event_id, # EventモデルのIDを使用
                'title': event_titles_map.get(event_id, "不明なイベント"),
                'similarity': float(similarity), # JSONシリアライズ可能なfloatに変換
                'reason': 'コンテンツベース (投稿内容類似)'
            })
        except Exception as e:
            print(f"[Error] イベント {event_id} との類似度計算中にエラー: {e}")

    recommendations_with_score.sort(key=lambda x: x['similarity'], reverse=True)
    
    # ユーザーが既に参加またはいいねしたイベントは除外 (初期推薦と同様のロジック)
    final_recommendations = []
    if recommendations_with_score:
        user = get_user_by_id(user_id)
        interacted_event_ids_for_filter = set()
        if user:
            if hasattr(user, 'memberships'): interacted_event_ids_for_filter.update([m.event_id for m in user.memberships])
            if hasattr(user, 'hearted_events'): interacted_event_ids_for_filter.update([e.id for e in user.hearted_events])
        
        for rec in recommendations_with_score:
            if rec['id'] not in interacted_event_ids_for_filter:
                final_recommendations.append(rec)
            if len(final_recommendations) >= num_recommendations:
                break
        
    if not final_recommendations:
        print(f"ユーザー ({user_id}) へのコンテンツベース推薦結果が0件でした。初期推薦を試みます。")
        return get_initial_recommendations_for_user(user_id) # フォールバック

    print(f"--- ユーザー ({user_id}) へのおすすめイベント (上位{len(final_recommendations)}件) ---")
    for rec in final_recommendations:
        print(f"  Event ID: {rec['id']}, Title: {rec['title']}, Similarity: {rec['similarity']:.4f}, Reason: {rec['reason']}")
        
    return final_recommendations


# === Flaskアプリケーションのコンテキスト内でテストするためのラッパー ===
# (この部分はFlaskアプリのエントリーポイントやテスト用スクリプトに記述するのがより適切)
def run_recommendation_test_in_context(app, test_user_id):
    with app.app_context():
        print(f"\n=== Flaskコンテキスト内でユーザー ({test_user_id}) の推薦処理テスト ===")

        # メインのコンテンツベース推薦のテスト
        content_based_recs = get_event_recommendations_for_user(test_user_id)
        if not content_based_recs:
            print(f"ユーザー ({test_user_id}) へのコンテンツベース推薦はありませんでした。")

