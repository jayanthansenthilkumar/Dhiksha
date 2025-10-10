"""
Build Milvus vector index from trained retrieval model.
"""

import argparse
import sys
from pathlib import Path

import mlflow
import numpy as np
from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.schemas import Content
from src.utils.config import settings, get_milvus_config


def connect_to_milvus():
    """Connect to Milvus server."""
    config = get_milvus_config()
    connections.connect(
        alias="default",
        host=config["host"],
        port=config["port"]
    )
    print(f"✅ Connected to Milvus at {config['host']}:{config['port']}")


def create_collection(collection_name: str, dim: int = 128):
    """
    Create Milvus collection for content embeddings.
    
    Args:
        collection_name: Name of collection
        dim: Embedding dimension
    """
    # Check if collection exists
    if utility.has_collection(collection_name):
        print(f"  Collection '{collection_name}' already exists, dropping...")
        utility.drop_collection(collection_name)
    
    # Define schema
    fields = [
        FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="created_at", dtype=DataType.INT64),  # Unix timestamp
    ]
    
    schema = CollectionSchema(fields, description="Content embeddings for recommendations")
    
    # Create collection
    collection = Collection(name=collection_name, schema=schema)
    print(f"✅ Created collection '{collection_name}'")
    
    return collection


def load_content_items():
    """Load all content items from database."""
    print("Loading content items from database...")
    
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    contents = session.query(Content).all()
    
    content_ids = [str(c.content_id) for c in contents]
    created_ats = [int(c.created_at.timestamp()) for c in contents]
    
    session.close()
    engine.dispose()
    
    print(f"  Loaded {len(contents)} content items")
    
    return content_ids, created_ats


def generate_embeddings(content_ids):
    """
    Generate embeddings for content items using retrieval model.
    
    Args:
        content_ids: List of content IDs
    
    Returns:
        numpy array of embeddings
    """
    print("Generating embeddings...")
    
    # TODO: Load retrieval model from MLflow
    # model = mlflow.tensorflow.load_model("models:/retrieval_model/Production")
    # embeddings = model.item_model.predict(content_ids)
    
    # Placeholder: random embeddings
    print("  ⚠️  Using random embeddings (placeholder)")
    embeddings = np.random.randn(len(content_ids), settings.EMBEDDING_DIM).astype(np.float32)
    
    # Normalize
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    print(f"  Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    
    return embeddings


def insert_embeddings(collection, content_ids, embeddings, created_ats):
    """
    Insert embeddings into Milvus collection.
    
    Args:
        collection: Milvus collection
        content_ids: List of content IDs
        embeddings: numpy array of embeddings
        created_ats: List of creation timestamps
    """
    print("Inserting embeddings into Milvus...")
    
    # Insert in batches
    batch_size = 1000
    n_batches = (len(content_ids) + batch_size - 1) // batch_size
    
    for i in range(n_batches):
        start = i * batch_size
        end = min((i + 1) * batch_size, len(content_ids))
        
        batch_ids = content_ids[start:end]
        batch_embeddings = embeddings[start:end].tolist()
        batch_timestamps = created_ats[start:end]
        
        data = [batch_ids, batch_embeddings, batch_timestamps]
        collection.insert(data)
        
        print(f"  Inserted batch {i + 1}/{n_batches}")
    
    collection.flush()
    print(f"✅ Inserted {len(content_ids)} embeddings")


def build_index(collection):
    """
    Build IVF_FLAT index on embeddings.
    
    Args:
        collection: Milvus collection
    """
    print("Building index...")
    
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    
    collection.create_index(field_name="embedding", index_params=index_params)
    print("✅ Index built")


def load_collection(collection):
    """Load collection into memory for queries."""
    print("Loading collection into memory...")
    collection.load()
    print("✅ Collection loaded")


def test_query(collection, n=5):
    """
    Test query to verify index works.
    
    Args:
        collection: Milvus collection
        n: Number of results to return
    """
    print(f"\nTesting query (top {n} similar items)...")
    
    # Generate random query vector
    query_vector = np.random.randn(1, settings.EMBEDDING_DIM).astype(np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)
    
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    
    results = collection.search(
        data=query_vector.tolist(),
        anns_field="embedding",
        param=search_params,
        limit=n,
        output_fields=["content_id", "created_at"]
    )
    
    print("  Results:")
    for i, hit in enumerate(results[0]):
        print(f"    {i + 1}. Content ID: {hit.entity.get('content_id')}, Distance: {hit.distance:.4f}")
    
    print("✅ Query test passed")


def main():
    parser = argparse.ArgumentParser(description="Build Milvus index from retrieval model")
    parser.add_argument("--collection", type=str, default="content_embeddings", help="Collection name")
    parser.add_argument("--dim", type=int, default=128, help="Embedding dimension")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Milvus Index Builder")
    print("=" * 60)
    print(f"Collection: {args.collection}")
    print(f"Embedding dimension: {args.dim}")
    print()
    
    try:
        # Connect to Milvus
        connect_to_milvus()
        print()
        
        # Create collection
        collection = create_collection(args.collection, dim=args.dim)
        print()
        
        # Load content items
        content_ids, created_ats = load_content_items()
        print()
        
        # Generate embeddings
        embeddings = generate_embeddings(content_ids)
        print()
        
        # Insert embeddings
        insert_embeddings(collection, content_ids, embeddings, created_ats)
        print()
        
        # Build index
        build_index(collection)
        print()
        
        # Load collection
        load_collection(collection)
        print()
        
        # Test query
        test_query(collection)
        
        print()
        print("=" * 60)
        print("✅ Index build complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Verify index: python -m pymilvus.client.grpc_handler")
        print("  2. Update API to use real embeddings")
        print("  3. Schedule daily index rebuild (CronJob)")
    
    except Exception as e:
        print(f"\n❌ Error building index: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
