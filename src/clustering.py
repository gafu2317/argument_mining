from typing import List
import numpy as np
from sklearn.decomposition import PCA

def reduce_dimensions_pca(vectors: List[List[float]]) -> List[List[float]]:
    """
    ベクトルデータのリストを受け取り、PCAで2次元に削減した座標のリストを返す。
    """
    # ベクトルが2つ未満の場合、PCAは適用できない
    if len(vectors) < 2:
        return [[0, 0] for _ in vectors]

    pca = PCA(n_components=2, random_state=42)
    reduced_vectors = pca.fit_transform(np.array(vectors))
    
    return reduced_vectors.tolist()