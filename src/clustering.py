from typing import List
import numpy as np
from sklearn.cluster import KMeans

def perform_clustering(
    vectors: List[List[float]], 
    num_clusters: int
) -> List[int]:
    """
    ベクトルデータのリストを受け取り、K-meansクラスタリングを実行して、
    各ベクトルのクラスターIDのリストを返す。

    Args:
        vectors: 埋め込みベクトルのリスト
        num_clusters: 作成するクラスターの数

    Returns:
        各ベクトルに対応するクラスターIDのリスト
    """
    # ベクトルの数がクラスター数より少ない場合、クラスタリングは不可能
    if len(vectors) < num_clusters:
        # 全ての要素を同じクラスターID (0) として返す
        return [0] * len(vectors)

    # K-meansモデルの初期化と学習
    kmeans = KMeans(
        n_clusters=num_clusters,
        random_state=42,  # 結果を固定するための乱数シード
        n_init=10 # 異なる初期値で10回実行し、最良の結果を採用
    )
    kmeans.fit(np.array(vectors))

    # 各ベクトルのクラスターラベルを返す
    return kmeans.labels_.tolist()
